"""Palmae ETL — build the family-complete scaffold in the database.

Run (API env active, DATABASE_URL set):
    PYTHONPATH=api .venv/bin/python -m etl.run

Order (each idempotent via a full clear):
  1. sources     — the provenance/citation registry (etl.sources)
  2. taxonomy    — WCVP accepted names + synonymy -> taxon + name_alias,
                   placed into subfamily/tribe/genus (PalmTraits classification)
  3. traits      — PalmTraits 1.0 -> trait
Ranges (GBIF/WCVP distributions) and the Faurby tree load in later steps.
"""
from __future__ import annotations

import re
import unicodedata

from sqlalchemy import delete, func, insert, select

from app import models as m
from app.db import SessionLocal
from etl import palmtraits, sources, wcvp


def _bulk(session, model, rows: list[dict], chunk: int = 500) -> None:
    """Fast batched insert (executemany) — a few round-trips, not thousands."""
    for i in range(0, len(rows), chunk):
        session.execute(insert(model), rows[i:i + chunk])

_CLEAR_ORDER = [
    m.Occurrence, m.RangeRegion, m.Trait, m.Use, m.ConservationAssessment,
    m.ClimateProfile, m.GeneticResource, m.Photo, m.PhylogenyNode, m.NameAlias,
    m.Taxon, m.Tree, m.DataSource,
]


def clear(session) -> None:
    for model in _CLEAR_ORDER:
        session.execute(delete(model))
    session.flush()


def load_sources(session) -> None:
    # merge (upsert on the `id` PK), not add — so this can be re-run standalone
    # against a live DB to pick up newly-added citations without colliding. This is
    # the citation-drift guard: a maintainer who adds a source and re-runs only this
    # step gets the new rows instead of an IntegrityError (which historically led to
    # the step being skipped and the Sources page silently under-citing).
    for s in sources.DATA_SOURCES:
        session.merge(m.DataSource(**s))
    session.flush()
    print(f"  sources: {len(sources.DATA_SOURCES)} registered (upsert)")


def _slugify(genus: str | None, scientific_name: str, used: set[str]) -> str:
    """A short unique ASCII handle, genus-epithet (e.g. 'pritchardia-martii').
    Genus-qualified because epithets collide across the family's 181 genera."""
    parts = scientific_name.split()
    epithet = parts[-1] if parts else "sp"
    base = f"{genus or (parts[0] if parts else 'palm')} {epithet}"
    ascii_ = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-") or "palm-sp"
    out, i = slug, 2
    while out in used:
        out = f"{slug}-{i}"
        i += 1
    used.add(out)
    return out


def load_taxonomy(session) -> dict[str, int]:
    """WCVP accepted palm species + synonymy -> taxon + name_alias, placed into
    subfamily/tribe/genus via the PalmTraits classification. Returns gbif_key->id."""
    accepted = wcvp.fetch_accepted()
    synonyms = wcvp.fetch_synonyms()
    classes = palmtraits.classification()  # genus -> {tribe, subfamily}

    used_slugs: set[str] = set()
    key_to_id: dict[int, int] = {}
    seen_alias: set[tuple[int, str]] = set()
    taxa_rows: list[dict] = []
    alias_rows: list[dict] = []

    def add_alias(sid: int, raw: str | None, auth: str | None, status: str) -> None:
        if not raw:
            return
        key = (sid, raw.lower())
        if key in seen_alias:
            return
        seen_alias.add(key)
        alias_rows.append({"species_id": sid, "raw_name": raw, "authorship": auth,
                           "name_status": status, "source": "wcvp"})

    # Explicit species_id (the table was just cleared) so we can map without a
    # per-row flush round-trip.
    for sid, a in enumerate(accepted, start=1):
        genus = a["genus"]
        placement = classes.get(genus, {})
        taxa_rows.append({
            "species_id": sid,
            "slug": _slugify(genus, a["scientific_name"], used_slugs),
            "scientific_name": a["scientific_name"],
            "authorship": a["authorship"],
            "genus": genus,
            "tribe": placement.get("tribe"),
            "subfamily": placement.get("subfamily"),
            "rank": "species",
            "is_hybrid": a["is_hybrid"],
            "accepted": True,
            "wcvp_id": a["wcvp_id"],
            "gbif_taxon_key": a["gbif_key"],
        })
        key_to_id[a["gbif_key"]] = sid
        add_alias(sid, a["scientific_name"], a["authorship"], "accepted")

    linked = skipped = 0
    for s in synonyms:
        sid = key_to_id.get(s["accepted_gbif_key"])
        if sid is None:  # accepted usage is infraspecific / out of scope
            skipped += 1
            continue
        add_alias(sid, s["raw_name"], s["authorship"], "synonym")
        linked += 1

    _bulk(session, m.Taxon, taxa_rows)
    _bulk(session, m.NameAlias, alias_rows)
    session.flush()

    placed = session.scalar(select(func.count()).select_from(m.Taxon)
                            .where(m.Taxon.subfamily.isnot(None)))
    print(f"  taxonomy: {len(accepted)} accepted species "
          f"({sum(1 for a in accepted if a['is_hybrid'])} nothospecies), "
          f"{linked} synonyms linked, {skipped} skipped; "
          f"{placed} placed to subfamily")
    return key_to_id


