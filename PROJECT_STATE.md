# PROJECT_STATE — Palmae

_Last updated: 2026-07-07. Read this first when resuming._

An interactive atlas of the palm family (Arecaceae), sister to Quercus, built on the Quercus code +
design as scaffold. See `palms-spec.md` for the full spec, `RESEARCH.md` for the evidence base, and
`HANDOFF.md` for background. The four locked decisions: **the palm-line money-shot**, a **co-equal grower
companion**, **family-complete from day one**, **conservation led by the Bellot 2022 predicted-risk
model**. Built first for **Scott Zona** — scientific precision is pass/fail.

## Status: DEPLOYED & LIVE — https://palmae.pages.dev

Fully static site on Cloudflare Pages (no runtime server/DB). Source is a **private** GitHub repo,
**github.com/chrysogonum/palmae** (branch `main`; `palms-app/` is the repo root). Deploys are **manual, no
CI**: bake (`python -m etl.export_static`, in-process) → `npm run build --prefix frontend` → `wrangler
pages deploy frontend/dist --project-name palmae --branch main`; commit + push after changes. Dev API on
**:8001** (oak owns :8000), Vite dev on :5173.

The frontend has four linked surfaces plus About/Sources:
- **Workbench** (default landing / home) — radial tree + world map, fully bidirectional brushing,
  search-to-locate, clade drill-in, region drill-down. A **tree toggle** switches between the all-species
  **Faurby 2016** supertree (2,539 tips) and the modern bootstrap-supported **Yao 2023** genus backbone
  (177 genera). Map hover shows region name; genus hover brushes the map + shows support.
- **World Atlas** — species-richness choropleth.
- **Palm Line** — the money-shot (native occurrences coloured by coldest-month mean temp; frost line +
  renegades). Nav position: between World Atlas and Field Guide.
- **Field Guide** — 2,591-species catalogue; cards carry honest predicted-vs-assessed risk, a derived
  coldest-month-climate block, and an "on the phylogeny →" cross-link that traces the species on the tree.
- Shared **subfamily + risk legend** on the region panel, clade view, and Field Guide.

Not yet built: the other lenses (form-function, people-palms), the dedicated grower companion, the
deep-time/future time ribbon, low-support flagging on the genus tree.

### The palm-line money-shot (built + verified this session)
- **Ingest** (`etl/worldclim.py` + `etl/occurrences.py`, standalone on top of the spine): cleaned wild
  GBIF occurrences per species → native/introduced by point-in-TDWG-polygon vs. the WCVP range → CMMT
  (coldest-month mean, min of WorldClim 2.1's 12 monthly `tavg`) per point → per-species `climate_profile`.
  **37,289** occurrences (30,943 native), **1,161** climate profiles. Curated renegades ingested by a
  deterministic backfill (`--renegades`). All derived; flagged as such. See FACT_LOCK for cold edges.
- **Frontend** `PalmLine.tsx` — world map of native occurrences coloured by CMMT (diverging palette pivoted
  on the frost line), legend marking the 2–8 °C band, renegades panel with each species' data-derived cold
  edge, introduced-points toggle, click-through to the species card. The card gained a derived
  coldest-month-climate block.
- **API** `/palm-line` (down-sampled points + frost line + renegade slugs), `/renegades`, `climate` folded
  into `/taxa/{slug}`.

### About / Sources + deploy prep (built this session)
- `Pages.tsx` rewritten for palms: **About** (pipeline, palm-line thesis, honest caveats/gaps) + **Sources**
  (full bibliography from the 20-source `data_source` registry). Wired into `App.tsx` (meta-nav).
- **Deploy prep:** `etl/export_static.py` rewritten for palm endpoints (no-arg set, per-slug cards +
  ranges, per-region species lists, both palm-line variants, search index); `api/client.ts` prod paths
  fixed for the query-param endpoints; dead oak components + oak `store.ts`/`sections.ts` moved to
  `.deadcode-frontend/` so `tsc -b && vite build` passes clean.

- **Database** — Supabase Postgres 17 + PostGIS 3.3 (session pooler, port 5432). `api/.env` holds the
  connection string (gitignored). Production will be static JSON baked by `etl/export_static.py` +
  Cloudflare Pages (no live prod DB), following Quercus.
- **Schema** — palm data model migrated (Alembic `0b06d8e2345c`). 13 tables: taxon, name_alias,
  occurrence, range_region, tree, phylogeny_node, trait, use, conservation_assessment, climate_profile,
  genetic_resource, data_source, photo. Placement is subfamily→tribe→genus; oak-only tables removed;
  palm-native `use` / `climate_profile` added; conservation carries predicted + assessed risk.
- **Base ingest done** (`PYTHONPATH=api .venv/bin/python -m etl.run`):
  - **2,591 accepted species** (42 nothospecies) from WCVP via the GBIF-hosted checklist (Arecaceae node
    326661320), placed into subfamily/tribe/genus. Subfamily counts verified (Arecoideae 1,356 …
    Nypoideae 1). 84 species unplaced to subfamily (genera newer than PalmTraits 2015).
  - **6,754 name aliases** — accepted + 4,179 linked synonyms; reconciliation verified.
  - **39,811 traits** across 2,256 species from **PalmTraits 1.0** (growth form, stem, armature, leaf/
    fruit size, fruit shape/colour). 335 species have no PalmTraits row (post-2015 descriptions).
  - **6,031 range records** across 2,573 species (5,482 native + 549 introduced) — TDWG level-3
    native/introduced from the WCVP checklist distributions (GBIF). 66% of species are single-region
    endemics. Stored as region codes joined to the shared TDWG geometry, not per-species polygons.
  - **1,730 conservation assessments** — **Bellot et al. 2022** predicted risk (438 real IUCN +
    1,292 ML-predicted, with probabilities), from the authors' CC-BY-4.0 workflow (GitHub
    `sidonieB/palm_extinction_risk_ML` / Zenodo 6678122), not the paywalled supplement. Threatened
    share is a range across the paper's two scenarios (50% high-precision → 72% high-sensitivity);
    exact headline figure to be pinned to the paper text before UI display. 861 species uncovered =
    "not evaluated," not "safe."
  - **Phylogeny** — the **Faurby 2016** complete supertree (`data/palmtraits/TREE.nex`, CC0), 5,077
    nodes (2,539 tips), parsed to `tree` + `phylogeny_node`; 2,488 tips reconciled via NameAlias,
    2,235 accepted species on the tree (86%). Topology verified (1 root, no orphan parent refs). The
    file has branch lengths but no node support (support left null). Constraint- vs molecular-placed
    tips not distinguished in the file.
  - **20 cited sources** (`etl/sources.py`) in `data_source`.

