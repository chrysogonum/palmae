# Decisions — Palmae

## 2026-07-07 (deploy + version control)

**Decision:** Ship to **Cloudflare Pages** (live at palmae.pages.dev) and put the source in a **private**
GitHub repo (`github.com/chrysogonum/palmae`), with **manual deploys and no CI**.
**Reason:** The app is a "surprise for Scott" and the data carries non-commercial licences, so private for
now. No version control existed at all before this — the private repo gives history + off-machine backup
without exposing the project. Manual deploy keeps the loop simple; the user declined auto-deploy CI.
**Impact:** Repo root = `palms-app/` (context docs `RESEARCH.md`/`palms-spec.md`/`HANDOFF.md` copied in so
it's self-contained). Gitignored: `api/.env`, `node_modules`/`.venv`, the baked `frontend/public/api/` and
WorldClim rasters (both ETL-regenerated), `.deadcode-frontend/`. Deploys go local `dist` → Cloudflare via
`wrangler`, independent of GitHub; commit + push after changes. A GitHub Action could auto-deploy later
(needs a CF API token in repo secrets).
**Supersedes:** refines the static-deploy decision below (which is now executed).

## 2026-07-07 (genus-tree session)

**Decision:** Add a **modern genus-level tree** (Yao et al. 2023 plastid phylogenomics) as a toggle
alongside the Faurby 2016 all-species supertree — do **not** replace Faurby.
**Reason:** Faurby 2016 is old and has no node support, but it is the only *species-complete* palm tree,
and the app is family-complete (every species needs a tip). The modern phylogenomic data (Yao 2023,
PAFTOL) samples ~98% of *genera* with bootstrap support but isn't species-complete, so it can't replace
Faurby — it complements it. The user picked "add a genus-level view" over re-anchoring the deep backbone.
**Impact:** `etl/yao.py` loads a second tree (`tree_id=2`, method `yao2023`), pruned to one tip per
genus (177 genera), with bootstrap support on the clades. New endpoint `/tree/genera`. The Workbench tree
gains a "All species / Genera" toggle; the genus tree brushes the map by each genus's native regions and
shows bootstrap support on branch hover. Yao 2023 added to the Sources bibliography (21 sources).
Tree file: Yao Figshare (doi:10.6084/m9.figshare.20489916), the 349-accession matrix, via bsdtar (RARv4).

## 2026-07-07 (money-shot session)

**Decision:** `export_static.py` bakes the static site by calling the FastAPI route handlers
**in-process** (with a real DB session), not over HTTP.
**Reason:** The dev API on :8001 keeps getting SIGTERM-reaped by the environment (exit 144), which
killed a first HTTP-based bake mid-run at ~1,200/2,591. Calling the route functions directly uses the
exact same serialization with no server to reap, and is faster (no HTTP round-trips).
**Impact:** The bake needs only `DATABASE_URL`, no running API. Query-param endpoints are baked to
path-based files (`ranges/{slug}.json`, `palm-line-introduced.json`) and `/search` to a client-side
index; `api/client.ts` mirrors these paths under `import.meta.env.PROD`. Verified end-to-end by serving
`frontend/dist` as pure static files (python http.server) with the API down — Palm Line, client-side
search, species cards, tree-trace and map all work with zero live API. Dead oak components + oak
`store.ts`/`sections.ts` moved to `.deadcode-frontend/` so `tsc -b && vite build` passes.
Note: local `vite preview` still proxies `/api`→:8001 (inherits `server.proxy`), so preview a static
build with a plain static server, not `vite preview`. Cloudflare Pages has no such proxy.


**Decision:** The palm line uses **coldest-month MEAN temperature (CMMT)**, computed as the minimum
across WorldClim 2.1's twelve monthly `tavg` rasters — **not** `bio6` (coldest-month minimum).
**Reason:** The frost-line calibration (Reichgelt et al. 2018) is stated in CMMT (~2–8 °C). `bio6` runs
several degrees colder than CMMT (e.g. London bio6 = 1.5 °C vs CMMT = 4.6 °C), so using it would misstate
the line — a precision error a palm anatomist would catch.
**Impact:** `etl/worldclim.py` samples the min-of-twelve-tavg; the `occurrence.cmmt` and
`climate_profile` values are true CMMT. Everything CMMT-derived is flagged `[derived]` in the UI.

**Decision:** Occurrence ingest resolves each species to its **GBIF backbone taxonKey** at fetch time and
tags native/introduced by **point-in-TDWG-polygon vs. the WCVP native range**; the fetch **retries on
rate-limits**.
**Reason:** The stored `gbif_taxon_key` is the WCVP *checklist* key, which the occurrence index doesn't
use — occurrences must be fetched by the backbone key. The first run silently returned empty ranges for
rate-limited species (dropping famous renegades like Chamaerops); a retrying, lower-concurrency fetch is
deterministic and complete. The range authority (not the raw point) decides native vs introduced, so
cultivated garden points don't pollute the frost line.
**Impact:** `etl/gbif.py` gains `_get_with_retry`; `etl/occurrences.py` is a standalone ingest on top of
the loaded spine (`python -m etl.occurrences`), writing `occurrence` + `climate_profile`.

**Decision:** The palm line is a **top-level surface** ("Palm Line", the default landing view), not a mode
buried inside the Workbench.
**Reason:** It is the signature reveal for both audiences (growers' hardiness + the paleoclimate proxy);
it should be the first thing seen.
**Impact:** `PalmLine.tsx` — world map of native occurrences coloured by CMMT (diverging palette pivoted on
the frost line), a renegades panel with each species' data-derived cold edge, and an introduced-points
toggle. The species card gains a derived coldest-month-climate block.

## 2026-07-07

**Decision:** Build **Palmae** as a sister to Quercus, reusing the Quercus code + dark "observatory"
design system as scaffold — a **production build**, not a fresh design-prototype pass.
**Reason:** The user asked to scaffold on Quercus's finished design rather than re-run the design process;
the palm data (WCVP + PalmTraits + Faurby) is production-ready on day one.
**Impact:** Snapshotted the Quercus working tree into `palms-app/`; the design language, the linked
tree+map workbench pattern, the FastAPI/PostGIS/React-D3 stack, and the name-reconciliation spine carry
over. Oak-specific pieces (cpDNA, food-web, sections) were dropped.
**Supersedes:** N/A.

**Decision:** The palm API runs on **:8001** (the oak Quercus API owns :8000).
**Reason:** Both apps run in the same dev environment; :8000 was already bound by Quercus.
**Impact:** Vite proxies `/api` → :8001; `main.py` title = "Palmae API". A shared-port collision was the
first bug (oak data appeared in the palm app until the port moved).

**Decision:** **Family-complete from day one** — load all ~2,600 species (tree + traits + TDWG ranges) at
once, rather than the 5-species slice → genus scale-up arc Quercus used.
**Reason:** PalmTraits 1.0 (CC0) bundles traits + the complete Faurby 2016 species-level tree + a TDWG
range matrix; WCVP gives the whole family's names. The scaffold is available immediately.
**Impact:** No slice phase. 2,591 species placed to subfamily/tribe/genus on the first ingest.

**Decision:** **Conservation leads with the peer-reviewed Bellot et al. 2022 ML predictions**; IUCN is a
labeled display-only overlay. Show the model's **two published scenarios (50% high-precision → 72%
high-sensitivity)** as a range, not a single "56%," and always distinguish **predicted vs. assessed**.
**Reason:** IUCN is license-restricted and covers only ~20% of palms; Bellot covers ~75% and is open
(CC-BY-4.0, from the authors' own GitHub/Zenodo, not the paywalled Nature supplement). Honest framing is
non-negotiable for the Scott-Zona / AI-skeptic bar.
**Impact:** `conservation_assessment` carries `risk_basis` (assessed|predicted) + `predicted_category` +
probability. Cards read "Threatened (predicted)" vs "Threatened (IUCN)" with "Bellot et al. 2022" cited.

**Decision:** Source data around Dryad's auth wall — WCVP via the **GBIF-hosted checklist** (Arecaceae
node 326661320); PalmTraits via the **GitHub mirror `EmilHvitfeldt/palmtrees`**; Bellot risk via the
authors' **GitHub `sidonieB/palm_extinction_risk_ML`**. The Faurby `TREE.nex` was hand-downloaded from
Dryad by the user (browser download works even though the API is walled).
**Reason:** Dryad added auth to its download API (401); GBIF/GitHub mirrors serve byte-identical data.
**Impact:** ETL depends on no Dryad API. If another Dryad-only file is needed, ask the user to grab it.

**Decision:** Store TDWG ranges as **region codes joined to a shared geometry layer**, not per-species
polygons; the primary categorical encoding is **subfamily** (5 hues), not per-species colors.
**Reason:** 2,591 species × their regions would be huge as per-species geometry; a family can't have a
distinct hue per species. Efficient and legible at family scale.
**Impact:** `range_region` holds `tdwg_code` + `origin` (geom nullable); the map joins codes to
`data/tdwg_level3.geojson`. Subfamily colors are consistent across tree, map, and cross-plots.

**Decision:** After reviewing **Kew's Tree of Life Explorer** (the closest prior art), add
**search-to-locate** and a **labeled clade drill-in** to match its practical advantages; keep our
differentiators (linked map, traits, predicted+assessed risk). Do **not** attempt node support values.
**Reason:** Kew's tool is a sequencing-provenance browser (no map/traits/conservation); its real
advantages are search + a readable subtree. The Faurby tree file has **no node support**, so we can't show
it honestly without the PAFTOL backbone.
**Impact:** Built `SearchBox`, `CladeFocus`, and (per user) region → tree + species drill-down, making the
workbench fully bidirectional. Node support is a noted, honest gap.

**Decision:** Deploy as **static JSON baked by `etl/export_static.py` + Cloudflare Pages** (no live prod
DB), following Quercus's new direction. Supabase is the **build-time ETL database only**.
**Reason:** Removes the live-API dependency (the dev API keeps getting reaped) and hosting cost; the data
is read-only.
**Impact:** `export_static.py` must be verified/extended for the palm endpoints before deploy (it was
written for oak endpoints). Not yet done.
