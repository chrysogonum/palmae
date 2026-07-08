# Palmae — a living atlas of the palms

An interactive, expert-facing atlas of the palm family (**Arecaceae** / Palmae). It spans the **whole
family** — every accepted species in Kew's World Checklist of Vascular Plants — and lets you explore it
by evolution (the phylogeny), by geography (a world range map), by climate (the palm line), and species
by species (a field guide). Built first for palm anatomist Scott Zona, so scientific precision and honest
attribution are the bar: every point, branch, and status traces to a published dataset, and every
approximation is labelled as one.

> **Status: live, family-complete, deployed.** Served as a fully static site (no runtime server or
> database) at **https://palmae.pages.dev**. Covers the **2,591 WCVP-accepted species**.

## What it does

- **Workbench** (the default home) — the palm tree of life and a world map, brushed against each other.
  Hover a clade → its native range lights up; click a map region → the tree lights up the branches that
  live there and a panel lists the region's palms; search a species (resolving synonyms) → it traces on
  the tree and lights its range; click a branch → drill into a labelled, scrollable subtree. A toggle
  switches the tree between the **all-species Faurby 2016 supertree** (2,539 tips) and the **modern,
  bootstrap-supported Yao 2023 genus backbone** (177 genera).
- **Palm Line** — the money-shot. Every cleaned native occurrence, coloured by the coldest-month mean
  temperature (CMMT) where it grows. The family hugs the warm side of the ~2–8 °C frost line (Reichgelt
  et al. 2018); a curated set of hardy **renegades** (windmill palm, needle palm, Mazari palm…) light up
  where they hold on past it, each with its data-derived cold edge.
- **World Atlas** — a species-richness choropleth (Borneo, Colombia, New Guinea, Madagascar light up);
  click a region for its native palms.
- **Field Guide** — a catalogue of all 2,591 species with placement, morphology, native range, an honest
  predicted-vs-assessed conservation status, and a derived coldest-month-climate block; filter by
  subfamily; every card links back onto the phylogeny.
- **About / Sources** — the pipeline and honest caveats in plain language, and a full bibliography with
  DOIs and licences for every dataset.

### Data coverage

| Layer | Source | Coverage |
|---|---|---|
| Taxonomy (accepted names + synonymy) | WCVP / POWO (Kew) | 2,591 species · 6,754 aliases |
| Functional traits | PalmTraits 1.0 | 39,811 rows · 2,256 species |
| Native/introduced ranges (TDWG level-3) | WCVP / POWO | 6,031 records · 2,573 species |
| Extinction risk (predicted + assessed) | Bellot et al. 2022 | 1,730 species (438 IUCN + 1,292 ML) |
| Phylogeny (all species) | Faurby et al. 2016 supertree | 2,539 tips · 2,235 species (86%) |
| Phylogeny (genus backbone, with support) | Yao et al. 2023 (plastid) | 177 genera |
| Occurrences × climate (the palm line) | GBIF × WorldClim 2.1 | 37,289 points (30,943 native) · 1,161 profiles |

Conservation risk is a **model prediction** wherever no formal IUCN assessment exists, and is always named
as the Bellot et al. 2022 prediction. The climate layer is **derived** (occurrence × WorldClim), never a
measured cold tolerance. Known gaps (14% of species off the tree, no node support on Faurby, no leaf
architecture in PalmTraits, binary-only IUCN category) are stated plainly on the About page.

## Architecture

```
palms-app/
  frontend/   Vite + React + TypeScript (D3 tree/map/palm-line)
  api/        FastAPI + SQLAlchemy 2 + GeoAlchemy2 — serves JSON contracts over PostGIS
  etl/        Python ingest (taxonomy, traits, ranges, conservation, tree, occurrences×climate, yao)
  data/       shared geometry (TDWG level-3) + downloaded datasets (gitignored where large)
```

- **Development / ingest:** PostgreSQL 17 + PostGIS on Supabase, behind FastAPI. The palm API runs on
  **:8001** (the sister oak app owns :8000). The frontend calls the API through a Vite proxy in dev.