## Data sources & access notes

- **WCVP** (names) — GBIF species API against the Kew WCVP checklist, family node **326661320**. No token.
- **PalmTraits 1.0** — Dryad put its download API behind auth (401); pulled the **byte-identical** file
  from the GitHub mirror `EmilHvitfeldt/palmtrees` (`data-raw/PalmTraits_1.0.txt`). In
  `data/palmtraits/`. **No leaf-architecture (pinnate/palmate) field exists in PalmTraits** — fan-vs-
  feather must come from Genera Palmarum later (spec corrected).
- Reusable geometry kept from Quercus: `data/tdwg_level3.geojson` (WGSRPD level-3), basemaps in
  `frontend/public/data/`.

## Frontend — live (dev)

React/D3 app rebuilt on the Quercus dark design system, rebranded Palmae. Runs at localhost:5173
(Vite) → proxy → localhost:8001 (API). **The oak API is on :8000, so the palm API uses :8001.** The
oak `frontend/src/components/*` are dead files (not imported); the live app is a fresh, small graph.

- **API** — `api/app/routes.py` rewritten for palms: `/sources`, `/search`, `/tree` (nested Faurby
  tree), `/ranges` (region richness + per-species), `/species-regions` (slug→native TDWG codes, for
  brushing), `/taxa`, `/taxa/coverage`, `/taxa/{slug}`, `/lens/traits`, `/lens/conservation`.
  `api/app/palette.py` recolored to subfamily + risk encodings.
- **Three surfaces** (nav in TopBar):
  - **Workbench** (default) — `Workbench.tsx` = `RadialTree.tsx` (2,539-tip radial cladogram, subfamily-
    coloured) + `LinkedMap.tsx`, brushed: hover a branch → clade highlights gold and the map lights up
    the union of its species' native regions. Click a tip → species card. **Working.**
  - **World Atlas** — `AtlasMap.tsx`, the richness choropleth (Colombia/Borneo hotspots).
  - **Field Guide** — `Catalogue.tsx`, searchable 2,591-species list + editorial detail cards with
    honest risk attribution (Bellot).
- **Map gotcha solved**: a few antimeridian-crossing TDWG regions (Fiji, Aleutians, Tuamotu) smear
  across the whole frame in d3-geo; dropped by a post-layout getBBox guard (`width > 0.6 * frame`).
- **Dev servers** die if their shell exits; restart the API with Bash `run_in_background`. Run cmds
  at the bottom of this file.

### Workbench features done (verified in browser)
- **Search-to-locate** — `SearchBox` in `Workbench.tsx` → `/search`; picking a species opens its card,
  traces a gold root-to-tip path on the radial tree (`RadialTree` `locate` prop), and lights its range
  on the map. Verified: *Ravenea louvelii* → Madagascar, "Threatened (IUCN)".
