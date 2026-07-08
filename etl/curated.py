"""Curated, cited facts for the five-species vertical slice.

For the slice we ingest *real* GBIF occurrences live (see gbif.py), and seed the
remaining fields from authoritative sources: WCVP/POWO (names, authorship,
synonymy), Denk/Grimm/Manos/Deng/Hipp 2017 (infrageneric placement), the Red
List of Oaks 2020 (conservation), Kew C-values / CCDB / Global Wood Density
(traits), Hipp et al. 2020 (phylogeny topology), and Petit et al. (chloroplast
lineages by geography). Figures that are approximate or single-source are marked
`[as-reported]` in the `note`/provenance so the UI can surface the caveat.

Full-authority bulk ingestion (WCVP dump, GBIF Download DOI, the complete Hipp
tree, TRY/BIEN traits, GloBI interactions) is the scaling phase, not the slice.
"""
from __future__ import annotations

# --- the five species (accepted names, authorship, placement, traits) ---------
# All are subgenus Quercus, section Quercus (the white oaks s.s.).
SPECIES = [
    {
        "slug": "robur",
        "scientific_name": "Quercus robur",
        "authorship": "L.",
        "common_name": "Pedunculate oak",
        "subgenus": "Quercus",
        "section": "Quercus",
        "gbif_name": "Quercus robur",
        "region": "Europe to the Caucasus",
        "leaf_habit": "deciduous",
        "acorn_maturation": "1-year",
        "chromosome_2n": 24,
        "genome_size": "~0.72–0.90 Gb",
        "wood_density": 0.65,      # g/cm3, Global Wood Density DB [as-reported]
        "drought_tolerance": 0.35,  # 0–1 relative [as-reported]
        "hybridizes": True,
        "iucn": "LC",
        "blurb": "The archetypal European oak: long-lived, wind-pollinated, its "
                 "acorns borne on long stalks (peduncles). A foundation tree of "
                 "lowland deciduous forest across the continent.",
        "synonyms": [
            ("Quercus pedunculata", "Ehrh.", "synonym"),
            ("Quercus robur subsp. robur", "L.", "synonym"),
        ],
    },
    {
        "slug": "petraea",
        "scientific_name": "Quercus petraea",
        "authorship": "(Matt.) Liebl.",
        "common_name": "Sessile oak",
        "subgenus": "Quercus",
        "section": "Quercus",
        "gbif_name": "Quercus petraea",
        "region": "Europe and Anatolia",
        "leaf_habit": "deciduous",
        "acorn_maturation": "1-year",
        "chromosome_2n": 24,
        "genome_size": "~0.72–0.90 Gb",
        "wood_density": 0.67,
        "drought_tolerance": 0.45,
        "hybridizes": True,
        "iucn": "LC",
        "blurb": "Close sister to the pedunculate oak, with stalkless (sessile) "
                 "acorns and a preference for slopes and better-drained soils. "
                 "The two hybridize freely where they meet.",
        "synonyms": [
            ("Quercus sessiliflora", "Salisb.", "synonym"),
            ("Quercus sessilis", "Ehrh.", "synonym"),
        ],
    },
    {
        "slug": "pubescens",
        "scientific_name": "Quercus pubescens",
        "authorship": "Willd.",
        "common_name": "Downy oak",
        "subgenus": "Quercus",
        "section": "Quercus",
        "gbif_name": "Quercus pubescens",
        "region": "Southern and central Europe (sub-Mediterranean)",
        "leaf_habit": "deciduous",
        "acorn_maturation": "1-year",
        "chromosome_2n": 24,
        "genome_size": "~0.80–0.95 Gb",
        "wood_density": 0.80,
        "drought_tolerance": 0.70,
        "hybridizes": True,
        "iucn": "LC",
        "blurb": "A drought-hardy oak of warm, dry hillsides, named for the soft "
                 "down on its young leaves and shoots. Anchors sub-Mediterranean "
                 "woodland from Iberia to the Balkans.",
        "synonyms": [
            ("Quercus lanuginosa", "(Lam.) Thuill.", "synonym"),
            ("Quercus humilis", "Mill.", "synonym"),
        ],
    },
    {
        "slug": "faginea",
        "scientific_name": "Quercus faginea",
        "authorship": "Lam.",
        "common_name": "Portuguese oak",
        "subgenus": "Quercus",
        "section": "Quercus",
        "gbif_name": "Quercus faginea",
        "region": "Iberian Peninsula and NW Africa",
        "leaf_habit": "semi-evergreen",
        "acorn_maturation": "1-year",
        "chromosome_2n": 24,
        "genome_size": "~0.80–0.95 Gb",
        "wood_density": 0.82,
        "drought_tolerance": 0.75,
        "hybridizes": True,
        "iucn": "LC",
        "blurb": "An Iberian near-endemic with marcescent, half-evergreen leaves "
                 "that persist through winter. Its narrow range makes it a useful "
                 "test of how geography, not species, patterns the chloroplast.",
        "synonyms": [
            ("Quercus valentina", "Cav.", "synonym"),
            ("Quercus lusitanica", "auct. non Lam.", "misapplied"),
        ],
    },
    {
        "slug": "frainetto",
        "scientific_name": "Quercus frainetto",
        "authorship": "Ten.",
        "common_name": "Hungarian oak",
        "subgenus": "Quercus",
        "section": "Quercus",
        "gbif_name": "Quercus frainetto",
        "region": "Southeastern Europe, the Balkans, southern Italy",
        "leaf_habit": "deciduous",
        "acorn_maturation": "1-year",
        "chromosome_2n": 24,
        "genome_size": "~0.80–0.95 Gb",
        "wood_density": 0.72,
        "drought_tolerance": 0.55,
        "hybridizes": True,
        "iucn": "LC",
        "blurb": "A large-leaved oak of the Balkan and south Italian lowlands, "
                 "carrying the eastern (Balkan) chloroplast lineage. Named for its "
                 "deeply lobed foliage.",
        "synonyms": [
            ("Quercus conferta", "Kit.", "synonym"),
            ("Quercus farnetto", "Ten.", "synonym"),
        ],
    },
]

