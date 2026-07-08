# Palmae — a living atlas of the palms (project spec, draft 1)

> **Working title:** *Palmae* (the old botanical name for Arecaceae — a real Latin word meaning "the
> palms," a natural sister to *Quercus*; alternatives welcome). A comprehensive, interactive pedagogical
> instrument about the natural history, evolution, geography, cultivation, and conservation of the palm
> family, worldwide.
>
> This is the build spec, poured into the **Quercus architecture as scaffold**. We are not re-running the
> design exploration — Quercus's design language (editorial-science, linked phylogeny + map workbench,
> lens system, expeditions, honest-data discipline) is inherited. This document specifies the palm-native
> *content, data, and features* that go into that shape, and where palms depart from oaks. It is grounded
> in `RESEARCH.md` (what the palm community actually cares about + the data landscape).

---

## 0. The four decisions this spec is built on

1. **The money-shot is the palm line** — palms as a living thermometer. §8.
2. **The grower "will it grow where I live?" surface is co-equal** with the expert workbench. §12.
3. **Family-complete from day one** — all ~2,600 species on the tree, traits, and TDWG ranges. §4, §14.
4. **Conservation leads with the open Bellot 2022 ML risk predictions**, IUCN a labeled display-only
   overlay. §7, §14.

---

## 1. The one-paragraph elevator

*Palmae* puts the **palm tree of life** and a **world map** side by side as co-equal, tightly-linked
partners, and lets you drop analytical lenses onto that pair to surface relationships only obvious once
you see them graphically — how the family's whole distribution is drawn by a **frost line** that a
handful of renegades cheat; how island chains **build their own palms** and then blur them together by
hybridizing; how form explodes from stemless understory palms to canopy giants to 200-metre climbing
rattans; how palms **feed and furnish people** across the tropics; and how **more than half the family may
be sliding toward extinction**. It is expert-first, but it is also, co-equally, for the grower standing in
their garden asking *will this palm survive my winter, and where do I get one* — the two audiences the
International Palm Society already contains.

---

## 2. Audience & the central design tension

The palm world is one society (the **International Palm Society**) with **two large, organized wings**,
and the product must serve both as first-class citizens (this is the main structural departure from
Quercus, which made the expert primary and the hobbyist secondary):

- **The palm scientists** — discover / name / delimit rare palms, resolve species limits with nuclear-gene
  phylogenies, tell it as field expedition. Center of gravity: threatened island-endemic palms of
  Madagascar, Hawaii, Fiji, New Caledonia, the Philippines, and Pacific atolls.
- **The palm growers** — obsessed above all with **growing palms past their climatic limits** (cold
  hardiness, zone-pushing, microclimate engineering), plus field ID, sourcing rare seed, and
  private-garden culture.

They are bound by **conservation**, a **collector-and-conservationist double identity** (distributed seed
is the ex-situ safety net), and **ethnobotany**. Design so the palm line reveal lands for both wings at
once, and so a selection made in the expert workbench carries straight into the grower companion.

---

### Who this is first built for — the acceptance test

The first person to see this is **Scott Zona** — palm anatomist, co-editor of *PALMS*, and a possible AI
skeptic — with the hope that the **International Palm Society could eventually adopt it**. That sets the
bar and three hard rules that override convenience everywhere below:

1. **Scientific precision is pass/fail.** A world expert will spot a wrong authority, a botched synonym, a
   sloppy morphological claim, or a misplaced tip instantly. Nomenclature, synonymy, classification, and
   morphology must be impeccable — keyed to WCVP / Genera Palmarum / PalmTraits, with provenance shown.
   Never invent a fact to fill a gap; mark it absent.
