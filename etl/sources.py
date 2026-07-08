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
    {"id": "ipni", "name": "IPNI — International Plant Names Index",
     "role": "nomenclature (names, authors, place of publication)", "license": "CC-BY",
     "note": "Canonical nomenclatural acts; supplies the IPNI ID carried on each taxon.",
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
     "note": "The only complete species-level palm tree (~2,539 tips); species without "
             "molecular data are placed by taxonomic constraint, so those terminal "
             "placements are shown as uncertain. Tree file bundled with PalmTraits 1.0.",
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
    {"id": "paftol", "name": "Baker et al. 2022 — Kew Tree of Life (PAFTOL)",
     "role": "nuclear backbone · dated nodes", "license": "CC-BY 4.0",
     "note": "Angiosperms353 nuclear phylogenomics; used for a defensible higher-level "
             "palm backbone topology and deep-node age ranges (shown as ranges, not points).",
     "authors": "Baker WJ, Bailey P, Barber V, Barker A, Bellot S, Bishop D, et al.",
     "year": 2022,
     "title": "A comprehensive phylogenomic platform for exploring the angiosperm tree of life",
     "venue": "Systematic Biology 71(2):301–319",
     "doi": "10.1093/sysbio/syab035",
     "url": "https://treeoflife.kew.org/"},
    {"id": "zuntini2024", "name": "Zuntini, Baker et al. 2024 — dated angiosperm tree",
     "role": "divergence-time calibration", "license": "CC-BY 4.0",
     "note": "Dated phylogenomic framework used for palm crown/divergence-age ranges.",
     "authors": "Zuntini AR, Carruthers T, Maurin O, Bailey PC, Leempoel K, Brewer GE, et al.",
     "year": 2024,
     "title": "Phylogenomics and the rise of the angiosperms",
     "venue": "Nature 629:843–850",
     "doi": "10.1038/s41586-024-07324-0",
     "url": "https://doi.org/10.1038/s41586-024-07324-0"},

    # --- Occurrences & distribution -------------------------------------------
    {"id": "gbif", "name": "GBIF — Global Biodiversity Information Facility",
     "role": "occurrence points", "license": "CC0 / CC-BY (per record, filtered)",
     "note": "Georeferenced palm records (family taxonKey 7681; ~1.1M georeferenced). "
             "Point evidence for ranges, filtered to CC0/CC-BY; each ingest is a "
             "citable Download DOI. Points are evidence; TDWG regions are authority — "
             "the two are never merged.",
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
     "role": "formal conservation status (assessed subset)", "license": "non-commercial · display-only",
     "note": "Formal Red List category for the ~20% of palms assessed, via the v4 API. "
             "Queried and displayed with attribution; NOT rehosted/redistributed (IUCN "
             "terms). Assessments contributed by the IUCN SSC Palm Specialist Group.",
     "authors": "IUCN; IUCN SSC Palm Specialist Group",
     "year": 2025,
     "title": "The IUCN Red List of Threatened Species",
     "venue": "IUCN Red List API v4",
     "doi": None,
     "url": "https://www.iucnredlist.org/"},
    {"id": "bgci", "name": "BGCI GlobalTreeSearch & PlantSearch",
     "role": "ex-situ holdings (arborescent palms)", "license": "CC-BY-NC 4.0",
     "note": "Living-collection holdings for the tree-form palm subset — the ex-situ "
             "safety-net picture. Rattans/acaulescent palms fall outside the tree definition.",
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
     "note": "Global temperature/precipitation surfaces — coldest-month temperature for "
             "the frost-line map, and CMIP6 projections for the warming/future axis.",
     "authors": "Fick SE, Hijmans RJ",
     "year": 2017,
     "title": "WorldClim 2: new 1-km spatial resolution climate surfaces for global land areas",
     "venue": "International Journal of Climatology 37(12):4302–4315",
     "doi": "10.1002/joc.5086",
     "url": "https://www.worldclim.org/"},
    {"id": "usda-zones", "name": "USDA Plant Hardiness Zone Map",
     "role": "hardiness-zone geography", "license": "public domain",
     "note": "US hardiness-zone geography (2023 revision) for the grower 'will it grow "
             "where I live?' surface; the 2012→2023 shift is the growers' lived warming signal.",
     "authors": "USDA Agricultural Research Service; PRISM Climate Group, Oregon State University",
     "year": 2023,
     "title": "USDA Plant Hardiness Zone Map",
     "venue": "United States Department of Agriculture",
     "doi": None,
     "url": "https://planthardiness.ars.usda.gov/"},
    {"id": "pbdb", "name": "Paleobiology Database (fossil Arecaceae)",
     "role": "deep-time fossil occurrences", "license": "CC-BY 4.0",
     "note": "Fossil palm occurrences for the deep-time axis (palms at high latitudes in "
             "the Eocene). Fossil genus taxonomy is coarse and reconciled manually; may "
             "start as a curated illustrative layer.",
     "authors": "Paleobiology Database contributors",
     "year": 2024,
     "title": "The Paleobiology Database",
     "venue": "paleobiodb.org",
     "doi": None,
     "url": "https://paleobiodb.org/"},

    # --- Media & descriptions -------------------------------------------------
    {"id": "inaturalist", "name": "iNaturalist",
     "role": "CC-licensed species photos (not yet displayed)", "license": "CC0 / CC-BY / CC-BY-NC (per image)",
     "note": "The intended source for a representative Creative-Commons-licensed photograph per species — "
             "credited to its observer, via the public iNaturalist taxa API, with all-rights-reserved "
             "images skipped. Not yet integrated: the app currently shows no photographs.",
     "authors": "iNaturalist community",
     "year": 2024,
     "title": "iNaturalist (Arecaceae, taxon 48867)",
     "venue": "iNaturalist.org",
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