# --- native-range bounding boxes (lon_min, lon_max, lat_min, lat_max) ----------
# GBIF includes cultivated/planted trees outside the native range (establishment
# means is usually blank, so it can't be filtered on). We clip occurrences to the
# expert native range — the "distinguish native from introduced using the range
# authority, not the points" principle. Coarse boxes for the slice; production
# uses IUCN/WCVP native-range polygons.
NATIVE_BBOX = {
    "robur":     (-10.0, 45.0, 36.0, 64.0),  # Europe to the Caucasus, incl. S Scandinavia
    "petraea":   (-10.0, 45.0, 36.0, 61.0),  # Europe and Anatolia
    "pubescens": (-3.0, 46.0, 35.0, 51.0),   # S/C Europe (sub-Mediterranean) to Caucasus
    "faginea":   (-10.0, 6.0, 30.0, 44.0),   # Iberian Peninsula and NW Africa
    "frainetto": (11.0, 30.0, 37.0, 48.0),   # SE Europe, Balkans, S Italy
}


def in_native_range(slug: str, lon: float, lat: float) -> bool:
    box = NATIVE_BBOX.get(slug)
    if not box:
        return True
    lon_min, lon_max, lat_min, lat_max = box
    return lon_min <= lon <= lon_max and lat_min <= lat <= lat_max


# --- chloroplast lineages (Petit et al. lineage-by-geography) ------------------
# Assignment to an occurrence is by geography (longitude/latitude bands), a
# documented approximation of the refugial structure — flagged [as-reported].
HAPLOTYPE_LINEAGES = [
    {"code": "iberian", "label": "Iberian lineage (A/B)", "color": "#E06B4A", "refugium_lon": -4.0, "refugium_lat": 40.0},
    {"code": "italian", "label": "Italian lineage (C)",   "color": "#C6A2E0", "refugium_lon": 13.0, "refugium_lat": 42.0},
    {"code": "balkan",  "label": "Balkan lineage (E)",    "color": "#6FD08A", "refugium_lon": 22.0, "refugium_lat": 42.0},
]


def haplotype_for(lon: float, lat: float) -> str:
    """Documented lineage-by-geography approximation (Petit et al.) [as-reported].

    West (Iberia/Atlantic) -> Iberian; central (Italy/Alps) -> Italian;
    east (Balkans/Carpathians) -> Balkan. Crude longitude bands, honest about it.
    """
    if lon < 3.0:
        return "iberian"
    if lon < 16.0:
        return "italian"
    return "balkan"