2. **AI-skeptic-proof honesty.** Nothing model-written is presented as fact. Species text comes from cited
   sources (POWO/Kew, Wikipedia CC-BY-SA with attribution, the journal), not generated prose. The
   predicted-risk layer is framed unmistakably as **the peer-reviewed Bellot et al. 2022 model** (Kew
   authors, incl. Zona's co-editor W. Baker) — a published scientific prediction, never "the AI guessed."
   The tool must read as built *by the palm world's own data and authorities*, because it is.
3. **IPS-adoptable, and a little personal.** Echo the PALMS/IPS aesthetic; credit Kew, the IPS, and the
   PalmTraits/Faurby authors prominently and in place. Include touches a palm anatomist would recognize —
   **palm anatomy/morphology as a real species-detail layer**, and the **hidden-diagnostic-character**
   delimitation motif his own journal prizes (e.g. the *Phoenix atlantica* leaflet cross-section).

## 3. Design principles (inherited from Quercus, held throughout)

1. **Two anchored views, many lenses.** The phylogeny and the map are always the spine; analytical layers
   are lenses dropped onto them, not separate destinations.
2. **Everything is linked, bidirectional.** Select anything anywhere, it lights up everywhere. A selection
   is a first-class, shareable object.
3. **Honest data.** Show coverage and uncertainty, not just point estimates. Predicted risk is labeled as
   prediction; a hardiness estimate derived from occurrences is labeled `[derived]`; Faurby tips placed by
   taxonomic constraint are shown as uncertain. Every figure traces to a source.
4. **Legible at family scale.** ~2,600 species across 5 subfamilies and every tropical continent must stay
   navigable via subfamilies/tribes, filters, and geographic slicing.
5. **The graphic is the argument.** Prefer a view that lets the user *see* a relationship over a panel that
   states it.
6. **Stand on prior work, visibly.** Open-source; reuse curated datasets (WCVP, PalmTraits, Faurby, GBIF,
   Bellot, iNaturalist) and credit every source in place. Attribution is a designed surface.
7. **Serve the grower as an equal, not a tourist.** The hardiness/sourcing/field-ID surface is a real
   instrument, co-registered with the expert workbench, not a shrunk-down mobile afterthought.

---

## 4. Core architecture — the workbench

The expert home is the Quercus workbench, palm-populated:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PALMAE     [ Expeditions ▾ ]   [ Lens: Climate × Geo × Phylo ▾ ]   [ ⌕ ] │
├───────────────────────────────┬───────────────────────────────────────────┤
│   PALM TREE OF LIFE           │            WORLD MAP  (co-equal)           │
│   Faurby complete tree,       │   occurrences / TDWG ranges / climate      │
│   collapsible: subgenus-free  │   surface / hardiness / risk               │
│   family → 5 subfamilies →    │   selection here lights up the tree        │
│   28 tribes → genera → spp.   │                                            │
├───────────────────────────────┴───────────────────────────────────────────┤
│  LENS PANEL — climate cross-plot / trait scatter / uses / risk (active lens)│
├─────────────────────────────────────────────────────────────────────────────┤
│  TIME RIBBON:  ◀ deep-time (Eocene poles) ──●── today ──── +warming ▶ + play │
└─────────────────────────────────────────────────────────────────────────────┘
    selection chips (shareable) · conservation filter · coverage toggle · "grow-it" handoff →
```

- **Tree (spine).** The complete **Faurby et al. 2016** species-level palm phylogeny (~2,600 tips),
  collapsible from the 5 subfamilies (Calamoideae, Nypoideae, Coryphoideae, Ceroxyloideae, Arecoideae)
  through the ~28 tribes (Genera Palmarum classification, attached per genus) to genera and species.
  Terminal placements of data-poor, constraint-placed species shown as uncertain. Deep-node ages and a
  nuclear backbone from PAFTOL / Zuntini & Baker 2024. Because there is no infrageneric subgenus layer as
  in oaks, the **subfamily → tribe → genus** hierarchy is the collapse ladder.
- **Map (co-equal).** Toggles between GBIF/iNat **point occurrences**, **TDWG level-3 range regions**
  (from PalmTraits/WCVP — the standard palm geography; few fine expert polygons exist), and per-lens
  surfaces: the **climate/frost-line surface** (the money-shot), **hardiness**, **predicted risk**, **trait
  color**, **use hotspots**. Lasso a region → the tree filters to what grows there.
- **Lens panel (bottom).** Reconfigures per active lens (§5).
- **Time ribbon.** Deep-time (palms at the poles in the Eocene), present, and future (warming/zone-shift) —
  the palm line's native third dimension.
- **Grow-it handoff.** Any species/selection carries into the co-equal grower companion (§12).

Family-complete arrives on day one for **tree + traits + TDWG ranges** (one open download). The
**rich-slice** treatment — dense occurrence points, the fully-wired money-shot, curated deep-trait/use
content — starts on a tractable, charismatic set and scales out (§14).

---

## 5. The lenses (the intellectual core)

Each lens = a question the user can probe graphically, grounded in what the community cares about.

### Lens A — Climate & the palm line (the flagship lens; drives the money-shot)
- **Questions:** Where can palms live, and why does their global range trace a **coldest-month
  temperature** isotherm? Which species **cheat the frost line**, and how? Where does the **plantable-palm
  zone** sit today, where was it in the Eocene, and where is it heading as the climate warms?
- **Graphics:** the map recolors from occurrences to a **coldest-month-mean-temperature surface**; a
  climate cross-plot (coldest-month temp × precipitation) with per-clade hulls; a **hardiness ladder** of
  the renegade species; the **time ribbon** sweeping the palm line from Eocene high-latitude palms to a
  future warmed distribution. This lens is where the grower's hardiness question and the paleobotanist's
  proxy meet.

### Lens B — Radiation & endemism
- **Questions:** How do island chains **build their own palms** (adaptive radiation)? Why do species
  boundaries **blur into hybridization** the closer you look (Hawaiian *Pritchardia*)? Where does
  **micro-endemism** concentrate diversity — and risk — into a single corner (Madagascar *Ravenea*,
  *Dypsis*; Fiji; New Caledonia)?
- **Graphics:** brush a genus/clade → its range and a **chronosequence** (e.g. the Hawaiian island ages)
  light up together; a diversity-by-region ridge with the Madagascar / New Guinea / Colombia peaks;
  a **zoom-to-blur** interaction where crisp species colors dissolve into admixture up close; single-locality
  endemics flagged.

### Lens C — Form & function
- **Questions:** How far does palm form stretch — stemless understory palms, canopy giants, **climbing
  rattans** (the largest genus, *Calamus*)? How does **leaf architecture** (pinnate / palmate /
  costapalmate / bipinnate) and **fruit size/color** map to habit and dispersal?
- **Graphics:** the **PalmTraits** trait-space scatter with clade hulls; color the tree/map by any trait
  (stem height, climbing habit, leaf type, fruit size); a habit spectrum from acaulescent to 60-m
  *Ceroxylon*; fruit-size × disperser cross-plot (the extinct-disperser anachronism lives here).

### Lens D — People & palms (ethnobotany & economic botany)
- **Questions:** Which palms furnish and feed people, and where — **rattan** cane and weaving, **thatch**,
  **palm heart**, **date**, **coconut**, **oil palm**, **sago**, **betel**, **palm wine**, **carnauba
  wax**? Where does human use overlap with threat (rattan over-harvest, wild-coconut dilution)?
- **Graphics:** a palm↔use bipartite view (species ↔ use categories); use-hotspot map layers; the
  harvest-pressure overlay that ties into conservation. Distinctly palm, and both wings love it.

### Conservation — a cross-cut, not a lens (§7)
Risk color / filter / sort available on every lens.

---

## 6. Genetics & evolution surfaces (woven through)

- **Phylogenomic backbone + uncertainty** — the tree itself, with constraint-placed tips and
  deep-node date ranges shown honestly.
- **Radiation & hybridization** — Lens B (the *Pritchardia* zoom-to-blur; admixture where island species
  meet).
- **Deep-time biogeography** — the time ribbon: palms as an old (Cretaceous-crown) lineage; the
  Eocene high-latitude palm record.
- **Genomes** — per-species link-outs to NCBI for the sequenced palms (oil palm, date, coconut, betel,
  rattan); note that no palm is in Ensembl Plants (a future genome layer would be white space).

---

## 7. Conservation — first-class, cross-cutting

Not a page; a dimension everywhere (color, filter, sort). Led by **open, family-wide predicted risk**.
- **Predicted extinction risk (Bellot et al. 2022)** as the spine — a risk category for ~75% of the family,
  with **over half of all palms predicted threatened**. Labeled as *prediction*, distinct from formal
  assessment.
- **IUCN Red List** category as a **display-only overlay** for the ~20% formally assessed (license-
  restricted; queried live, attributed, never rehosted).
- **Ex-situ safety net** — BGCI GlobalTreeSearch/PlantSearch for the arborescent subset; the
  collector-as-conservationist loop (distributed seed → living collections) made visible.
- **Signature conservation graphics:** a richness × %-predicted-threatened map (Madagascar, New Guinea,
  Colombia, SE Asia hotspots); the **micro-endemism collapse** view (a genus crammed into one corner,
  ranges shrinking to single dots); harvest-pressure layers (rattan, wild-coconut dilution, oil-palm
  conversion); pest fronts (coconut rhinoceros beetle, lethal bronzing, *Rhynchophorus* weevils).

---

## 8. The money-shot flow — the palm line (BUILD THIS REAL)

The ~90-second reveal that makes someone *get it*. Wired end-to-end on real data.

1. Open on the world map, palm **occurrences** plotted (colored by subfamily). It looks like a band around
   the tropics.
2. Prompt: *"Now color the map by winter cold instead."* Toggle to the **coldest-month temperature
   surface**.
3. The map recolors — and the palms **snap to a line**: the family's whole distribution hugs the frost
   isotherm (coldest-month mean ≈ 2–8 °C; Reichgelt et al. 2018). Palms *are* a thermometer.
4. **The renegades light up.** The handful of species that break the line — *Trachycarpus fortunei* in the
   Alps and Britain, *Rhapidophyllum hystrix*, *Nannorrhops ritchiana*, *Jubaea chilensis*, *Sabal minor*,
   *Chamaerops humilis* — flag where palms grow *past* the frost line. A hardiness ladder ranks them.
5. **Run time.** The time ribbon sweeps: back to the **Eocene**, palms grow to the poles (fossil palms in
   the high-latitude record) as the line retreats toward the poles; forward under **warming**, the
   plantable-palm zone marches north — the growers' lived 2012 → 2023 USDA zone shift, extended.
6. A one-line, glossary-linked explainer: *palms lack the anatomy to survive sustained freezing, so where
   palms grow maps where it does not hard-freeze — which is why fossil palms date warm climates, and why a
   grower can read a hardiness map as a palm map.* **Handoff to the grower companion:** *"Where's the frost
   line where you live?"*

This single flow proves the thesis for both audiences — tree + map + climate + time, linked, revealing
something you can't see in a table — and it hands the expert reveal directly to the grower's own question.

**Reuses Quercus's money-shot primitives exactly:** single-toggle animated map recolor between layers;
synchronized substrates sharing one encoding; a time ribbon; an "open question / plain explainer" card;
a state → live handoff.

**Data for the reveal:** GBIF palm occurrences × **WorldClim** coldest-month temperature (bio6/derived
CMMT); the Reichgelt 2018 frost-line calibration; a curated **hardy-renegade** set with documented
cold-survival; **deep-time** high-latitude palm fossils (Paleobiology Database — the harder data feed,
may start curated); **future** WorldClim CMIP6 projections + USDA zone geography. Hardiness estimates are
`[derived]` from occurrence×climate, not authoritative.

---

## 9. Time — three axes on one ribbon

- **Deep evolutionary / paleoclimate** — palms as a paleothermometer: the frost line marching poleward in
  the Eocene, high-latitude fossil palms pinned, crown/divergence ages shown as ranges (disputed).
- **Seasonal / life-history** — the annual clock and the dramatic palm life histories: hapaxanthy
  (*Corypha*, *Metroxylon*, *Caryota* — decades of growth, one flowering, death) vs. pleonanthy;
  flowering/fruiting; the extinct-disperser anachronism.
- **Anthropocene / future** — warming-driven range and hardiness-zone shifts; the plantable-palm zone
  moving north; harvest/land-use pressure over time.

---

## 10. Species detail

A rich non-modal detail surface (right rail / expandable card): habit and fruit/inflorescence photos
(iNaturalist CC + journal-style plates), TDWG range thumbnail, position on the tree, PalmTraits key traits,
predicted risk + IUCN overlay + ex-situ holdings, uses, name history/synonymy (the community actively
debates genus reshuffling — *Dypsis*/*Chrysalidocarpus*, *Wallichia*/*Arenga* — so synonymy is
first-class), a **grow-it panel** (hardiness estimate, habit, sun/soil, germination notes), and jump-offs
back into the workbench and the grower companion.

---

## 11. The pedagogical on-ramp — expeditions & glossary

Authored **expeditions** (the Quercus format: a saved sequence of workbench states + narration that hands
over the controls) and a **living glossary** (every term of art a link). Draft three flagship expeditions:

1. **"The line palms draw"** — the palm-line money-shot (§8). Climate lens; both audiences; hands off into
   the grower companion ("find the frost line where you live").
2. **"An island makes its own palms"** — the Hawaiian *Pritchardia* radiation along the volcanic
   chronosequence, then the zoom-to-blur where species dissolve into hybridization; ends on the
   downhill-trap (extinct bird dispersers → fruit rolls downhill into the pigs/rats/beetle zone) and the
   conservation stakes. Lens B + conservation. (Fresh 2026 data: Keller et al., *PALMS* 70(1).)
3. **"Half the palms could vanish"** — the whole family by predicted risk (Bellot ML), zoom into
   Madagascar's *Ravenea* micro-endemism collapse, the ex-situ gap, and the collector-as-safety-net loop.
   Conservation cross-cut.

Glossary terms: *rattan, hapaxanthic/pleonanthic, acaulescent, costapalmate, coldest-month temperature /
frost line, adaptive radiation, introgression/admixture, micro-endemism, recalcitrant seed, ex-situ,
predicted vs. assessed risk.*

A grower-oriented expedition ("grow a palm where you shouldn't") can be authored later; expedition 1
already carries the seed of it via the handoff.

---

## 12. The grower companion — a co-equal surface

Not a shrunk workbench; a first-class instrument for the enthusiast wing (the newsletters ask for exactly
this):

- **"Will this palm survive my winter?"** — drop a pin / enter a location → the coldest-month temperature
  and hardiness zone there, and the palms that grow **outdoors / marginally / only under glass**, ranked.
  The consumer face of the palm-line money-shot.
- **Field ID, phone-first** — a fast lookup keyed on the distinctions growers actually argue about
  (fan vs. feather, solitary vs. clustered, acaulescent vs. caulescent, armed vs. unarmed) using
  PalmTraits + photos; works on a phone in the field.
- **Sourcing & availability** — where a species can be obtained (society sales/auctions, botanical-garden
  distributions, seed sources), with germination/customs caveats. This community's bottleneck is
  acquisition, not information. (Link-out, not rehost, for commercial vendors.)
- **Garden & feral log** — pin your own successes and mature specimens; surface iNaturalist **feral /
  spontaneous** palm occurrences (the "a *Trachycarpus* is naturalizing in Seattle" thrill), tied to the
  climate/warming layer.

Everything here co-registers with the expert workbench: a species opened in one is the same object in the
other.

---

## 13. Intellectual integrity (non-negotiable)

- **Coverage is a visible layer.** GBIF sampling is uneven (Mexico, New Guinea, Central Africa
  under-sampled); risk is *predicted* for most species; hardiness is *derived*. Surface it; never present a
  biased sample or a model output as settled truth.
- **Uncertainty is shown.** Constraint-placed tree tips flagged; divergence ages as ranges; predicted vs.
  assessed risk always distinguished.
- **Every figure is sourced**, clickable to its provenance and vintage.
- **Attribution is a designed surface** — WCVP (CC-BY), PalmTraits (CC0), Faurby/PAFTOL, GBIF (per-record
  license, filtered), iNaturalist (per-image CC), Bellot 2022, IUCN (attributed, display-only), Genera
  Palmarum (classification, print). Honor each license; IUCN and the hobbyist wikis (Palmpedia, PACSOA,
  PalmTalk) are **link-out, not rehost**.

---

## 14. Data — sources & model

**Name authority & join spine.** **WCVP (Kew)** as the source of truth for accepted names and synonymy
(CC-BY); ~2,600 accepted species, ~181 genera, 5 subfamilies. A **NameAlias** table is the linchpin
(as in Quercus): every incoming record — occurrence, trait, tree tip, risk row, use — resolves through
aliases to an accepted species before it can be linked. Load WCVP synonymy first; carry **name history**
because the community tracks genus reshuffling actively. Overlay the **Genera Palmarum** subfamily/tribe
classification per genus as a curated attribute.

**Core feeds (all open unless noted):**
- **Taxonomy** — WCVP bulk DwC-A (Kew SFTP / GBIF mirror), CC-BY 4.0; POWO/IPNI IDs for enrichment.
- **Phylogeny** — Faurby et al. 2016 complete species-level tree (`TREE.nex`, bundled in the PalmTraits
  Dryad package), CC0; PAFTOL / Zuntini & Baker 2024 for dated backbone (CC-BY).
- **Traits** — **PalmTraits 1.0** (Dryad, CC0): 2,557 species; growth form, climbing, stem height/diameter,
  armature, leaf type, fruit size/shape/color; **also bundles the species × TDWG range matrix + level-3
  shapefile**.
- **Occurrences** — GBIF (family taxonKey 7681), ~1.14 M georeferenced, DOI-minted downloads, filtered to
  CC0/CC-BY; iNaturalist research-grade via AWS Open Data (per-image CC).
- **Ranges** — TDWG WGSRPD level-3 regions from PalmTraits/WCVP (native/introduced). Point occurrences are
  *evidence*, TDWG regions are *authority* — never merged (the two-kinds-of-range rule from Quercus).
- **Conservation** — **Bellot et al. 2022** predicted risk (primary; confirm supplement license before
  rehosting rows vs. link-out); **IUCN v4 API** display-only overlay; **BGCI GlobalTreeSearch** ex-situ
  (tree subset, CC-BY-NC).
- **Climate (money-shot)** — WorldClim coldest-month temperature (present + CMIP6 future); Reichgelt 2018
  frost-line calibration; USDA zone geography (public domain); a curated hardy-renegade set; Paleobiology
  Database high-latitude palm fossils (deep-time; the hardest feed).
- **Uses** — a curated ethnobotany/economic table (rattan, thatch, heart, date, coconut, oil, sago, betel,
  wine, wax), sourced from the literature; no single open database exists, so this is curated with citations.
- **Genomes** — NCBI accessions (oil palm, date, coconut, betel, rattan) as link-outs.

**Core entities** (adapting the Quercus model):
- `Taxon` — `species_id` PK; `wcvp_id`, `ipni_lsid`, `gbif_taxon_key`; name, authorship, **genus, tribe,
  subfamily**, `is_hybrid`, `accepted_flag`.
- `NameAlias` — `species_id` FK, `raw_name`, `name_status` (synonym / basionym / former-genus-placement),
  `source`.
- `Occurrence` — GBIF/iNat point: lat/lon, `basis_of_record`, `event_date`, `license`, `native_flag`
  (from TDWG), `coordinate_uncertainty_m`, quality flags.
- `RangeRegion` — TDWG level-3 code, `origin` (native/introduced), `source`.
- `PhylogenyNode` / `Tree` — `branch_length`, `support`, `age_estimate`, `tip_label`, nullable
  `species_id`, `clade_label`, `placement` (molecular vs. constraint); supports multiple trees (Faurby
  complete, PAFTOL backbone).
- `Trait` — EAV: `trait_name`, value, unit, `source` (PalmTraits), `license`.
- `ConservationAssessment` — `predicted_risk` (Bellot) + `iucn_category` (display), `assessment_year`,
  `ex_situ_count` (BGCI), `source`, `is_prediction` flag.
- `ClimateProfile` — per-species coldest-month-temp envelope, precip, derived hardiness estimate + zone;
  `derived_flag`.
- `Use` — `use_category` (cane/thatch/heart/food/oil/wax/wine/ornamental…), `region`, `source`.
- `GeneticResource` — `resource_type` (genome/SRA), `accession`, external URL.

**Hard problems (design for these):**
1. **Name reconciliation is the whole game**, and palms churn genera live (*Dypsis*/*Chrysalidocarpus*,
   *Wallichia*/*Arenga*, *Retispatha*/*Calamus*). Carry name history; expect the community to notice.
2. **Tips ≠ species, and many Faurby tips are constraint-placed** — store placement method; show
   data-poor terminal placements as uncertain.
3. **Two kinds of range, never merged** — GBIF points (evidence) vs. TDWG regions (authority; few fine
   polygons for palms). Derive native/introduced from regions.
4. **Occurrence cleaning** — cultivated palms are everywhere (ornamentals, plantations); flag/clip so the
   climate/frost-line reveal isn't distorted by planted specimens. (This matters *more* for palms than oaks
   — the whole money-shot depends on native distribution, not garden palms.)
5. **Rare species are data-poor and are the conservation priorities** — nullable everywhere; "data absent"
   ≠ "trait absent"; show per-species completeness.
6. **Licensing is mixed** — PalmTraits CC0, WCVP/PAFTOL CC-BY, GBIF per-record, iNat per-image, IUCN
   restricted, BGCI CC-BY-NC. Store license per record; gate accordingly.
7. **Hardiness is derived, not authoritative** — flag `[derived]`; the authoritative hobbyist hardiness
   data (Palmpedia, PalmTalk, RHS) is unlicensed, so re-derive from occurrence×climate + public sources.

---

## 15. Aesthetic — inherited, palm-native motifs

Reuse Quercus's **modern editorial science** system (characterful display face + legible workhorse;
restrained near-neutral scaffold so the data carries color; encoding-first categorical hues consistent
across tree/map/plots; light + dark). Palm-native touches, drawn from the community's own publications:
- **Palette:** the PALMS journal's warm **sand/tan + forest green + cream**; the newsletters' pale
  sage-green tinted content blocks.
- **Motifs:** the journal's "**raking-light frond strip + one hero image**" cover device; habitat-first,
  authentic photography (lone emergent crowns, silhouetted fans against sky, human-for-scale field shots);
  black-background morphology plates; saturated fruit/inflorescence color reserved for the photos.
- **Encoding:** a subfamily keeps one color everywhere; sequential ramps for climate/temperature; a
  clear prediction-vs-assessment visual distinction for risk.
- **Motion with meaning:** the palm-line recolor, the time-ribbon sweep, the zoom-to-blur — every motion
  teaches.

---

## 16. What's reused from Quercus vs. new

- **Reused (scaffold):** the linked tree+map workbench; the lens system; the money-shot primitives
  (single-toggle recolor, synchronized substrates, time ribbon, open-question card, state handoff); the
  expedition format + glossary; the honest-data discipline; the name-reconciliation spine + NameAlias; the
  species-detail rail; the separate-surface pattern for scale; the editorial-science aesthetic; the
  React/TS + D3 + FastAPI + PostGIS stack and much of the code.
- **New / palm-specific:** the **palm-line climate money-shot** + climate/hardiness data pipeline; the
  **co-equal grower companion** (hardiness matcher, field ID, sourcing, garden/feral log); the
  **subfamily→tribe→genus** collapse ladder (no subgenus layer); **family-complete day one** (no slice
  scale-up arc); **predicted-risk-led conservation** (Bellot); the **uses/ethnobotany** lens; the palette
  and motif shift to palm sources.

---

## 17. Open questions (for iteration)
1. **Name/title** — *Palmae* as working title; open to alternatives.
2. **Build path** — assumed a production build reusing the Quercus design system + code (not a fresh
   design-prototype pass). Confirm.
3. **Rich-slice choice** — which charismatic set gets dense occurrence points + the fully-wired money-shot
   first (candidates: the hardy renegades + a well-mapped temperate-margin region for the palm line; or
   Coryphoideae fan palms, which hold both the renegades and the *Pritchardia* radiation).
4. **Deep-time feed** — how far to push the Eocene-palms-at-the-poles axis in pass one (Paleobiology
   Database fossils are the hardest data); may start as a curated illustrative layer.
5. **Grower data ethics** — sourcing/availability and hobbyist hardiness are largely unlicensed; confirm
   the link-out-and-re-derive posture.
6. **Your "lot more guidance"** — fold in whatever you've been holding.
```
