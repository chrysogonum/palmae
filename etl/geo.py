"""Offline reverse geocoding — coordinates to a human place string.

Uses the bundled `reverse_geocoder` dataset (nearest known populated place); no
network calls, no rate limits. Returns "City, Region, Country" (nearest city).
"""
from __future__ import annotations

import reverse_geocoder as rg

# ISO country codes -> readable names for the slice's window (Europe + Mediterranean).
_CC = {
    "GB": "United Kingdom", "IE": "Ireland", "FR": "France", "ES": "Spain", "PT": "Portugal",
    "IT": "Italy", "DE": "Germany", "NL": "Netherlands", "BE": "Belgium", "LU": "Luxembourg",
    "CH": "Switzerland", "AT": "Austria", "DK": "Denmark", "SE": "Sweden", "NO": "Norway",
    "FI": "Finland", "PL": "Poland", "CZ": "Czechia", "SK": "Slovakia", "HU": "Hungary",
    "SI": "Slovenia", "HR": "Croatia", "BA": "Bosnia and Herzegovina", "RS": "Serbia",
    "ME": "Montenegro", "MK": "North Macedonia", "AL": "Albania", "GR": "Greece",
    "BG": "Bulgaria", "RO": "Romania", "MD": "Moldova", "UA": "Ukraine", "TR": "Türkiye",
    "MA": "Morocco", "DZ": "Algeria", "TN": "Tunisia",
}


def _fmt(r: dict) -> str | None:
    city, admin, cc = r.get("name"), r.get("admin1"), r.get("cc")
    country = _CC.get(cc, cc)
    parts = [p for p in (city, admin, country) if p]
    return ", ".join(parts) if parts else None


def place_for(lat: float, lon: float) -> str | None:
    try:
        return _fmt(rg.search([(lat, lon)], mode=1)[0])
    except Exception:  # noqa: BLE001
        return None


def places_for(coords: list[tuple[float, float]]) -> list[str | None]:
    """Batch reverse-geocode many (lat, lon) points in one pass (genus scale)."""
    if not coords:
        return []
    try:
        results = rg.search(coords, mode=1)
    except Exception:  # noqa: BLE001
        return [None] * len(coords)
    return [_fmt(r) for r in results]