def load_traits(session) -> None:
    """PalmTraits 1.0 -> trait rows, matched to accepted species by name then alias."""
    by_name = {sn.lower(): sid for sid, sn in session.execute(
        select(m.Taxon.species_id, m.Taxon.scientific_name).where(m.Taxon.accepted == True))}  # noqa: E712
    alias = {rn.lower(): sid for sid, rn in session.execute(
        select(m.NameAlias.species_id, m.NameAlias.raw_name))}

    records = palmtraits.species_traits()
    matched = unmatched = 0
    trait_rows: list[dict] = []
    for rec in records:
        sid = by_name.get(rec["name"].lower()) or alias.get(rec["name"].lower())
        if sid is None:
            unmatched += 1
            continue
        matched += 1
        for t in rec["traits"]:
            trait_rows.append({
                "species_id": sid, "trait_name": t["trait_name"],
                "value_num": t["value_num"], "value_cat": t["value_cat"],
                "unit": t["unit"], "source": "PalmTraits 1.0", "license": "CC0"})
    _bulk(session, m.Trait, trait_rows)
    session.flush()
    written = len(trait_rows)
    species_with_traits = session.scalar(
        select(func.count(func.distinct(m.Trait.species_id))))
    print(f"  traits: matched {matched}/{len(records)} PalmTraits species "
          f"({unmatched} unmatched); {written} trait rows; "
          f"{species_with_traits} species carry traits")


def load_ranges(session) -> None:
    """TDWG (WGSRPD level-3) native/introduced ranges per species from the WCVP
    checklist distributions (via GBIF). Stores region codes + origin, not per-species
    geometry — the map joins these to the shared TDWG layer. Fetched in parallel."""
    from concurrent.futures import ThreadPoolExecutor

    keyed = [(sid, key) for sid, key in session.execute(
        select(m.Taxon.species_id, m.Taxon.gbif_taxon_key)
        .where(m.Taxon.gbif_taxon_key.isnot(None)))]

    def fetch(pair):
        sid, key = pair
        try:
            return sid, wcvp.fetch_distributions(key)
        except Exception:  # noqa: BLE001
            return sid, None

    rows: list[dict] = []
    n_species = failed = 0
    with ThreadPoolExecutor(max_workers=10) as ex:
        for sid, dist in ex.map(fetch, keyed):
            if dist is None:
                failed += 1
                continue
            seen: set[str] = set()
            for d in dist:
                code = d["tdwg_code"]
                if not code or code in seen:
                    continue
                # Don't assert a doubtful/extinct WCVP occurrence as part of the range —
                # previously these silently defaulted to "native", over-stating ranges.
                status = d.get("status") or ""
                if "doubtful" in status or "extinct" in status:
                    continue
                seen.add(code)
                origin = "introduced" if d.get("establishment") == "introduced" else "native"
                rows.append({"species_id": sid, "tdwg_code": code,
                             "origin": origin, "source": "WCVP/POWO"})
            if seen:
                n_species += 1
    _bulk(session, m.RangeRegion, rows)
    session.flush()
    print(f"  ranges: {len(rows)} region records across {n_species} species "
          f"({failed} fetch failures)")


