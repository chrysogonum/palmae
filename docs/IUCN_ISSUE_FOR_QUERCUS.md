# IUCN integration — issue found in Palmae, worth checking in Quercus

*Short handoff note. Context: the palm atlas (Palmae) was scaffolded from the Quercus app,
so some of its skeleton — including the IUCN and source-loading code — came straight from oak.*

## What we found in the palm app

The conservation layer **implied a live IUCN Red List integration that doesn't exist.**

- `etl/iucn.py` in the palm app is *literally the Quercus code* — `fetch_quercus_assessments()`,
  Fagaceae — copied over and never adapted, and never imported by the palm `run.py`. Result:
  `iucn_category`, `assessment_year`, `criteria`, and `population_trend` are **all NULL** in the palm DB.
- Meanwhile the UI showed an "(IUCN)" badge on species flagged *assessed*, and the Sources page cited
  "IUCN Red List **API v4 (2025)**, queried and displayed with attribution." **Nothing queried the API.**
  The assessed-vs-predicted split actually comes from **Bellot et al. 2022's own flag** (its ML model
  used existing IUCN assessments as training ground-truth), not from any Red List call.
- A data test still asserted `count(distinct iucn_category) >= 5` — an oak-era assumption that would
  **fail** on the palm DB (all NULL).

Net: the app claimed/implied data it didn't hold. We fixed it by relabeling honestly — assessed species
now read "(assessed)", sourced "via Bellot et al. 2022", with the Sources entry stating we do **not**
query the Red List API and do **not** display categories/years — until a real integration is wired up.

## Is it a problem in Quercus?

The **direct** cause is palm-specific: Quercus is where `iucn.py` *came from*, so Quercus presumably does
load real IUCN assessments (the oak app had ~421 assessed species). So the "no IUCN data" bug is probably
**not** present there. But three related things are worth a look, because the palm app inherited its
skeleton from oak:

1. **Claim-vs-reality audit (cheap).** Does the Quercus Sources page / UI describe its IUCN integration
   *accurately* — correct API version and currency (v3 vs v4), and actually running in the ingest? The
   palm failure mode was "the prose describes an integration that isn't wired up." Verify: does `run.py`
   actually call the IUCN loader, and are `iucn_category` / `assessment_year` genuinely populated?

2. **The citation-drift bug (definitely shared).** `load_sources` uses `session.add`, which only works
   because a full ingest calls `clear()` first. It **can't be run standalone** — re-running collides on
   the string PK (`data_source.id`). This reportedly already bit Quercus: the DB sat at 14 sources while
   the curated list defined 18, so the Sources page silently under-cited four real sources. **Fix:
   `session.add` → `session.merge`** (upsert). We just applied this in the palm app.

3. **Two source lists.** The palm app still carries a dead `curated.py` (the oak five-species
   vertical-slice seed) alongside the live `sources.py`; only one is loaded. Check Quercus doesn't have
   the same two-lists-one-loaded shape — that's exactly how the drift starts.

## One-line ask for Quercus

Confirm (a) `iucn_category` / `assessment_year` are actually populated in the Quercus DB and the Sources
text matches the real integration, and (b) `load_sources` upserts (`merge`) so added citations can't
silently drift.
