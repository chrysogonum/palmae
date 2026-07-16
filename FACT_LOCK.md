# Validated Facts — Palmae
*Facts in this file are verified and should NOT be changed without explicit user instruction.*
*Last updated: 2026-07-15.*

## Supabase RLS / Security Advisor (verified 2026-07-15, against the live DB `tcsqhxyehkmolpoxwcms`)
- Live Alembic head is **`e7b3a91c4d20`** (RLS enabled, deny-all, on all 13 public app tables). Prior head
  was `0b06d8e2345c` (initial schema).
- The 13 app tables (taxon, occurrence, …) grant `anon`/`authenticated` **only `REFERENCES, TRIGGER,
  TRUNCATE`** — **no SELECT/INSERT/UPDATE/DELETE**. The anon key could never read or write app data; enabling
  RLS on them is hardening, not a real-hole fix, and does **not** clear the advisor.
- The Security Advisor's only `rls_disabled_in_public` **error is `public.spatial_ref_sys`** (1 error total;
  all 13 app tables cleared, `alembic_version` not flagged).
- `spatial_ref_sys` is **owned by `supabase_admin`** (not `postgres`); `anon`/`authenticated` hold full
  `SELECT, INSERT, UPDATE, DELETE` on it, **granted by `supabase_admin`**. So anon has real *write* access to
  the PostGIS projection table (public reference data, no app data/PII).
