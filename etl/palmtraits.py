"""PalmTraits 1.0 (Kissling et al. 2019, CC0) — traits + the genus-level
classification (tribe, subfamily) that WCVP does not carry.

Parses the tab-delimited `PalmTraits_1.0.txt` (2,557 species). Two products:
- `classification()` — genus -> {tribe, subfamily} (from the World Checklist of
  Palms / Genera Palmarum), to place every WCVP species into its subfamily/tribe.
- `species_traits()` — per-species trait records for the EAV `trait` table.

Note: PalmTraits 1.0 has NO leaf-architecture field (pinnate/palmate/costapalmate);
that 'fan vs feather' distinction must come from another source (Genera Palmarum),
so it is deliberately absent here rather than fabricated.
"""
from __future__ import annotations

import csv
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "palmtraits" / "PalmTraits_1.0.txt"

# PalmTraits column -> (trait_name, unit)
_NUMERIC = {
    "MaxStemHeight_m": ("max_stem_height", "m"),
    "MaxStemDia_cm": ("max_stem_diameter", "cm"),
    "MaxLeafNumber": ("max_leaf_number", None),
    "Max_Blade_Length_m": ("max_blade_length", "m"),
    "Max_Rachis_Length_m": ("max_rachis_length", "m"),
    "Max_Petiole_length_m": ("max_petiole_length", "m"),
    "AverageFruitLength_cm": ("avg_fruit_length", "cm"),
    "MaxFruitLength_cm": ("max_fruit_length", "cm"),
    "AverageFruitWidth_cm": ("avg_fruit_width", "cm"),
    "MaxFruitWidth_cm": ("max_fruit_width", "cm"),
}
# Binary 1/0 columns -> trait_name (value_cat = yes/no)
_BINARY = {
    "Climbing": "climbing",
    "Acaulescent": "acaulescent",
    "Erect": "erect",
    "StemSolitary": "stem_solitary",
    "StemArmed": "stem_armed",
    "LeavesArmed": "leaves_armed",
}
# Categorical columns -> trait_name
_CATEGORICAL = {
    "UnderstoreyCanopy": "strata",
    "FruitSizeCategorical": "fruit_size_class",
    "FruitShape": "fruit_shape",
    "MainFruitColors": "fruit_color",
    "Conspicuousness": "fruit_conspicuousness",
}


def _rows() -> list[dict]:
    # The file is Latin-1 (stray 0xa0 non-breaking spaces), not pure UTF-8.
    with DATA.open(encoding="latin-1", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _clean(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return None if v in ("", "NA", "na", "NaN") else v


def classification() -> dict[str, dict]:
    """genus -> {'tribe':..., 'subfamily':...} from PalmTraits."""
    out: dict[str, dict] = {}
    for r in _rows():
        g = _clean(r.get("accGenus"))
        if not g or g in out:
            continue
        out[g] = {
            "tribe": _clean(r.get("PalmTribe")),
            "subfamily": _clean(r.get("PalmSubfamily")),
        }
    return out


def species_traits() -> list[dict]:
    """Per-species: {'name': binomial, 'genus':..., 'traits': [ {...}, ... ]}."""
    records = []
    for r in _rows():
        name = _clean(r.get("SpecName"))
        if not name:
            continue
        name = name.replace("_", " ")
        traits: list[dict] = []

        for col, (tname, unit) in _NUMERIC.items():
            val = _clean(r.get(col))
            if val is None:
                continue
            try:
                traits.append({"trait_name": tname, "value_num": float(val),
                               "value_cat": None, "unit": unit})
            except ValueError:
                continue

        for col, tname in _BINARY.items():
            val = _clean(r.get(col))
            if val is None:
                continue
            traits.append({"trait_name": tname,
                           "value_num": None,
                           "value_cat": "yes" if val in ("1", "1.0") else "no",
                           "unit": None})

        for col, tname in _CATEGORICAL.items():
            val = _clean(r.get(col))
            if val is None:
                continue
            traits.append({"trait_name": tname, "value_num": None,
                           "value_cat": val, "unit": None})

        records.append({"name": name, "genus": _clean(r.get("accGenus")),
                        "traits": traits})
    return records
