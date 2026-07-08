"""The palm-line ingest — occurrences x climate, on top of the loaded spine.

This is the money-shot's data phase. It runs *standalone* against an already-built
database (it needs the taxonomy + TDWG ranges from `etl.run`); it does not re-run the
whole pipeline.

    PYTHONPATH=api .venv/bin/python -m etl.occurrences            # full family
    PYTHONPATH=api .venv/bin/python -m etl.occurrences --limit 200 # a quick subset

Steps:
  1. Fetch wild GBIF occurrences per species (worldwide, cultivated/managed dropped
     at the source via basisOfRecord + establishmentMeans — gardens must not define
     the frost line).
  2. Tag each point native / introduced by point-in-polygon against the TDWG
     level-3 layer, cross-checked to the species' WCVP native range we already hold.
     The range authority decides native vs introduced, not the raw point.
  3. Sample the coldest-month mean temperature (CMMT) at every point from WorldClim.
  4. Aggregate a per-species `climate_profile` (CMMT mean, the cold edge = CMMT min
     over native points, n) — all flagged derived.

Everything here is DERIVED and labelled as such in the UI; the authoritative layers
(names, ranges, tree, risk) are untouched.
"""
from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import delete, func, insert, select, text

from app import models as m
from app.db import SessionLocal
from etl import gbif, worldclim

# How many wild points to keep per species. Enough to trace the family's cold edge
# without letting a handful of over-recorded ornamentals dominate the cloud.
PER_SPECIES_CAP = 60
_TDWG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tdwg_level3.geojson")


# --------------------------------------------------------------------------- #
# TDWG point-in-polygon — which botanical country a point falls in
# --------------------------------------------------------------------------- #
class TdwgIndex:
    """Spatial index over the WGSRPD level-3 polygons: (lon, lat) -> region code."""

    def __init__(self) -> None:
        from shapely.geometry import shape
        from shapely.strtree import STRtree

        feats = json.load(open(_TDWG))["features"]
        self._geoms = []
        self._codes: list[str] = []
        for f in feats:
            code = f["properties"].get("LEVEL3_COD")
            if not code:
                continue
            self._geoms.append(shape(f["geometry"]))
            self._codes.append(code)
        self._tree = STRtree(self._geoms)

    def code_for(self, lon: float, lat: float) -> str | None:
        from shapely.geometry import Point

        p = Point(lon, lat)
        for i in self._tree.query(p):
            if self._geoms[i].contains(p):
                return self._codes[i]
        return None


# --------------------------------------------------------------------------- #
# fetch
# --------------------------------------------------------------------------- #
def _fetch_species(pair: tuple[int, str]) -> tuple[int, list[dict]]:
    """Resolve the name to a GBIF *backbone* taxonKey (the stored key is the WCVP
    checklist key, which the occurrence index doesn't use), then fetch wild points."""
    sid, name = pair
    try:
        key = gbif.match_taxon_key(name)
        if not key:
            return sid, []
        return sid, gbif.fetch_global(key, max_records=PER_SPECIES_CAP)
    except Exception:  # noqa: BLE001
        return sid, []


