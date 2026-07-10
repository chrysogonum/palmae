"""The palm atlas provenance registry — the bibliography behind the Sources panel
and every per-field attribution.

Each entry maps 1:1 onto the `data_source` table (id, name, role, license, note,
authors, year, title, venue, doi, url). Keep citations complete and, wherever a
source has one, a resolvable DOI or a canonical URL — this tool is judged first by
a PALMS editor, so every figure must trace to a real, linkable source.

`run.load_sources` seeds these rows. This supersedes the oak `curated.DATA_SOURCES`;
when the palm ETL is wired against the database, `run.py` imports DATA_SOURCES from
here.
"""
from __future__ import annotations

DATA_SOURCES = [
    # --- Names & classification (the join spine) ------------------------------
    {"id": "wcvp", "name": "WCVP — World Checklist of Vascular Plants (Kew)",
     "role": "name authority · accepted names & synonymy", "license": "CC-BY 4.0",
     "note": "Source of truth for accepted palm names (~2,600 species, ~181 genera). "
             "Every incoming record resolves through a NameAlias table to an accepted "
             "taxon before it can be linked. Descended from the World Checklist of Palms.",
     "authors": "Govaerts R, Nic Lughadha E, Black N, Turner R, Paton A",
     "year": 2021,
     "title": "The World Checklist of Vascular Plants, a continuously updated resource for exploring global plant diversity",
     "venue": "Scientific Data 8:215",
     "doi": "10.1038/s41597-021-00997-6",
     "url": "https://powo.science.kew.org/"},
    {"id": "powo", "name": "POWO — Plants of the World Online (Kew)",
     "role": "descriptions · images · distributions", "license": "CC-BY 4.0",
     "note": "Per-species descriptive text, imagery, and TDWG distributions; the "
             "public front-end to WCVP. Cited in place for any description shown.",
     "authors": "Royal Botanic Gardens, Kew",
     "year": 2024,
     "title": "Plants of the World Online",
     "venue": "Royal Botanic Gardens, Kew",
     "doi": None,
     "url": "https://powo.science.kew.org/"},
    {"id": "genera-palmarum", "name": "Genera Palmarum, 2nd ed.",
     "role": "family classification (subfamily · tribe · genus)", "license": "© Kew Publishing (print)",
     "note": "The palm classification bible: 5 subfamilies, ~28 tribes, ~183 genera. "
             "Attached per genus as a curated attribute; text not redistributed.",
     "authors": "Dransfield J, Uhl NW, Asmussen CB, Baker WJ, Harley MM, Lewis CE",
     "year": 2008,
     "title": "Genera Palmarum: The Evolution and Classification of Palms",
     "venue": "Kew Publishing, Royal Botanic Gardens, Kew (ISBN 9781842461822)",
     "doi": None,
     "url": "https://www.kewbooks.com/asp/BookDetails.asp?BookId=239"},
    {"id": "ipni", "name": "IPNI — International Plant Names Index", "planned": True,
     "role": "stable name identifiers", "license": "CC-BY",
     "note": "Not yet integrated — the schema reserves a stable IPNI identifier per name, "
             "but it is not populated. A candidate layer, available on request.",
     "authors": "The International Plant Names Index (Kew, Harvard University Herbaria & ANBG)",
     "year": 2024,
     "title": "International Plant Names Index",
     "venue": "ipni.org",
     "doi": None,
     "url": "https://www.ipni.org/"},

    # --- Traits ---------------------------------------------------------------
    {"id": "palmtraits", "name": "PalmTraits 1.0",
     "role": "functional traits (whole family)", "license": "CC0",
     "note": "Species-level traits for 2,557 palms: growth form (climbing/erect/"
             "acaulescent), stem height & diameter, armature, leaf type (pinnate/"
             "palmate/costapalmate/bipinnate), fruit size, shape & colour. The same "
             "Dryad package also bundles the Faurby 2016 tree and a species x TDWG "
             "range matrix. Keyed to the World Checklist of Palms.",
     "authors": "Kissling WD, Balslev H, Baker WJ, Dransfield J, Göldel B, Lim JY, Onstein RE, Svenning J-C",
     "year": 2019,
     "title": "PalmTraits 1.0, a species-level functional trait database of palms worldwide",
     "venue": "Scientific Data 6:178 · data: Dryad doi:10.5061/dryad.ts45225",
     "doi": "10.1038/s41597-019-0189-0",
     "url": "https://doi.org/10.5061/dryad.ts45225"},

    # --- Phylogeny ------------------------------------------------------------
    {"id": "faurby2016", "name": "Faurby et al. 2016 — complete palm phylogeny",
     "role": "phylogenetic backbone (species-complete)", "license": "CC0 (Dryad)",
     "note": "The only complete species-level palm tree (~2,539 tips). It is a supertree: "
             "species without molecular data are grafted by taxonomic constraint. It carries "
             "branch lengths and dates, but the atlas currently renders it as a cladogram "
             "(topology only) and does not yet flag which tips are molecularly supported. "
             "Tree file bundled with PalmTraits 1.0.",
     "authors": "Faurby S, Eiserhardt WL, Baker WJ, Svenning J-C",
     "year": 2016,
     "title": "An all-evidence species-level supertree for the palms (Arecaceae)",
     "venue": "Molecular Phylogenetics and Evolution 100:57–69",
     "doi": "10.1016/j.ympev.2016.03.002",
     "url": "https://doi.org/10.1016/j.ympev.2016.03.002"},
    {"id": "yao2023", "name": "Yao et al. 2023 — plastid phylogenomic palm backbone",
     "role": "genus-level phylogeny (modern backbone)", "license": "CC-BY 4.0",
     "note": "A plastid phylogenomic framework sampling ~98% of palm genera with bootstrap "
             "support; powers the genus-level tree view in the workbench. It is not "
             "species-complete, so it complements rather than replaces the Faurby 2016 "
             "all-species supertree. Tree file from the authors' Figshare (doi:10.6084/"
             "m9.figshare.20489916), pruned to one tip per genus.",
     "authors": "Yao G, Zhang Y-Q, Barrett C, Xue B, Bellot S, Baker WJ, Ge X-J",
     "year": 2023,
     "title": "A plastid phylogenomic framework for the palm family (Arecaceae)",
     "venue": "BMC Biology 21:50",
     "doi": "10.1186/s12915-023-01544-y",
     "url": "https://doi.org/10.1186/s12915-023-01544-y"},
    {"id": "paftol", "name": "Baker et al. 2022 — Kew Tree of Life (PAFTOL)", "planned": True,
     "role": "nuclear phylogenomic backbone", "license": "CC-BY 4.0",
     "note": "Not yet integrated — the Angiosperms353 nuclear backbone would sharpen the "
             "tree's deep nodes and dating (we currently use Faurby for species, Yao for "
             "genera). A candidate upgrade, available on request.",
     "authors": "Baker WJ, Bailey P, Barber V, Barker A, Bellot S, Bishop D, et al.",
     "year": 2022,
     "title": "A comprehensive phylogenomic platform for exploring the angiosperm tree of life",
     "venue": "Systematic Biology 71(2):301–319",
     "doi": "10.1093/sysbio/syab035",
     "url": "https://treeoflife.kew.org/"},
    {"id": "zuntini2024", "name": "Zuntini, Baker et al. 2024 — dated angiosperm tree", "planned": True,
     "role": "divergence-time calibration", "license": "CC-BY 4.0",
     "note": "Not yet integrated — this dated angiosperm tree could re-anchor the chronogram's "
             "divergence times (which currently come from Faurby's supertree calibration). "
             "A candidate upgrade, available on request.",
     "authors": "Zuntini AR, Carruthers T, Maurin O, Bailey PC, Leempoel K, Brewer GE, et al.",
     "year": 2024,
     "title": "Phylogenomics and the rise of the angiosperms",
     "venue": "Nature 629:843–850",
     "doi": "10.1038/s41586-024-07324-0",
     "url": "https://doi.org/10.1038/s41586-024-07324-0"},
    {"id": "kuhnhauser2025", "name": "Kühnhäuser et al. 2025 — island geography & rattan diversity",
     "role": "biogeography of Asian palm diversity", "license": "citation",
     "note": "Species-level phylogenomics + fossils of the rattans (Calamoideae) show that "
             "region size and isolation — not climate alone — drive tropical-Asian palm "
             "diversity, classifying regions as radiators, incubators, corridors, and "
             "accumulators. The evidence behind the atlas's richness × rainfall anomaly "
             "(why wet-but-isolated regions are palm-poor) and the region-role layer.",
     "authors": "Kühnhäuser BG, Bates CD, Dransfield J, Bellot S, Eiserhardt WL, Baker WJ, et al.",
     "year": 2025,
     "title": "Island geography drives evolution of rattan palms in tropical Asian rainforests",
     "venue": "Science 387:6739",
     "doi": "10.1126/science.adp3437",
     "url": "https://doi.org/10.1126/science.adp3437"},

    # --- Occurrences & distribution -------------------------------------------
    {"id": "gbif", "name": "GBIF — Global Biodiversity Information Facility",
     "role": "occurrence points", "license": "CC0 / CC-BY (per record, filtered)",
     "note": "Georeferenced palm records (family taxonKey 7681; ~1.1M georeferenced). "
             "Point evidence for climate, filtered to CC0/CC-BY and to living/managed/fossil "
             "records removed. This build queries the GBIF search API (not a snapshot); a "
             "citable GBIF Download DOI is the intended provenance for a production run. Points "
             "are evidence; TDWG regions are authority — the two are never merged.",
     "authors": "GBIF Secretariat",
     "year": 2024,
     "title": "GBIF Occurrence Download (Arecaceae)",
     "venue": "GBIF.org",
     "doi": None,
     "url": "https://www.gbif.org/species/7681"},
    {"id": "tdwg", "name": "WGSRPD — World Geographical Scheme for Recording Plant Distributions",
     "role": "native/introduced range regions", "license": "CC-BY",
     "note": "TDWG level-3 botanical countries; native/introduced ranges per species "
             "from WCVP + PalmTraits. The standard geography for the whole atlas.",
     "authors": "Brummitt RK (TDWG / Biodiversity Information Standards)",
     "year": 2001,
     "title": "World Geographical Scheme for Recording Plant Distributions, ed. 2",
     "venue": "Hunt Institute for Botanical Documentation",
     "doi": None,
     "url": "https://www.tdwg.org/standards/wgsrpd/"},

    # --- Conservation ---------------------------------------------------------
    {"id": "bellot2022", "name": "Bellot et al. 2022 — predicted palm extinction risk",
     "role": "predicted conservation risk (whole family)", "license": "CC-BY 4.0 (authors' workflow)",
     "note": "Peer-reviewed machine-learning predictions of extinction risk for ~1,382 "
             "unassessed palms; combined with the assessed species this gives a threatened / "
             "not-threatened status for ~1,730 species. The model's two published scenarios "
             "estimate 50% (high-precision) to 72% (high-sensitivity) of covered palms are "
             "threatened — the paper's 'more than half' range. Shown as PREDICTION, distinct "
             "from a formal IUCN assessment. Loaded from the authors' own openly-licensed "
             "workflow (CC-BY 4.0; GitHub sidonieB/palm_extinction_risk_ML, archived "
             "Zenodo 10.5281/zenodo.6678122), not the paywalled supplement.",
     "authors": "Bellot S, Lu Y, Antonelli A, Baker WJ, Dransfield J, Forest F, et al.",
     "year": 2022,
     "title": "The likely extinction of hundreds of palm species threatens their contributions to people and ecosystems",
     "venue": "Nature Ecology & Evolution 6:1710–1722",
     "doi": "10.1038/s41559-022-01858-0",
     "url": "https://doi.org/10.1038/s41559-022-01858-0"},
    {"id": "iucn", "name": "IUCN Red List of Threatened Species (Arecaceae)",
     "role": "formal conservation status (assessed subset)", "license": "non-commercial · display-only (IUCN terms)",
     "note": "Formal Red List category, criteria and assessment year for the ~1,300 palms "
             "with a latest assessment — pulled from the Red List API v4 (family Arecaceae, "
             "keeping the latest Global-scope assessment per species) and shown with the real "
             "category (CR/EN/VU/NT/LC/DD) and year. Displayed with attribution, not rehosted. "
             "Species IUCN has not assessed fall back to the Bellot 2022 prediction. "
             "Assessments contributed by the IUCN SSC Palm Specialist Group.",
     "authors": "IUCN; IUCN SSC Palm Specialist Group",
     "year": None,
     "title": "The IUCN Red List of Threatened Species",
     "venue": "IUCN Red List API v4",
     "doi": None,
     "url": "https://www.iucnredlist.org/"},
    {"id": "bgci", "name": "BGCI GlobalTreeSearch & PlantSearch", "planned": True,
     "role": "ex-situ holdings (arborescent palms)", "license": "CC-BY-NC 4.0",
     "note": "Not yet integrated — the atlas reserves a slot for ex-situ living-collection "
             "counts (tree-form palms) from BGCI's GlobalTree Portal, but none are loaded. "
             "Rattans/acaulescent palms fall outside the tree definition. Available on request.",
     "authors": "Botanic Gardens Conservation International (BGCI)",
     "year": 2024,
     "title": "GlobalTree Portal (GlobalTreeSearch · PlantSearch)",
     "venue": "BGCI, Richmond, UK",
     "doi": None,
     "url": "https://www.bgci.org/resources/bgci-databases/globaltree-portal/"},

    # --- Climate (the palm-line money-shot) -----------------------------------
    {"id": "reichgelt2018", "name": "Reichgelt, West & Greenwood 2018 — palms & climate",
     "role": "frost-line calibration", "license": "CC-BY 4.0 (open access)",
     "note": "Quantifies the palm frost line: palms indicate a coldest-month mean "
             "temperature of roughly 2–8 °C, the calibration behind the money-shot and "
             "the paleoclimate proxy. Freeze tolerance is reduced under high CO₂.",
     "authors": "Reichgelt T, West CK, Greenwood DR",
     "year": 2018,
     "title": "The relation between global palm distribution and climate",
     "venue": "Scientific Reports 8:4721",
     "doi": "10.1038/s41598-018-23147-2",
     "url": "https://doi.org/10.1038/s41598-018-23147-2"},
    {"id": "worldclim", "name": "WorldClim 2.1",
     "role": "climate surfaces (present & future)", "license": "CC-BY 4.0",
     "note": "Global temperature/precipitation surfaces. The atlas samples the coldest-month "
             "mean temperature for the frost-line map at 10-arc-minute resolution (~18.5 km "
             "cells) — not the 1-km grid named in the paper title. (The published surfaces are "
             "offered down to 30 arc-seconds / ~1 km.)",
     "authors": "Fick SE, Hijmans RJ",
     "year": 2017,
     "title": "WorldClim 2: new 1-km spatial resolution climate surfaces for global land areas",
     "venue": "International Journal of Climatology 37(12):4302–4315",
     "doi": "10.1002/joc.5086",
     "url": "https://www.worldclim.org/"},
    {"id": "usda-zones", "name": "USDA Plant Hardiness Zone Map", "planned": True,
     "role": "hardiness-zone geography", "license": "public domain",
     "note": "Not yet integrated — USDA hardiness zones would drive a grower 'will it grow "
             "where I live?' surface; the atlas currently derives a coldest-month cold edge "
             "from WorldClim instead. A candidate layer, available on request.",
     "authors": "USDA Agricultural Research Service; PRISM Climate Group, Oregon State University",
     "year": 2023,
     "title": "USDA Plant Hardiness Zone Map",
     "venue": "United States Department of Agriculture",
     "doi": None,
     "url": "https://planthardiness.ars.usda.gov/"},
    {"id": "pbdb", "name": "Paleobiology Database (fossil Arecaceae)", "planned": True,
     "role": "deep-time fossil occurrences", "license": "CC-BY 4.0",
     "note": "Not yet integrated — fossil palm occurrences could ground the chronogram's "
             "deep-time axis with fossil calibrations (palms reached high latitudes in the "
             "Eocene). A candidate layer, available on request.",
     "authors": "Paleobiology Database contributors",
     "year": 2024,
     "title": "The Paleobiology Database",
     "venue": "paleobiodb.org",
     "doi": None,
     "url": "https://paleobiodb.org/"},

    # --- Media & descriptions -------------------------------------------------
    {"id": "inaturalist", "name": "iNaturalist",
     "role": "species photos · common names", "license": "CC0 / CC-BY / CC-BY-NC / CC-BY-SA (per image)",
     "note": "A representative Creative-Commons-licensed photograph per species — credited to its "
             "observer, via the public iNaturalist taxa API, with all-rights-reserved images skipped — "
             "plus a common name where the taxon record has one. About a third of palm species carry a "
             "usable CC photo; the rest show a coloured subfamily marker. "
             "NOTE ON LINK ROT: photos are hot-linked from iNaturalist's open-data CDN, not copied or "
             "re-hosted here, so an occasional image can break if its observer removes it or iNaturalist "
             "changes the URL. This keeps attribution with the source and adds no storage, at the cost of "
             "that small permanence risk.",
     "authors": "iNaturalist community",
     "year": 2024,
     "title": "iNaturalist (Arecaceae, taxon 48867)",
     "venue": "iNaturalist.org · open-data CDN",
     "doi": None,
     "url": "https://www.inaturalist.org/taxa/48867-Arecaceae"},
    {"id": "wikipedia", "name": "Wikipedia",
     "role": "species descriptions (fallback)", "license": "CC-BY-SA 4.0",
     "note": "Short descriptive lead extract per species where no primary description is "
             "cached; attributed inline to Wikipedia contributors with the article URL. "
             "Never presented as original text.",
     "authors": "Wikipedia contributors",
     "year": None,
     "title": "Wikipedia species articles (Arecaceae)",
     "venue": "en.wikipedia.org",
     "doi": None,
     "url": "https://en.wikipedia.org/wiki/Arecaceae"},

    # --- The palm world itself ------------------------------------------------
    {"id": "ips-palms", "name": "PALMS — Journal of the International Palm Society",
     "role": "natural-history & expedition content", "license": "© IPS (cited, not rehosted)",
     "note": "The palm community's own literature — new species, delimitation, field "
             "expeditions, conservation — cited for natural-history detail and expedition "
             "narratives. Editors W.J. Baker & S. Zona.",
     "authors": "International Palm Society (eds. Baker WJ, Zona S)",
     "year": 2026,
     "title": "PALMS (formerly Principes), the quarterly journal of the International Palm Society",
     "venue": "International Palm Society",
     "doi": None,
     "url": "https://palms.org/"},
]
