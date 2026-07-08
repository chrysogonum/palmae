# Palmae — hand-off prompt for a fresh session

Paste this (or "read /Users/peterrepetti/palms/HANDOFF.md") to bootstrap a new session. This session
will tackle **the palm-line money-shot**, the **About / Data / Citations pages**, and the remaining
backlog.

---

## What this project is

**Palmae** — an interactive, expert-facing web atlas of the palm family (**Arecaceae** / Palmae — NOT
Araceae). A sister project to **Quercus** (`/Users/peterrepetti/quercus/quercus-app`), reusing Quercus's
code + dark "observatory" design system as scaffold. Working dir: **`/Users/peterrepetti/palms`**; the app
is in **`palms-app/`**.

**Built first for Scott Zona** — palm anatomist, co-editor of *PALMS* (the IPS journal), possible AI
skeptic — as a surprise, with the hope the International Palm Society could adopt it. This sets the bar:
**scientific precision is pass/fail** (nomenclature, synonymy, morphology must be impeccable — he'll spot
errors); **AI-skeptic-proof honesty** (no model-written facts as truth; every figure sourced; predicted
risk framed as the peer-reviewed Bellot 2022 model, never "the AI"); **IPS-adoptable** (attribution is a
first-class surface).

**Read first:** `RESEARCH.md` (evidence base — what the palm community cares about + the data landscape),
`palms-spec.md` (the full spec), `palms-app/PROJECT_STATE.md` (current state, definitive), and
`palms-app/DECISIONS.md`.

**Four locked decisions:** (1) the money-shot is **the palm line** (palms as a living thermometer);
(2) the grower **"will it grow where I live?" companion is co-equal**; (3) **family-complete from day one**;
(4) conservation **leads with the open Bellot 2022 ML risk predictions**, IUCN a display-only overlay.

## Current state (what's built and working)

- **Database** — Supabase Postgres 17 + PostGIS 3.3. Full data spine loaded and verified: 2,591 species
  (placed to subfamily/tribe/genus), 6,754 name aliases, 39,811 traits (PalmTraits 1.0), 6,031 TDWG range
  records, 1,730 conservation assessments (Bellot), 5,077 phylogeny nodes (Faurby 2016, 2,539 tips), 20
  cited sources. Reproducible: `PYTHONPATH=api .venv/bin/python -m etl.run` (~2–4 min).
- **API** — FastAPI on **:8001** (the oak app owns :8000). Endpoints: `/sources`, `/search`, `/tree`,
  `/ranges`, `/species-regions`, `/regions/{code}/species`, `/taxa`, `/taxa/coverage`, `/taxa/{slug}`,
  `/lens/traits`, `/lens/conservation`, `/occurrences` (empty until the money-shot ingest).
- **Frontend** — React/D3, rebranded Palmae. Four linked surfaces: **Workbench** (radial 2,539-tip tree +
  world map, fully bidirectional: hover a clade → map lights up; click a region → tree + species panel
  light up; search-to-locate; click a branch → labeled clade drill-in), **World Atlas** (richness
  choropleth, click a region → its species), **Field Guide** (2,591-species catalogue + cards), and the
  species **cards** (honest predicted-vs-assessed risk). Live components: `App`, `Workbench`, `RadialTree`,
  `LinkedMap`, `CladeFocus`, `RegionPanel`, `AtlasMap`, `Catalogue`, `api/client`, `api/types`.

## Tasks for this session

### 1. The palm-line money-shot (the big one)
The signature reveal, for both audiences (growers' hardiness + scientists' paleoclimate proxy). The data
model is already there: `occurrence.cmmt` (coldest-month temp per point) and the `climate_profile` table
(cmmt_mean/min, hardiness_c, hardiness_zone, derived flag).

**Data ingest (new):**
- **GBIF occurrences** — family taxonKey **7681**, ~1.14M georeferenced. Fetch native points **cleaned of
  cultivated** (filter `establishmentMeans`; drop cultivated/managed), license-filter to CC0/CC-BY, cap per
  species. Tag native/introduced via the TDWG range we already have (`etl/wcvp.fetch_distributions` /
  `range_region`). Load into `occurrence` (geom, source, in_native_range, establishment_means).
- **WorldClim 2.1** — coldest-month temperature (bio6 = min temp of coldest month, or a derived CMMT).
  Sample at each native occurrence → `occurrence.cmmt`; aggregate per species → `climate_profile`
  (cmmt_mean, cmmt_min = the hardiness edge, derived hardiness estimate). Everything here is `[derived]`,
  not authoritative — flag it.
