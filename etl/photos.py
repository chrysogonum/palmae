"""Ingest a representative CC-licensed iNaturalist photo per species (+ backfill the
common name from the same lookup). Standalone, on top of the loaded spine.

iNaturalist asks for <= ~60-100 requests/minute, so this is globally rate-limited to
~80/min and takes a while (~30-35 min for the whole family). Only Creative-Commons
photos are stored; all-rights-reserved default photos are skipped. Each photo keeps
its observer attribution + licence, shown in the UI.

    PYTHONPATH=api .venv/bin/python -m etl.photos            # whole family
    PYTHONPATH=api .venv/bin/python -m etl.photos --limit 50 # a quick subset
"""
from __future__ import annotations

import argparse
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import delete, insert, select, text, update

from app import models as m
from app.db import SessionLocal
from etl import inat

_MIN_INTERVAL = 60.0 / 80  # ~80 requests/minute, family-wide
_lock = threading.Lock()
_last = [0.0]


def _throttle() -> None:
    with _lock:
        wait = _last[0] + _MIN_INTERVAL - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.monotonic()


def _fetch(pair: tuple[int, str]) -> tuple[int, dict | None]:
    sid, name = pair
    for attempt in range(2):
        _throttle()
        try:
            return sid, inat.fetch_media(name)
        except Exception:  # noqa: BLE001 (rate-limit / transient) — one retry
            if attempt == 0:
                time.sleep(2.0)
    return sid, None


def run(limit: int | None = None) -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not set — see api/.env")
    with SessionLocal() as s:
        rows = s.execute(
            select(m.Taxon.species_id, m.Taxon.scientific_name, m.Taxon.common_name)
            .where(m.Taxon.accepted == True)  # noqa: E712
            .order_by(m.Taxon.species_id)).all()
    if limit:
        rows = rows[:limit]
    keyed = [(sid, name) for sid, name, _ in rows]
    common_null = {sid for sid, _, cn in rows if not cn}
    print(f"photos: iNat lookup for {len(keyed)} species (~{len(keyed) * _MIN_INTERVAL / 60:.0f} min)")

    photos: list[dict] = []
    common_updates: list[tuple[int, str]] = []
    matched = done = 0
    with ThreadPoolExecutor(max_workers=3) as ex:
        for sid, res in ex.map(_fetch, keyed):
            done += 1
            if res:
                matched += 1
                if res.get("url"):
                    photos.append({
                        "species_id": sid, "url": res["url"], "kind": "photo",
                        "attribution": res.get("attribution"), "license": res.get("license"),
                        "source_url": res.get("source_url"),
                        "source": "iNaturalist", "is_default": True})
                cn = res.get("common_name")
                if cn and sid in common_null:
                    common_updates.append((sid, cn))
            if done % 300 == 0:
                obs = sum(1 for p in photos if "/observations/" in (p.get("source_url") or ""))
                print(f"  {done}/{len(keyed)} — {len(photos)} CC photos ({obs} → observations), "
                      f"{len(common_updates)} common names")

    with SessionLocal() as s:
        s.execute(text("ALTER TABLE photo ADD COLUMN IF NOT EXISTS source_url varchar"))
        s.execute(delete(m.Photo).where(m.Photo.source == "iNaturalist"))
        s.flush()
        for i in range(0, len(photos), 500):
            s.execute(insert(m.Photo), photos[i:i + 500])
        for sid, cn in common_updates:
            s.execute(update(m.Taxon).where(m.Taxon.species_id == sid).values(common_name=cn))
        s.commit()
    print(f"done: {matched}/{len(keyed)} matched on iNat; {len(photos)} CC photos stored; "
          f"{len(common_updates)} common names backfilled.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    run(**vars(ap.parse_args()))