# --- phylogeny (section Quercus topology, after Hipp et al. 2020) --------------
# Schematic tips + one conflicted/hybridizing node, carrying representative
# support values [as-reported]. Full 632-tip tree ingest is the scaling phase.
TREE_META = {
    "citation_doi": "10.1111/nph.16162",
    "method": "RAD-seq phylogenomics (topology after Hipp et al. 2020)",
    "source_url": "https://github.com/andrew-hipp/global-oaks-2019",
}
# nodes: (key, parent_key, kind, name, support, conflict, note, species_slug)
TREE_NODES = [
    ("sect", None, "section", "sect. Quercus", None, False, "white oaks s.s.", None),
    ("clade1", "sect", "clade", "clade1", 71, True, "gene trees disagree — hybridization", None),
    ("robur", "clade1", "tip", "Quercus robur", 98, False, None, "robur"),
    ("petraea", "clade1", "tip", "Quercus petraea", 98, False, None, "petraea"),
    ("pubescens", "sect", "tip", "Quercus pubescens", 85, False, None, "pubescens"),
    ("ff", "sect", "clade", "clade2", 79, False, None, None),
    ("faginea", "ff", "tip", "Quercus faginea", 82, False, None, "faginea"),
    ("frainetto", "ff", "tip", "Quercus frainetto", 80, False, None, "frainetto"),
]

# --- syngameon gene-flow edges (Lens B), after Cannon & Petit 2020 [as-reported]
# (species_a_slug, species_b_slug, weight 0–1 = relative introgression rate)
SYNGAMEON_EDGES = [
    ("robur", "petraea", 0.9),
    ("petraea", "pubescens", 0.6),
    ("robur", "frainetto", 0.35),
    ("pubescens", "faginea", 0.5),
    ("pubescens", "frainetto", 0.45),
    ("petraea", "faginea", 0.3),
    ("robur", "pubescens", 0.4),
]

# --- realized climate envelope per species (Lens A) [as-reported] -------------
# [mean annual temperature °C, annual precipitation mm], representative centroids.
CLIMATE = {
    "robur": [9.0, 780],
    "petraea": [9.5, 820],
    "pubescens": [12.5, 680],
    "faginea": [13.5, 640],
    "frainetto": [12.0, 720],
}

# --- keystone food-web bands (Lens C) for the focal oak, Q. robur -------------
# Representative counts [as-reported] (Narango/Tallamy; GloBI/HOSTS/FungalRoot);
# real GloBI ingestion is the scaling phase.
KEYSTONE_BANDS = {
    "robur": [
        {"band": "Lepidoptera", "count": 60, "specialist_fraction": 0.35},
        {"band": "Gall wasps", "count": 34, "specialist_fraction": 0.80},
        {"band": "Ectomycorrhizal fungi", "count": 28, "specialist_fraction": 0.20},
        {"band": "Acorn consumers", "count": 12, "specialist_fraction": 0.15},
    ],
}