- **Clade drill-in** — click a branch → `CladeFocus.tsx`, a labeled scrollable rectangular cladogram
  (species names, subfamily dots, risk chips, clickable tips), "← full tree" back button, map stays
  linked to the clade. Matches Kew ToL's readable-subtree + search; we add the linked map + risk.
- **Region → tree + species (bidirectional)** — click a map region → `RegionPanel.tsx` lists its native
  palms (subfamily dots + risk chips, each opens the card), and in the Workbench the tree lights up the
  branches/tips that live there (`RadialTree` `highlightSlugs`). New endpoint `/regions/{code}/species`.
  Works in both Workbench (`LinkedMap` `onPick`) and World Atlas (`AtlasMap`). Verified: Brazil NE
  (89 spp), Madagascar (220 spp, mostly threatened Chrysalidocarpus). Brushing is now bidirectional.

## Next steps
*(Deploy is DONE — live at palmae.pages.dev, source on GitHub. Deploys stay manual by user's choice; a
GitHub Action could auto-deploy on push to main but needs a Cloudflare API token in repo secrets.)*
1. **The dedicated grower companion** — "will it grow where I live?" (co-equal locked decision, not yet
   built). The `climate_profile` (CMMT edge per species) + USDA-zone geography is the spine for it.
2. **The other lenses** (form-function, people-palms / ethnobotany — `use` and `photo` tables still empty).
3. **The palm-line time ribbon** (deferred, harder) — Eocene high-latitude fossils (Paleobiology DB) for
   the deep-time axis + WorldClim CMIP6 future for the warming axis. Currently a static present-day reveal.
4. **Genus-tree polish** — flag low-support clades (e.g. dim/mark nodes under ~70% bootstrap) so
   uncertainty is visible at a glance, not just on hover.
5. **Occurrence coverage** — the bulk fetch covers 1,192 of 2,591 species (rare/newly-described palms have
   few/no GBIF records). A GBIF Download DOI snapshot would raise coverage + give a citable dataset.

### Known rough edges (polish)
- API dev process keeps getting reaped between shells — run it via Bash `run_in_background` and don't
  `pkill` it mid-session. When it dies, the species card hangs on "Loading…" (should show an error).
- The species-card overlay covers the map's right edge (hides Madagascar during a locate).
- Hovering the tree overrides an active locate highlight (transient; clears on mouse-out).
- Kew parity gap we can't close honestly: **node support values** — the Faurby tree file has none;
  would need the PAFTOL backbone.

### Data refinements (as we go)
- Tree: label key internal nodes by subfamily/tribe (MRCA pass) so the tree collapses cleanly; the
  Tree source row still shows the pre-edit Bellot note until the next full `run.main()` re-seeds sources.
- Leaf architecture (pinnate/palmate/costapalmate) from Genera Palmarum — absent in PalmTraits.
- Full IUCN category (VU/EN/CR) for assessed species via the IUCN v4 API (needs a token) or the Bellot
  `IUCN_TS_detail` field — currently only binary threatened/not is loaded.
- 84 species unplaced to subfamily + 356 species off the tree = post-2015 taxa; refresh from current
  Genera Palmarum / a newer tree when available.
- `use` (ethnobotany) and `photo` (iNaturalist CC) tables are still empty.

## Run

```bash
# ETL — all loaders end to end (sources → taxonomy → traits → ranges → conservation → tree),
# idempotent via a full clear. ~2–4 min (GBIF fetches dominate).
PYTHONPATH=api .venv/bin/python -m etl.run

# Palm-line ingest (on top of the loaded spine): GBIF native occurrences × WorldClim CMMT
# → occurrence + climate_profile. ~10–14 min. Needs data/worldclim/wc2.1_10m_tavg_*.tif.
PYTHONPATH=api .venv/bin/python -m etl.occurrences
# Deterministic renegade backfill (the curated hardy palms, cap 300, sequential):
PYTHONPATH=api .venv/bin/python -m etl.occurrences --renegades

# Genus-level tree (Yao 2023) as a second tree (tree_id=2); needs data/yao2023/ tree file:
PYTHONPATH=api .venv/bin/python -m etl.yao

# Bake the read-only API to static JSON (in-process; needs DATABASE_URL, no running API):
PYTHONPATH=api .venv/bin/python -m etl.export_static
# then: npm run build --prefix frontend   → frontend/dist (static site, baked /api/*.json)
# then: npx wrangler pages deploy frontend/dist --project-name palmae   (needs CF login)

# API (palm uses :8001; oak owns :8000)
PYTHONPATH=api .venv/bin/uvicorn app.main:app --app-dir api --port 8001

# Frontend → http://localhost:5173
npm run dev --prefix frontend
```

## Run it
```bash
# ingest (needs api/.env)
PYTHONPATH=api .venv/bin/python -m etl.run
# migrations
cd api && ../.venv/bin/alembic upgrade head
```
