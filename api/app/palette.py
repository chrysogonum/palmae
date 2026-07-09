"""Display palette — presentation constants, not source data.

Palms are a family, so the primary categorical encoding is the SUBFAMILY (used
consistently on the tree, the map, and every cross-plot). Conservation risk has its
own scale. Colourblind-aware, encoding-first.
"""
from __future__ import annotations

# The five accepted subfamilies (Genera Palmarum), one stable hue each.
SUBFAMILY_COLOR = {
    "Arecoideae": "#4FB89A",      # teal-green (the large one)
    "Coryphoideae": "#E0A63C",    # amber (fan palms)
    "Calamoideae": "#7F9CD6",     # blue (rattans / scaly-fruited)
    "Ceroxyloideae": "#A98BC0",   # violet
    "Nypoideae": "#C15A4B",       # coral (monotypic Nypa)
}

# Predicted / assessed threat status.
RISK_COLOR = {
    "threatened": "#C1403C",
    "not-threatened": "#6FBF73",
    "not-evaluated": "#9AA0A6",
}
RISK_LABEL = {
    "threatened": "Threatened",
    "not-threatened": "Not threatened",
    "not-evaluated": "Not evaluated",
}

# Formal IUCN categories (shown only for assessed species, as an overlay).
IUCN_COLOR = {
    "LC": "#6FBF73", "NT": "#B5C34A", "VU": "#E0A63C",
    "EN": "#E07B3C", "CR": "#C1403C", "DD": "#9AA0A6",
    "EW": "#4A4A4A", "EX": "#4A4A4A",
    "LR/nt": "#B5C34A", "LR/lc": "#6FBF73", "LR/cd": "#B5C34A",
}
IUCN_LABEL = {
    "LC": "Least Concern", "NT": "Near Threatened", "VU": "Vulnerable",
    "EN": "Endangered", "CR": "Critically Endangered", "DD": "Data Deficient",
    "EW": "Extinct in the Wild", "EX": "Extinct",
    "LR/nt": "Lower Risk (near threatened)", "LR/lc": "Lower Risk (least concern)",
    "LR/cd": "Lower Risk (conservation dependent)",
}

_NEUTRAL = "#8A8E79"


def subfamily_color(subfamily: str | None) -> str:
    return SUBFAMILY_COLOR.get(subfamily or "", _NEUTRAL)


def risk_color(category: str | None) -> str:
    return RISK_COLOR.get(category or "", RISK_COLOR["not-evaluated"])