def run(limit: int | None = None) -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not set — see api/.env")

    with SessionLocal() as session:
        keyed = session.execute(
            select(m.Taxon.species_id, m.Taxon.scientific_name)
            .where(m.Taxon.accepted == True)  # noqa: E712
            .order_by(m.Taxon.species_id)).all()
        if limit:
            keyed = keyed[:limit]
        # native TDWG codes per species (the range authority for native/introduced)
        native_codes: dict[int, set[str]] = {}
        for sid, code in session.execute(text(
                "select species_id, tdwg_code from range_region where origin='native'")):
            native_codes.setdefault(sid, set()).add(code)

    print(f"palm-line ingest: {len(keyed)} species, cap {PER_SPECIES_CAP}/sp")

    # 1. fetch (parallel; GBIF search API, cultivated dropped in gbif.fetch_global)
    fetched: dict[int, list[dict]] = {}
    done = 0
    # 8 workers (not 12) so GBIF rate-limits less often; the fetch also retries.
    with ThreadPoolExecutor(max_workers=8) as ex:
        for sid, pts in ex.map(_fetch_species, [(s, n) for s, n in keyed]):
            if pts:
                fetched[sid] = pts
            done += 1
            if done % 300 == 0:
                print(f"  fetched {done}/{len(keyed)} species, "
                      f"{sum(len(v) for v in fetched.values())} points so far")
    total_pts = sum(len(v) for v in fetched.values())
    print(f"  fetched {total_pts} wild points across {len(fetched)} species")

    # 2. native/introduced by point-in-polygon vs the WCVP native range
    print("  tagging native/introduced (TDWG point-in-polygon)...")
    tdwg = TdwgIndex()
    rows: list[dict] = []
    coords: list[tuple[float, float]] = []
    for sid, pts in fetched.items():
        nat = native_codes.get(sid, set())
        for p in pts:
            code = tdwg.code_for(p["lon"], p["lat"])
            in_native = bool(code and code in nat)
            rows.append({
                "species_id": sid, "source": "GBIF",
                "source_record_id": p["source_record_id"],
                "lon": p["lon"], "lat": p["lat"],
                "basis_of_record": p["basis_of_record"],
                "event_date": p["event_date"], "license": p["license"],
                "coordinate_uncertainty_m": p["coordinate_uncertainty_m"],
                "dataset_key": p["dataset_key"],
                "in_native_range": in_native,
                "establishment_means": "native" if in_native else "introduced",
                "tdwg_code": code,
            })
            coords.append((p["lon"], p["lat"]))

    # 3. CMMT per point
    print(f"  sampling CMMT at {len(coords)} points (WorldClim)...")
    cmmts = worldclim.cmmt_at(coords)
    for r, c in zip(rows, cmmts):
        r["cmmt"] = c

    # 4. write occurrences + aggregate climate_profile
    _write(rows)
    print("done.")


def _write(rows: list[dict]) -> None:
    with SessionLocal() as session:
        session.execute(delete(m.Occurrence))
        session.execute(delete(m.ClimateProfile))
        session.flush()

        occ_rows = [{
            "species_id": r["species_id"], "source": r["source"],
            "source_record_id": r["source_record_id"],
            "geom": f"SRID=4326;POINT({r['lon']} {r['lat']})",
            "basis_of_record": r["basis_of_record"], "event_date": r["event_date"],
            "license": r["license"],
            "coordinate_uncertainty_m": r["coordinate_uncertainty_m"],
            "dataset_key": r["dataset_key"], "in_native_range": r["in_native_range"],
            "establishment_means": r["establishment_means"], "cmmt": r["cmmt"],
        } for r in rows]
        for i in range(0, len(occ_rows), 1000):
            session.execute(insert(m.Occurrence), occ_rows[i:i + 1000])

        # per-species envelope over NATIVE points with a valid CMMT
        prof: dict[int, list[float]] = {}
        for r in rows:
            if r["in_native_range"] and r["cmmt"] is not None:
                prof.setdefault(r["species_id"], []).append(r["cmmt"])
        prof_rows = [{
            "species_id": sid,
            "cmmt_mean": round(sum(v) / len(v), 2),
            "cmmt_min": round(min(v), 2),  # the hardiness edge
            "n_occurrences": len(v),
            "hardiness_c": round(min(v), 2),  # coldest monthly-mean it occupies (derived)
            "derived": True, "source": "WorldClim 2.1 x GBIF (derived)",
        } for sid, v in prof.items() if v]
        for i in range(0, len(prof_rows), 500):
            session.execute(insert(m.ClimateProfile), prof_rows[i:i + 500])
        session.commit()

        n_occ = session.scalar(select(func.count()).select_from(m.Occurrence))
        n_nat = session.scalar(select(func.count()).select_from(m.Occurrence)
                               .where(m.Occurrence.in_native_range == True))  # noqa: E712
        n_prof = session.scalar(select(func.count()).select_from(m.ClimateProfile))
        print(f"  wrote {n_occ} occurrences ({n_nat} native), "
              f"{n_prof} species climate profiles")