- **Cannot be fixed from our `postgres` role**: `ALTER TABLE public.spatial_ref_sys ENABLE ROW LEVEL
  SECURITY` → `ERROR: must be owner of table spatial_ref_sys` (tested in a rolled-back transaction, 2026-07-15).
  A `REVOKE` from `postgres` removes nothing (postgres isn't the grantor/owner). Only `supabase_admin`
  (i.e. a Supabase support ticket) or moving PostGIS off `public` could change it. Accepted as a known
  PostGIS false-positive.

## Real IUCN Red List v4 (verified 2026-07-09, from the live DB + API)
- **1,266** palms carry a genuine IUCN category (latest Global assessment, `iucn.py` fetch of family
  Arecaceae): **184 CR · 202 EN · 133 VU · 73 NT · 520 LC · 126 DD · 1 EW · 1 EX** (+ a few LR/*).
  1,300 assessments fetched, 1,266 matched to taxa (34 unmatched = synonym mismatches).
- Conservation coverage after the IUCN overlay: **2,021** species (1,327 assessed / rest Bellot-predicted).
- Header "threatened" count is now **1,124** (real IUCN CR/EN/VU + Bellot-predicted-threatened), down from
  1,238 under Bellot-only — the real assessments reclassify some.

## Deep time (verified 2026-07-09)
- The Faurby 2016 tree is **ultrametric** (stdev of root-to-tip = 0.0000): crown age **105.386 Ma** (units
  = millions of years), i.e. a **mid-Cretaceous** origin. Branch lengths are in `/tree` as `len`.

## Region climate & anomaly (verified 2026-07-09, WorldClim 2.1 zonal means over TDWG level-3)
- Rainfall (bio_12): Borneo **2,991 mm** · New Guinea 2,990 · Colombia 2,642 · Amazon (Brazil N) 2,224;
  vs W. Sahara **36 mm** · Saudi 103 · Niger 144. 367 regions computed.
- Richness×rainfall anomaly (rank residual, among CMMT≥10 °C + area≥8 sq° regions, 87 eligible): Gabon
  **−0.20** (wet but palm-poor — the tropical-Africa signal), Madagascar +0.35, Queensland +0.36,
  Borneo 0.0 (on the trend).
- Ranges re-derived (doubtful/extinct no longer promoted to native): **6,023** records / **2,572** species
  (8 doubtful/extinct records removed vs the prior 6,031).

## Sources registry (verified 2026-07-09)
- **22** sources in `data_source`; **6 à-la-carte** (registered, not loaded — reserved columns confirmed
  0 non-null): BGCI, IPNI, PAFTOL, Zuntini 2024, USDA-zones, PBDB. Kühnhäuser et al. 2025 (Science) added.

## Loaded data counts (as of the 2026-07-07 `etl.run` ingest)
Live counts drift with WCVP/GBIF versions; these are the verified state of this ingest.
- **2,591** accepted palm species (42 nothospecies); **6,754** name aliases (4,179 synonyms linked).
- **39,811** trait rows across **2,256** species (PalmTraits 1.0).
- **6,031** TDWG range records: **5,482** native + **549** introduced across **2,573** species.
  **1,700** species (66%) are single-region endemics.
- **1,730** conservation assessments: **438** IUCN-assessed + **1,292** ML-predicted (Bellot 2022).
- **5,077** phylogeny nodes / **2,539** tips (Faurby 2016); **2,488** tips reconciled; **2,235** accepted
  species on the tree (**86%** of the family).
- **20** cited sources in `data_source`.

## Subfamily counts (verified)
- Arecoideae **1,356** · Calamoideae **575** · Coryphoideae **526** · Ceroxyloideae **49** · Nypoideae
  **1** (monotypic *Nypa*) · unplaced-to-subfamily **84** (genera newer than PalmTraits' 2015 snapshot).
- Largest genera: *Calamus* **437** (the rattans, the family's largest genus), *Licuala* 149,
  *Pinanga* 145, *Chamaedorea* 114, *Dypsis* 108, *Syagrus* 83.

## Richness hotspots (native species per TDWG level-3 region, verified)
- Borneo **304** · Colombia **264** · New Guinea **244** · Madagascar **220** · Malaya **217**.

## Conservation (Bellot et al. 2022, verified from the source table)
- Threatened share of covered species = **50%** (high-precision model) to **72%** (high-sensitivity) —
  the paper's "more than half" range. Report as a range, never a single number. Assessed reality:
  **298 of 439** IUCN-assessed species are threatened.

## Palm-line money-shot (verified 2026-07-07, from the occurrence ingest)
- **37,289** cleaned wild GBIF occurrences (**30,943** native), **1,161** species climate profiles.
  Native/introduced set by point-in-TDWG-polygon vs. the WCVP native range.
- CMMT = **coldest-month MEAN** temperature = min across WorldClim 2.1's 12 monthly `tavg` rasters
  (10 arc-min). NOT `bio6` (coldest-month minimum), which runs several degrees colder than CMMT.
- Frost-line calibration: palms indicate CMMT ≈ **2–8 °C** or warmer (Reichgelt et al. 2018).
- Renegade native cold edges (CMMT min over native points, derived — verified): needle palm
  (*Rhapidophyllum hystrix*) **3.9 °C**, dwarf palmetto (*Sabal minor*) **3.2 °C**, windmill palm
  (*Trachycarpus fortunei*) **2.7 °C** (n=7, sparse native records), Mazari palm
  (*Nannorrhops ritchieana*) **−5.6 °C**, Mediterranean fan palm (*Chamaerops humilis*) **5.5 °C**,
  California fan palm (*Washingtonia filifera*) **6.5 °C**, Chilean wine palm (*Jubaea chilensis*)
  **7.4 °C**, cabbage palmetto (*Sabal palmetto*) **7.6 °C**, pindo (*Butia odorata*) **9.9 °C**
  (the one that sits at/above the line — shown honestly, not cherry-picked).
- The renegades are ingested by a **deterministic sequential backfill**
  (`python -m etl.occurrences --renegades`, cap 300); the bulk concurrent fetch can miss their sparse
  native points under GBIF rate-limits.

## Genus-level tree (Yao et al. 2023, verified this session)
- **177** genus tips, **176** internal clades with bootstrap support (range 15–100, mean ~79); 1 root,
  0 orphan parent refs. Loaded as `tree_id=2`, method `yao2023` (Faurby stays `tree_id=1`).
- Covers 177 of the ~186 genera we recognise; the ~9 missing are hybrid/very-recently-described genera
  Yao didn't sample (Butyagrus, ×Microphoenix, Jailoloa, Wallaceodoxa, Sabinaria, Truongsonia, …).
- Source: **Yao et al. 2023**, BMC Biology 21:50, doi 10.1186/s12915-023-01544-y; tree from the authors'
  Figshare doi:10.6084/m9.figshare.20489916 (349-accession "incomplete-105 regions" matrix), pruned to
  one representative tip per genus. It is NOT species-complete — it complements, not replaces, Faurby 2016.
- **21** cited sources now in `data_source` (added `yao2023`).

## Source keys / access (verified this session)
- WCVP: **Arecaceae node 326661320** in the GBIF-hosted WCVP checklist (datasetKey
  `f382f0ce-323a-4091-bb9f-add557f3a9a2`).
- GBIF occurrences: family **taxonKey 7681** (~1.14M georeferenced; not yet ingested).
- PalmTraits 1.0: **2,557** species; pulled from GitHub `EmilHvitfeldt/palmtrees` (byte-identical to the
  auth-walled Dryad `doi:10.5061/dryad.ts45225`). No leaf-architecture (fan/feather) field exists in it.
- Faurby 2016 tree: **2,539** tips, branch lengths but **no node support values**; `TREE.nex` (CC0).
- Bellot risk: GitHub `sidonieB/palm_extinction_risk_ML` / Zenodo `10.5281/zenodo.6678122`, CC-BY-4.0.
- Frost-line calibration: coldest-month mean ≈ **2–8 °C** (Reichgelt et al. 2018, doi
  10.1038/s41598-018-23147-2).

## Infrastructure
- Palm API port **8001** (the Quercus/oak app owns **8000**); Vite dev **5173**. Supabase Postgres 17 +
  PostGIS 3.3, session pooler port 5432.
