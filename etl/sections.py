"""Infrageneric placement for Quercus — each species' subgenus + section.

Source: the Hipp et al. global-oaks classification (Denk, Grimm, Manos, Deng & Hipp
2017, "An updated infrageneric classification of the oaks"), as distributed with the
global oak phylogeny project (github.com/andrew-hipp/global-oaks-2019,
`OaksofWorldSpeciesSampledNotsampled.xlsx`) — the same project our phylogeny came from.
Bundled here as data/oak_sections.csv: 263 Quercus species across the two subgenera
(Quercus = New-World clade, Cerris = Old-World clade) and eight sections.
"""
from __future__ import annotations

import csv
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "oak_sections.csv"


def read_sections() -> list[dict]:
    rows: list[dict] = []
    with DATA.open() as f:
        for r in csv.DictReader(f):
            sec = (r.get("section") or "").strip()
            if not sec:
                continue
            rows.append({
                "name": r["name"].strip(),
                "subgenus": (r.get("subgenus") or "").strip() or None,
                "section": sec,
            })
    return rows