def load_conservation(session) -> None:
    """Bellot et al. 2022 predicted risk -> conservation_assessment. Each species gets
    a threatened / not-threatened status with risk_basis (assessed vs predicted)."""
    from etl import bellot
    by_name = {sn.lower(): sid for sid, sn in session.execute(
        select(m.Taxon.species_id, m.Taxon.scientific_name).where(m.Taxon.accepted == True))}  # noqa: E712
    alias = {rn.lower(): sid for sid, rn in session.execute(
        select(m.NameAlias.species_id, m.NameAlias.raw_name))}

    recs = bellot.records()
    rows: list[dict] = []
    seen: set[int] = set()
    unmatched = 0
    for r in recs:
        sid = by_name.get(r["name"].lower()) or alias.get(r["name"].lower())
        if sid is None:
            unmatched += 1
            continue
        if sid in seen:
            continue
        seen.add(sid)
        rows.append({
            "species_id": sid, "risk_basis": r["risk_basis"],
            "predicted_category": r["predicted_category"],
            "prediction_probability": r["prediction_probability"],
            "scope": "global", "source": "Bellot et al. 2022"})
    _bulk(session, m.ConservationAssessment, rows)
    session.flush()

    threat = sum(1 for r in rows if r["predicted_category"] == "threatened")
    assessed = sum(1 for r in rows if r["risk_basis"] == "assessed")
    pct = round(100 * threat / len(rows)) if rows else 0
    print(f"  conservation: {len(rows)} species ({assessed} assessed, "
          f"{len(rows) - assessed} predicted; {unmatched} unmatched); "
          f"{threat} threatened ({pct}% of covered)")


def load_tree(session) -> None:
    """Faurby 2016 complete supertree -> tree + phylogeny_node. Tips reconciled to
    accepted taxa through the NameAlias spine; inserted in preorder so each node's
    parent exists first."""
    from etl import phylo
    nodes = phylo.parse()
    _bulk(session, m.Tree, [{
        "tree_id": 1, "method": "faurby-supertree",
        "citation_doi": "10.1016/j.ympev.2016.03.002",
        "source_url": "https://doi.org/10.5061/dryad.ts45225"}])

    by_name = {sn.lower(): sid for sid, sn in session.execute(
        select(m.Taxon.species_id, m.Taxon.scientific_name).where(m.Taxon.accepted == True))}  # noqa: E712
    alias = {rn.lower(): sid for sid, rn in session.execute(
        select(m.NameAlias.species_id, m.NameAlias.raw_name))}

    rows: list[dict] = []
    matched = unmatched = 0
    for n in nodes:
        sid = None
        name = None
        kind = "clade"
        if n["is_tip"]:
            kind = "tip"
            name = (n["tip_label"] or "").replace("_", " ").strip()
            sid = by_name.get(name.lower()) or alias.get(name.lower())
            if sid:
                matched += 1
            else:
                unmatched += 1
        rows.append({
            "node_id": n["node_id"], "tree_id": 1,
            "parent_node_id": n["parent_node_id"], "is_tip": n["is_tip"],
            "kind": kind, "name": name, "tip_label": n["tip_label"],
            "branch_length": n["branch_length"], "species_id": sid})
    _bulk(session, m.PhylogenyNode, rows)
    session.flush()
    tips = sum(1 for n in nodes if n["is_tip"])
    print(f"  tree: {len(nodes)} nodes ({tips} tips); "
          f"{matched} tips reconciled to accepted taxa ({unmatched} unmatched)")


def main() -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not set — see api/.env")
    with SessionLocal() as session:
        print("Palmae ETL")
        clear(session)
        load_sources(session)
        load_taxonomy(session)
        load_traits(session)
        load_ranges(session)
        load_conservation(session)
        load_tree(session)
        session.commit()
        print("done.")


if __name__ == "__main__":
    main()