def backfill(names: list[str], cap: int = 300) -> None:
    """Deterministically (re)ingest specific species by name — used for the curated
    renegades, whose native points the bulk concurrent fetch can miss under GBIF
    rate-limits. Fetches each sequentially at a higher cap, then replaces just those
    species' occurrences + climate profiles. Leaves every other species untouched."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not set — see api/.env")

    with SessionLocal() as session:
        resolved: list[tuple[int, str]] = []
        for name in names:
            row = session.execute(text("""
                select t.species_id, t.scientific_name from taxon t
                left join name_alias a on a.species_id = t.species_id
                where t.accepted and (lower(t.scientific_name)=lower(:n)
                                      or lower(a.raw_name)=lower(:n)) limit 1
            """), {"n": name}).first()
            if row:
                resolved.append((row[0], row[1]))
            else:
                print(f"  ! no accepted taxon for '{name}'")
        native_codes: dict[int, set[str]] = {}
        for sid, code in session.execute(text(
                "select species_id, tdwg_code from range_region where origin='native'")):
            native_codes.setdefault(sid, set()).add(code)

    print(f"backfill: {len(resolved)} species, cap {cap}/sp (sequential)")
    tdwg = TdwgIndex()
    rows: list[dict] = []
    coords: list[tuple[float, float]] = []
    for sid, sci in resolved:
        key = gbif.match_taxon_key(sci)
        pts = gbif.fetch_global(key, max_records=cap) if key else []
        nat = native_codes.get(sid, set())
        n_native = 0
        for p in pts:
            code = tdwg.code_for(p["lon"], p["lat"])
            in_native = bool(code and code in nat)
            n_native += in_native
            rows.append({
                "species_id": sid, "source": "GBIF",
                "source_record_id": p["source_record_id"], "lon": p["lon"], "lat": p["lat"],
                "basis_of_record": p["basis_of_record"], "event_date": p["event_date"],
                "license": p["license"], "coordinate_uncertainty_m": p["coordinate_uncertainty_m"],
                "dataset_key": p["dataset_key"], "in_native_range": in_native,
                "establishment_means": "native" if in_native else "introduced",
            })
            coords.append((p["lon"], p["lat"]))
        print(f"  {sci:28s} {len(pts):4d} pts, {n_native:4d} native")

    cmmts = worldclim.cmmt_at(coords)
    for r, c in zip(rows, cmmts):
        r["cmmt"] = c

    sids = [sid for sid, _ in resolved]
    with SessionLocal() as session:
        session.execute(delete(m.Occurrence).where(m.Occurrence.species_id.in_(sids)))
        session.execute(delete(m.ClimateProfile).where(m.ClimateProfile.species_id.in_(sids)))
        session.flush()
        occ_rows = [{
            "species_id": r["species_id"], "source": r["source"],
            "source_record_id": r["source_record_id"],
            "geom": f"SRID=4326;POINT({r['lon']} {r['lat']})",
            "basis_of_record": r["basis_of_record"], "event_date": r["event_date"],
            "license": r["license"], "coordinate_uncertainty_m": r["coordinate_uncertainty_m"],
            "dataset_key": r["dataset_key"], "in_native_range": r["in_native_range"],
            "establishment_means": r["establishment_means"], "cmmt": r["cmmt"],
        } for r in rows]
        for i in range(0, len(occ_rows), 1000):
            session.execute(insert(m.Occurrence), occ_rows[i:i + 1000])
        prof: dict[int, list[float]] = {}
        for r in rows:
            if r["in_native_range"] and r["cmmt"] is not None:
                prof.setdefault(r["species_id"], []).append(r["cmmt"])
        prof_rows = [{
            "species_id": sid, "cmmt_mean": round(sum(v) / len(v), 2),
            "cmmt_min": round(min(v), 2), "n_occurrences": len(v),
            "hardiness_c": round(min(v), 2), "derived": True,
            "source": "WorldClim 2.1 x GBIF (derived)",
        } for sid, v in prof.items() if v]
        for i in range(0, len(prof_rows), 500):
            session.execute(insert(m.ClimateProfile), prof_rows[i:i + 500])
        session.commit()
        print(f"  backfilled {len(occ_rows)} occurrences, {len(prof_rows)} profiles")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="only the first N species")
    ap.add_argument("--renegades", action="store_true",
                    help="deterministically (re)ingest just the curated renegades")
    args = ap.parse_args()
    if args.renegades:
        from app.reference import RENEGADES
        backfill([r["name"] for r in RENEGADES])
    else:
        run(limit=args.limit)
