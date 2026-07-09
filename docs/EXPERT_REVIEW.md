# Expert-readiness review — Palmae atlas

*Date: 2026-07-08 · Purpose: surface what expert palm botanists, systematists, ecologists,
and conservation biologists would find wanting, before sharing with Scott Zona and colleagues.*

> **Status — 2026-07-08.** The "fix before sharing" honesty items are done and deployed: the card no
> longer implies a live IUCN pull (assessed species read "(assessed)", sourced via Bellot 2022); the
> Sources entries for IUCN, WorldClim (now states 10-arc-min), GBIF (no false Download-DOI claim), and
> Faurby (no false "shown as uncertain" claim) are corrected; the stale oak IUCN test is rewritten.
> **#5 (range origin) is staged in code (`etl/run.py`) but inert until an ETL re-run** — the collapsed
> origins are already baked into the live data. Larger follow-ups (real IUCN loading, occurrence
> cleaning #6, phylogram #8, synonyms #11, export #19) remain open.

This is a self-critique, grounded in an audit of the actual pipeline (ETL → API → UI), not a
description of intentions. Findings are grouped by urgency. The most important are not the tree's
visual conventions — those are largely fixed — but a handful of places where the running atlas
**states or implies data it does not actually hold**. Those must be resolved before an expert
audience sees it, because they read as overclaiming rather than as honest limitations.

---

## Fix before sharing — the atlas implies data it doesn't have

These are integrity gaps between what the UI/Sources page claims and what the database contains.
An expert will find these fast, and each one costs trust disproportionately.

1. **IUCN Red List categories are not loaded, yet the UI implies they are.**
   The card renders an "(IUCN)" badge for species flagged *assessed*, and the Sources page cites
   "IUCN Red List API v4 (2025)." In reality `etl/iucn.py` is still the oak-project code
   (`fetch_quercus_assessments`, Fagaceae) and is never run; `iucn_category`, `assessment_year`,
   `criteria`, and `population_trend` are uniformly NULL. The "assessed vs predicted" distinction
   comes from **Bellot 2022's own flag**, not the Red List — so no CR/EN/VU category or assessment
   year exists anywhere. A conservation-literate reviewer looks for the category and year first.
   - **Action:** either load real IUCN assessments (category, year, criteria) for the assessed
     palms, or — until then — remove the "(IUCN)" implication, state plainly that risk is the
     Bellot 2022 **prediction only**, correct the Sources entry, and fix the stale oak test
     (`api/tests/test_data.py` still asserts ≥5 distinct `iucn_category` values).

2. **WorldClim resolution is misstated: "1 km" advertised, ~18.5 km used.**
   The climate layer samples WorldClim 2.1 **10-arc-minute** `tavg` rasters (~18.5 km at the
   equator), but the Sources entry cites the WorldClim 2 paper by its "new 1-km resolution" title.
   - **Action:** either compute on the 30-arc-second (1 km) grid, or state 10 arc-minute honestly.

3. **The "placement uncertainty" claim is unbacked.**
   Prose/Sources say constraint-placed tips (species lacking molecular data) "are shown as
   uncertain," but the `placement` field is never populated — it is uniformly NULL and nothing is
   shown. Systematists care a great deal which tips are molecularly supported vs taxonomically
   grafted onto the supertree.
   - **Action:** populate `placement` (mark grafted/constraint tips) and show it, or remove the claim.

4. **A "citable GBIF Download DOI" is claimed but not produced.**
   Sources says each ingest is a citable Download DOI; the pipeline uses the live GBIF **search
   API** with no DOI or download date recorded.
   - **Action:** generate a real GBIF download (mint the DOI, record the date), or drop the claim.

5. **Range origin over-assigns "native."**
   WCVP distribution `status` (extinct / doubtful / location-doubtful) is captured but discarded;
   origin is collapsed to `"introduced" if establishment=='introduced' else "native"`, so anything
   *not explicitly introduced* — including doubtful/unknown — silently becomes **native**.
   - **Action:** carry introduced/extinct/doubtful distinctly; do not promote doubtful to native.

---

## Methodological soft spots reviewers will probe

6. **Occurrence data are essentially uncleaned, and thin — and the Palm Line rests on them.**
   No coordinate cleaning at all: no removal of country/institution centroids, zero-coordinates,
   sea points, duplicates, or high-uncertainty records (`coordinate_uncertainty_m` is stored but
   never filtered). Native filtering is **country-level only** (TDWG level-3) — a cultivated palm
   in a country where the species is genuinely native still counts toward its climate envelope.
   The per-species fetch is capped at **~60 points** (300 for curated renegades). So each species'
   "cold edge" — the headline number on the Palm Line — is derived from ≤60 country-filtered,
   uncleaned occurrences. This is the single most likely thing a palm ecologist will challenge,
   precisely because palms are so widely cultivated.
   - **Action:** add coordinate cleaning (CoordinateCleaner-style), reconsider/raise and document
     the cap, and flag or down-weight low-*n* species.

7. **The frost-line narrative mixes paleo and neo.**
   The 2–8 °C threshold is Reichgelt 2018's *fossil*-palm paleothermometer calibration; mapping it
   onto modern realized niches is a compelling story but should be framed as analogy. Cultivated
   contamination (#6) directly threatens the renegade claims — a "renegade" cold edge could be a
   street tree or botanic-garden specimen.
   - **Action:** frame the calibration as analogy; spot-check each renegade's driving occurrences.

---

## What systematists will find wanting

8. **It's a cladogram; branch lengths and dates are discarded.**
   Faurby 2016 is time-calibrated and we carry the branch lengths (`len`), but the radial layout
   uses `d3.cluster` (equal depth) and ignores them. Divergence times are frequently the whole
   point for a systematist.
   - **Action:** offer a phylogram / time-scaled option (radius ∝ branch length, with a Ma axis).

9. **No node support on the species tree, and no nod to newer phylogenomics.**
   The Faurby supertree carries no support values (inherent to it) — that limitation should be
   stated at the tree. Reviewers will also expect the modern phylogenomic backbones (PAFTOL/Baker,
   Zuntini 2024 — already registered as sources) at least acknowledged, with a sentence on why the
   2016 supertree is used at species level and Yao 2023 for the genus backbone.

10. **Classification fidelity to *Genera Palmarum* 2 (2008) and post-2008 updates.**
    Subfamily/tribe assignments, genus concepts, and whether recent reclassifications are reflected
    are exactly what Zona will spot-check. The genus tree samples 177 of ~181 accepted genera.
    - **Action:** state the classification followed (GP2 + WCVP updates) explicitly, and do a pass
      over known trouble spots (e.g. Areceae/Dypsidinae, Chamaedoreeae) for concordance.

---

## What taxonomists / nomenclaturists will find wanting

11. **No synonyms or basionyms on the species card.** Synonymy exists in the DB (it powers search)
    but is never displayed; basionyms are not loaded at all. A taxonomist checking a name wants the
    synonymy and the basionym/protologue.
    - **Action:** surface accepted-name synonymy on the card; load basionym where available.

12. **WCVP version/date not pinned.** Only the 2021 paper is cited — give the checklist version and
    the access date, since palm names turn over.

13. **Species-only.** Infraspecific taxa (subspecies, varieties), of which palms have many, are out
    of scope — state it rather than let the absence read as completeness.

---

## What ecologists / biogeographers will find wanting

14. **TDWG level-3 ranges are coarse.** A whole botanical country overstates a narrow endemic; the
    filled-region range map can imply a far larger range than reality. The caveat exists, but
    consider finer representation (or occurrence-derived hints) for endemics.

15. **Occurrence cleaning and native/introduced surfacing** (see #6) — also show introduced vs
    native distinctly on the maps, not just in the Palm Line toggle.

---

## Conservation

16. **IUCN reality** (see #1) is the headline. Predicted probability is already shown distinctly
    ("p = …"); once real IUCN data is loaded, show category + year + criteria, and keep the
    predicted-vs-assessed line bright.

---

## Reproducibility & citation

17. **No "how to cite this atlas."** Add a self-citation (title, author, year, URL, and the
    underlying dataset DOIs). Anyone who uses it in work will need it.

18. **Pin every dataset version/date + the GBIF DOI** (see #2, #4, #12). Consider publishing a data
    snapshot/DOI for the atlas itself.

---

## Expert-user affordances

19. **No data export.** Scientists want the underlying table (species × range / traits / risk /
    climate) and per-region species lists as CSV/JSON.

20. **No faceted filtering.** Experts think in queries — "all threatened Madagascar endemics with
    stem > 10 m." A filter panel over traits/range/risk would land well.

21. **No per-taxon deep links.** A species view can't be bookmarked or cited (this is also the SEO
    follow-up already on the list — per-taxon URLs + prerender).

22. **Coverage honesty.** The coverage statistic omits the **photo** and **climate** layers (four
    of six layers are quantified; those two are only described in prose). Make per-layer coverage —
    including these — visible so users know what is and isn't populated per species.

---

## Presentation — largely addressed

23. **Branch style.** Now right-angled (the iTOL/FigTree convention) by default, with an
    angled/straight/curved toggle and an explicit "cladogram (relationships, not branch lengths)"
    label. Good. The substantive remainder is the phylogram/dates option (#8).

---

## Suggested order of work

- **Before showing anyone:** #1 (IUCN implication), #2 (WorldClim text), #3 (placement claim),
  #4 (GBIF DOI), #5 (native over-assignment). Mostly small honesty fixes — except loading real
  IUCN data, which is larger but the most important.
- **High-value next:** #6 (occurrence cleaning), #11 (synonyms), #8 (phylogram option),
  #19 (export), #10 (classification statement).
- **Then:** #20 (faceted filter), #21 (deep links), #14 (finer ranges), #22 (coverage honesty).