- **Calibration** — Reichgelt, West & Greenwood 2018 (*Sci Rep* 8:4721, doi 10.1038/s41598-018-23147-2):
  palms indicate coldest-month mean ≈ 2–8 °C — the frost line. Already in `data_source` as `reichgelt2018`.
- **Hardy renegades** — a curated set that breaks the line (Trachycarpus fortunei, Rhapidophyllum hystrix,
  Nannorrhops ritchiana, Jubaea chilensis, Sabal minor, Chamaerops humilis, Washingtonia, Butia). Verify
  each against the data.
- **Deep time / future** (optional, harder): Eocene high-latitude palm fossils (Paleobiology Database) for
  the deep-time axis; WorldClim CMIP6 future for the warming axis + USDA zone geography. May start as a
  curated illustrative layer.

**Frontend reveal:** a map mode toggle (occurrences → coldest-month-temperature surface); the family snaps
to the frost isotherm; the renegades light up where palms grow past the line; a time ribbon (Eocene →
today → +warming). Reuse the single-toggle-recolor + time-ribbon primitives. Hands off into the grower
"will it grow where I live?" question.

### 2. About / Data / Citations pages
Attribution as a designed surface (Zona/IPS bar). The 20 sources are already fully cited in the
`data_source` table (served by `/sources`, seeded from `etl/sources.py`). Build:
- an **About / How it works** page — the pipeline in plain language, the palm-line thesis, the data
  caveats, and the honest gaps (14% of species off the tree; binary-only IUCN category; predicted vs
  assessed risk; PalmTraits has no leaf architecture; Faurby tree has no node support; derived hardiness).
- a **Sources & bibliography** page — every dataset with full citation + DOI/URL + license, from `/sources`.
The oak app had these as `Pages.tsx` (About + Bibliography) — dead oak code to adapt, not reuse verbatim.

### 3. Remaining backlog (from PROJECT_STATE)
- The other lenses (form & function, people & palms / ethnobotany) and the **grower companion** surface.
- **Deploy** — `etl/export_static.py` bakes the API to static JSON + Cloudflare Pages → a URL to show
  Scott. It was written for oak endpoints; verify/extend for the palm endpoints. This removes the live-API
  dependency entirely.
- **Production build cleanup** — port or delete the dead oak `frontend/src/components/*` so
  `tsc -b && vite build` passes (dev works because esbuild only compiles the live import graph).

## Operational gotchas (important)
- **API on :8001** (oak owns :8000). The dev API process gets **SIGTERM'd (exit 144)** by the environment
  shortly after any *foreground* Bash runs — start it with Bash `run_in_background`, don't `pkill` it
  mid-session, and go **straight to the browser** (no foreground bash between start and test). When it
  dies, the species card hangs on "Loading…" and maps come up empty. Restart:
  `PYTHONPATH=api .venv/bin/uvicorn app.main:app --app-dir api --port 8001`.
- **`api/.env`** holds the Supabase `DATABASE_URL` (session pooler, port 5432). Gitignored — never commit.
- **Frontend** — Vite dev on :5173 proxies `/api` → :8001. Hard-reload after edits sometimes needs a
  cache-buster: `location.replace('http://localhost:5173/?t='+Date.now())` in the browser console.
- **Map antimeridian artifact** (Fiji/Aleutians/Tuamotu smearing) is solved by a post-layout getBBox guard
  (drop paths wider than 0.6 × frame) — keep it in any new map component.
- **Data sourcing** — WCVP via GBIF checklist (Arecaceae node 326661320); PalmTraits from the GitHub mirror
  `EmilHvitfeldt/palmtrees` (Dryad's download API is auth-walled); Faurby tree at
  `palms-app/data/palmtraits/TREE.nex` (user hand-downloaded from Dryad); Bellot risk from GitHub
  `sidonieB/palm_extinction_risk_ML` (CC-BY-4.0). Dryad blocks programmatic download — if you need another
  Dryad file, ask the user to grab it in a browser.

## Run
```bash
cd /Users/peterrepetti/palms/palms-app
PYTHONPATH=api .venv/bin/python -m etl.run                                  # ETL (needs api/.env)
PYTHONPATH=api .venv/bin/uvicorn app.main:app --app-dir api --port 8001     # API
npm run dev --prefix frontend                                               # → http://localhost:5173
```
