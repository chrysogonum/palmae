# NEXT — planned work for Quercus

Concrete plans for the next session(s). Companion to `PROJECT_STATE.md` (current status) and the design
docs in `../` (`quercus-design-prompt.md`, `quercus-expeditions.md`, feedback rounds).

---

## 1. Cold-open intro (port from the design)

The one designed piece never ported to production. In the v4 mockup
(`../quercus_v4_extracted/Quercus Workbench.dc.html`, `drawCold`) it's a full-screen overlay on load:
a ghosted globe + a self-drawing tree + the thesis "One genus / Two hemispheres / A tangled tree" +
a live data-load narration, dismissed with a scale-up.

**Plan:** a React `<ColdOpen>` component shown while data loads (doubling as the load screen).
- Draw with D3/Canvas: ghosted Natural-Earth globe + a tree that draws itself + staggered thesis text.
- **Upgrade over the mockup** (per `../quercus-design-feedback-r4.md`): make the tree the *actual*
  Quercus topology, and on dismiss **morph into the workbench** (tree → the left spine, globe → the
  real map) rather than fade to a separate screen.
- Respect `prefers-reduced-motion` (skip straight to the assembled workbench).
- Add a store flag `intro:true`; dismiss when data is ready + a min time elapsed.

## 2. Scale from 5 → all ~500 oak species

The big one. Drive it with **`/goal` + auto mode against `./verify.sh`** (make verify's data invariants
genus-agnostic first — e.g. "zero unresolved names" holds; drop the hardcoded 1,250 assertion).

- **Taxonomy:** ingest the full WCVP Quercus checklist (bulk download) → `taxon` + `name_alias` for all
  accepted species + synonymy. **Reconciliation is the hard part** — budget for the ~5–15% that won't
  auto-match (hybrids, misspellings, section reassignments).
- **Occurrences:** move from the per-species GBIF *search* API to a **GBIF Download (DOI) snapshot**
  (needs a free GBIF account → creds in `api/.env`: `GBIF_USER/PWD/EMAIL`). Replace the hardcoded
  native-range bboxes with real **IUCN/WCVP TDWG range** per species for the native/introduced split.
- **Conservation:** IUCN Red List API for all assessed species (needs `IUCN_API_TOKEN` in `.env`).
- **Phylogeny:** ingest the full Hipp 2020 tree (632 tips); map tips → accepted species (curated, lossy).
- **Traits / photos:** TRY/BIEN batch; iNaturalist default photos for all species (cached).
- **Credentials to gather up front:** GBIF account, IUCN Red List API token. (iNaturalist token optional
  — public reads work without it.)

## 3. More ways to slice & dice

- **Facets/filters** usable everywhere: section/subgenus, IUCN status, leaf habit, native region.
- **New colour-by modes:** IUCN status, section, and *climate* (needs per-point MAT — add a WorldClim
  sample at ingest, currently null).
- **Cross-filtering / brushing:** brush the Lens A climate cross-plot → highlight on map + tree.
- **Time axes:** phenology (leaf-out / flowering / acorn), deep-time biogeography animation, future
  range-shift — the three time modes from the brief.
- **Expert range polygons** as a shaded layer (alongside the occurrence points).
- **Compare mode** (two species side by side) and **saved views** (shareable workbench state — the
  deep-link engine already exists).

## 4. Comprehensive data reference (linked bibliography)

- Expand the `data_source` table with full citation fields (`authors, year, title, venue, doi, url`).
- A **Bibliography / Data Reference** surface listing every source with a proper citation + DOI/URL +
  license. Seed from the current `data_source` rows and the frontier-research bibliography in the design
  docs.
- Make every in-app `[as-reported]` flag and Sources entry link into this reference.

## 5. "About / how it works" page

- The pipeline explained (GBIF · WCVP · Hipp 2020 · IUCN · iNaturalist → PostGIS → API → workbench).
- The chloroplast money-shot explained in plain language.
- The data caveats stated plainly: sampling bias, native-range clipping, the cpDNA-by-geography
  approximation, nearest-city geocoding.
- The non-commercial / attribution posture; credits; link to the bibliography.

---

**Sequencing suggestion:** cold-open + about/bibliography are quick wins (pure frontend/content).
The ~500 scale-up is the large, `/goal`-suited effort and should come with its credentials gathered
first. Slice-and-dice features can slot in incrementally once the data is broader.
