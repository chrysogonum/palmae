"""Bake the whole read-only palm API into static JSON under frontend/public/api, so
the site can be served from Cloudflare Pages with no live API or database.

Calls the FastAPI route handlers **in-process** (with a real DB session) rather than
over HTTP — the same functions the live API serves, so serialization is identical,
but there is no server to start, rate-limit, or have the environment reap mid-bake.
Idempotent: overwrites.

Query-parameter endpoints can't be a single file, so they are baked to path-based
files that `api/client.ts` mirrors in prod:
  /ranges?species={slug}   -> ranges/{slug}.json
  /palm-line?introduced=1  -> palm-line-introduced.json
  /search?q=...            -> search-index.json (filtered client-side)

Run:  PYTHONPATH=api .venv/bin/python -m etl.export_static
Then: npm run build --prefix frontend   (Vite copies public/api -> dist/api)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import text

from app import palette, routes
from app.db import SessionLocal

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public" / "api"
TDWG = ROOT / "data" / "tdwg_level3.geojson"


def write(relpath: str, obj) -> None:
    p = OUT / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, separators=(",", ":")))


def main() -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not set — see api/.env")
    OUT.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        # 1. no-argument endpoints (baked once)
        simple = {
            "sources": routes.sources, "tree": routes.tree, "taxa": routes.taxa,
            "tree/genera": routes.tree_genera,
            "taxa/coverage": routes.taxa_coverage, "ranges": routes.ranges,
            "species-regions": routes.species_regions, "renegades": routes.renegades,
            "lens/traits": routes.lens_traits, "lens/conservation": routes.lens_conservation,
        }
        for name, fn in simple.items():
            write(f"{name}.json", fn(db=db))
        write("palm-line.json", routes.palm_line(db=db))
        write("palm-line-introduced.json", routes.palm_line(introduced=1, db=db))
        print(f"  baked {len(simple) + 2} no-argument endpoints")

        # 2. per-species detail cards + per-species native/introduced ranges
        taxa = routes.taxa(db=db)
        for i, t in enumerate(taxa):
            slug = t["slug"]
            write(f"taxa/{slug}.json", routes.taxon_detail(slug, db=db))
            write(f"ranges/{slug}.json", routes.ranges(species=slug, db=db))
            if (i + 1) % 500 == 0:
                print(f"  taxa {i + 1}/{len(taxa)}")
        print(f"  baked {len(taxa)} taxa cards + {len(taxa)} per-species range files")

        # 3. per-region species lists (every TDWG level-3 botanical country)
        codes = [f["properties"]["LEVEL3_COD"]
                 for f in json.loads(TDWG.read_text())["features"]
                 if f["properties"].get("LEVEL3_COD")]
        for i, code in enumerate(codes):
            write(f"regions/{code}/species.json", routes.region_species(code, db=db))
            if (i + 1) % 150 == 0:
                print(f"  regions {i + 1}/{len(codes)}")
        print(f"  baked {len(codes)} per-region species lists")

        # 4. client-side search index (replicates /search over name_alias)
        rows = db.execute(text("""
            select t.slug, t.scientific_name, t.common_name, t.subfamily,
                   a.raw_name, a.name_status
            from name_alias a join taxon t on t.species_id = a.species_id
            where t.accepted
        """)).all()
        idx = [{"slug": slug, "latin": sci, "common": common, "raw": raw,
                "status": status, "color": palette.subfamily_color(subfamily)}
               for slug, sci, common, subfamily, raw, status in rows]
        write("search-index.json", idx)
        print(f"  baked search index ({len(idx)} names)")
    finally:
        db.close()

    print(f"\nDONE. static palm API written to {OUT}")


if __name__ == "__main__":
    sys.exit(main())