- **Production is fully static.** `etl/export_static.py` bakes every endpoint's response to JSON under
  `frontend/public/api/` by calling the route handlers **in-process** (no running server needed) — the
  tree(s), all 2,591 species cards, per-species ranges, per-region species lists, the palm line, and a
  client-side search index. The built site runs on **Cloudflare Pages with no server and no database**.
- **Name reconciliation is the spine:** every incoming record resolves through a `name_alias` table to an
  accepted taxon before it is linked (palm genera are actively reshuffled).
- **Occurrences are tagged native/introduced** by point-in-TDWG-polygon against each species' WCVP range,
  and the frost line is drawn from native points only, so cultivated/planted records don't distort it.

## Local setup

Prerequisites: Node 22, Python 3.11, a Supabase project with the `postgis` extension enabled.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # API + ETL
npm install --prefix frontend                                         # frontend deps
# paste your Supabase session-pooler URL into api/.env as DATABASE_URL (never committed)

cd api && ../.venv/bin/alembic upgrade head && cd ..   # create tables
PYTHONPATH=api .venv/bin/python -m etl.run             # spine: names, traits, ranges, risk, tree (~2–4 min)
PYTHONPATH=api .venv/bin/python -m etl.occurrences     # the palm line: GBIF × WorldClim (~10–14 min)
PYTHONPATH=api .venv/bin/python -m etl.occurrences --renegades   # deterministic hardy-palm backfill
PYTHONPATH=api .venv/bin/python -m etl.yao             # Yao 2023 genus tree (needs data/yao2023/)
```

The palm-line ingest needs the WorldClim monthly `tavg` rasters in `data/worldclim/`, and the genus tree
needs the Yao tree file in `data/yao2023/` (both large and gitignored — see `PROJECT_STATE.md` for the
exact download URLs).

Run (two terminals):

```bash
PYTHONPATH=api .venv/bin/uvicorn app.main:app --app-dir api --port 8001   # API → http://localhost:8001
npm run dev --prefix frontend                                             # app → http://localhost:5173
```

## Deploy (static → Cloudflare Pages)

The bake calls the API in-process, so no server needs to be running:

```bash
PYTHONPATH=api .venv/bin/python -m etl.export_static   # writes frontend/public/api/*.json
npm run build --prefix frontend                        # Vite copies public/ → dist/
npx wrangler pages deploy frontend/dist --project-name palmae --branch main
```

That whole loop is all a redeploy needs — re-run it after any data re-ingest or code change. Preview a
built site locally with a plain static server (e.g. `python -m http.server` from `frontend/dist`), **not**
`vite preview` (which proxies `/api` to the dev server and so won't test the baked JSON).

## Data sources & attribution

Open biodiversity data; each source keeps its own licence and is attributed in full on the app's
**Sources** page. Principal sources: **WCVP / POWO** (taxonomy, CC-BY), **PalmTraits 1.0** (traits, CC0),
**Faurby et al. 2016** (all-species tree, CC0) and **Yao et al. 2023** (genus backbone, CC-BY), **GBIF**
(occurrences, CC0/CC-BY), **WorldClim 2.1** (climate, CC-BY) with the **Reichgelt et al. 2018** frost-line
calibration, **Bellot et al. 2022** (predicted extinction risk, CC-BY, from the authors' own release),
the **IUCN Red List** (assessed status, non-commercial, display-only), and **Genera Palmarum** (the
subfamily/tribe/genus classification).

## License

Source code: **MIT** (see [LICENSE](LICENSE)). The **data** carries its own licences — several
non-commercial — so any deployment that serves it is, in practice, for non-commercial and educational
use. Honour each source's terms.

## Project docs

`PROJECT_STATE.md` (current state, definitive) · `DECISIONS.md` (why things are the way they are) ·
`FACT_LOCK.md` (verified figures) · `RESEARCH.md` and `palms-spec.md` (evidence base + full spec).
