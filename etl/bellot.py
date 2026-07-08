"""Bellot et al. 2022 (Nature Ecology & Evolution) — predicted extinction risk.

The conservation spine: a threatened / not-threatened status for every species the
study covered, distinguishing a real IUCN assessment from a machine-learning
prediction. This is the PUBLISHED result (high-sensitivity selected model), from the
authors' own openly-licensed workflow (CC-BY-4.0, Zenodo 10.5281/zenodo.6678122;
GitHub sidonieB/palm_extinction_risk_ML) — not a reconstruction.

File columns: accepted_name, IUCN_TS_sum (LC/nonLC for assessed species),
Subset (TRAIN/TEST/ASSESSED = assessed; NOT_ASSESSED = ML-predicted),
Predicted_class (LC/nonLC), Predicted_PnonLC (P of being threatened).
"nonLC" = threatened; "LC" = not threatened.
"""
from __future__ import annotations

import csv
from pathlib import Path

DATA = (Path(__file__).resolve().parents[1] / "data" / "bellot"
        / "Predictions_selected_model_HighSe.txt")

_ASSESSED = {"TRAIN", "TEST", "ASSESSED"}


def records() -> list[dict]:
    out: list[dict] = []
    with DATA.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            name = (row["accepted_name"] or "").strip().replace("_", " ")
            if not name:
                continue
            if row["Subset"] in _ASSESSED:
                status, basis, prob = row["IUCN_TS_sum"], "assessed", None
            else:
                status, basis = row["Predicted_class"], "predicted"
                try:
                    prob = float(row["Predicted_PnonLC"])
                except (ValueError, TypeError, KeyError):
                    prob = None
            if status == "nonLC":
                category = "threatened"
            elif status == "LC":
                category = "not-threatened"
            else:  # NE / NA — no usable status
                continue
            out.append({"name": name, "risk_basis": basis,
                        "predicted_category": category,
                        "prediction_probability": prob})
    return out