# --- provenance registry (Sources panel + per-field attribution) --------------
# Full citations are verified against the primary literature; DOIs/URLs are the
# canonical record. Composite sources (traits, interactions) list the primary
# databases in `authors`/`note` and leave `doi` null (no single identifier).
DATA_SOURCES = [
    {"id": "wcvp", "name": "WCVP — World Checklist of Vascular Plants (Kew)",
     "role": "name authority · IPNI LSID key", "license": "CC-BY",
     "note": "Accepted names and synonymy; every record resolves through a NameAlias table.",
     "authors": "Govaerts R, Nic Lughadha E, Black N, Turner R, Paton A",
     "year": 2021, "title": "The World Checklist of Vascular Plants, a continuously updated resource for exploring global plant diversity",
     "venue": "Scientific Data 8:215", "doi": "10.1038/s41597-021-00997-6",
     "url": "https://powo.science.kew.org/"},
    {"id": "gbif", "name": "GBIF — Global Biodiversity Information Facility",
     "role": "occurrence points", "license": "CC0 / CC-BY",
     "note": "Point evidence for ranges (live occurrence search for the slice; production uses a Download DOI snapshot).",
     "authors": "GBIF Secretariat", "year": 2024,
     "title": "GBIF Occurrence Data (Quercus)", "venue": "GBIF.org",
     "doi": None, "url": "https://www.gbif.org/"},
    {"id": "hipp2020", "name": "Hipp et al. 2020, New Phytologist",
     "role": "phylogenomic backbone", "license": "CC-BY",
     "note": "RAD-seq global oak tree; slice uses the section Quercus topology [as-reported].",
     "authors": "Hipp AL, Manos PS, Hahn M, Avishai M, Bodénès C, Cavender-Bares J, et al.",
     "year": 2020, "title": "Genomic landscape of the global oak phylogeny",
     "venue": "New Phytologist 226(4):1198–1212", "doi": "10.1111/nph.16162",
     "url": "https://doi.org/10.1111/nph.16162"},
    {"id": "petit", "name": "Petit et al. 2002 — white-oak cpDNA",
     "role": "chloroplast lineages", "license": "published dataset",
     "note": "Lineage-by-geography (Iberian/Italian/Balkan refugia); slice assigns by geography [as-reported].",
     "authors": "Petit RJ, Csaikl UM, Bordács S, Burg K, Coart E, et al.",
     "year": 2002, "title": "Chloroplast DNA variation in European white oaks: phylogeography and patterns of diversity based on data from over 2600 populations",
     "venue": "Forest Ecology and Management 156:5–26", "doi": "10.1016/S0378-1127(01)00645-4",
     "url": "https://doi.org/10.1016/S0378-1127(01)00645-4"},
    {"id": "redlist-oaks", "name": "IUCN Red List of Threatened Species (Quercus)",
     "role": "conservation status", "license": "non-commercial",
     "note": "Live Red List category per species via the IUCN Red List API v4 "
             "(421 of 685 Quercus assessed); underlying assessments from the Red List "
             "of Oaks 2020 (Carrero et al.). ~31% of oaks are threatened.",
     "authors": "IUCN; Carrero C, Jerome D, Beckman E, et al. (Red List of Oaks 2020)",
     "year": 2020, "title": "The IUCN Red List of Threatened Species / The Red List of Oaks 2020",
     "venue": "IUCN Red List API v4 · The Morton Arboretum, Lisle, IL", "doi": None,
     "url": "https://www.iucnredlist.org/"},
    {"id": "traits", "name": "Kew C-values · CCDB · Global Wood Density",
     "role": "traits", "license": "CC-BY / CC0",
     "note": "Genome size, chromosome number, wood density [as-reported]. Composite of three primary databases.",
     "authors": "Pellicer & Leitch (Plant DNA C-values); Rice et al. (CCDB); Zanne et al. (Global Wood Density)",
     "year": None, "title": "Composite trait databases",
     "venue": "Kew · New Phytologist · Dryad", "doi": None,
     "url": "https://cvalues.science.kew.org/"},
    {"id": "inaturalist", "name": "iNaturalist",
     "role": "photos · common names · observations", "license": "CC (per record)",
     "note": "Default CC-licensed species photo, preferred common name, and observation "
             "count per species, via the public iNaturalist API; photos credited to their "
             "observers inline.",
     "authors": "iNaturalist community", "year": 2024,
     "title": "iNaturalist Research-grade Observations (Quercus)", "venue": "iNaturalist.org",
     "doi": None, "url": "https://www.inaturalist.org/"},
    {"id": "wikipedia", "name": "Wikipedia",
     "role": "species descriptions", "license": "CC-BY-SA",
     "note": "Short descriptive blurb per species (lead extract), retrieved through the "
             "iNaturalist taxon API; text is CC-BY-SA and attributable to Wikipedia contributors.",
     "authors": "Wikipedia contributors", "year": None,
     "title": "Wikipedia species articles (Quercus)", "venue": "en.wikipedia.org",
     "doi": None, "url": "https://en.wikipedia.org/wiki/Quercus"},
    {"id": "gift", "name": "GIFT — Global Inventory of Floras and Traits",
     "role": "leaf habit · growth form", "license": "CC-BY 4.0",
     "note": "Leaf habit (deciduous/evergreen) per species, aggregated from regional "
             "Floras with reference counts; retrieved via the GIFT REST API (trait "
             "Deciduousness 2.4.1). Backfilled from Wikipedia where GIFT is silent.",
     "authors": "Weigelt P, König C, Kreft H",
     "year": 2020, "title": "GIFT – A Global Inventory of Floras and Traits for macroecology and biogeography",
     "venue": "Journal of Biogeography 47(1):16–43", "doi": "10.1111/jbi.13623",
     "url": "https://gift.uni-goettingen.de/"},
    {"id": "globi", "name": "GloBI · HOSTS · FungalRoot",
     "role": "ecological interactions", "license": "CC0 / mixed",
     "note": "Keystone food-web (Lens C); slice seeds representative counts [as-reported].",
     "authors": "Poelen JH, Simons JD, Mungall CJ (GloBI)",
     "year": 2014, "title": "Global Biotic Interactions: an open infrastructure to share and analyze species-interaction datasets",
     "venue": "Ecological Informatics 24:148–159", "doi": "10.1016/j.ecoinf.2014.08.005",
     "url": "https://www.globalbioticinteractions.org/"},
]

CONSERVATION_SOURCE = "IUCN Red List of Oaks 2020"
