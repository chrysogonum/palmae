"""Fetch real occurrence points from the open GBIF API (no credentials needed).

For the vertical slice we use the occurrence *search* API with a European bounding
box and a per-species cap. The production build swaps this for a GBIF Download
(DOI-citable snapshot) — same shape, fuller coverage.
"""
from __future__ import annotations

import time

import requests

GBIF = "https://api.gbif.org/v1"
# Western Palearctic window (matches the design's European white-oak slice).
LAT_RANGE = "34,72"
LON_RANGE = "-12,40"
_SKIP_BASIS = {"LIVING_SPECIMEN", "MANAGED", "FOSSIL_SPECIMEN"}
_SKIP_ESTABLISHMENT = {"MANAGED", "CULTIVATED", "INTRODUCED"}


def match_taxon_key(name: str) -> int | None:
    r = _get_with_retry(
        f"{GBIF}/species/match",
        {"name": name, "rank": "SPECIES", "kingdom": "Plantae"})
    return r.json().get("usageKey") if r is not None else None


# Genus-wide: worldwide, keep wild records regardless of native/introduced
# (the TDWG range decides native vs introduced); still drop clearly-cultivated.
_SKIP_ESTABLISHMENT_WILD = {"MANAGED", "CULTIVATED"}


def _get_with_retry(url: str, params: dict, tries: int = 4):
    """GET with backoff on rate-limits / transient errors. Returns the Response or
    None if it never succeeded — callers must not treat None as 'no records'."""
    delay = 0.6
    for attempt in range(tries):
        try:
            r = requests.get(url, params=params, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.RequestException(f"status {r.status_code}")
            r.raise_for_status()
            return r
        except requests.RequestException:
            if attempt == tries - 1:
                return None
            time.sleep(delay)
            delay *= 2
    return None


def fetch_global(taxon_key: int, max_records: int = 240) -> list[dict]:
    """Worldwide occurrences for a species — no bounding box, wild records only.

    Retries on GBIF rate-limits so a burst of 429s doesn't silently return an empty
    range for a well-recorded species (the bug that dropped the renegades)."""
    out: list[dict] = []
    offset = 0
    while len(out) < max_records:
        limit = min(300, max_records - len(out))
        r = _get_with_retry(f"{GBIF}/occurrence/search", {
            "taxonKey": taxon_key, "hasCoordinate": "true",
            "hasGeospatialIssue": "false", "limit": limit, "offset": offset,
        })
        if r is None:
            break
        d = r.json()
        results = d.get("results", [])
        if not results:
            break
        for o in results:
            if o.get("basisOfRecord") in _SKIP_BASIS:
                continue
            if (o.get("establishmentMeans") or "").upper() in _SKIP_ESTABLISHMENT_WILD:
                continue
            lat, lon = o.get("decimalLatitude"), o.get("decimalLongitude")
            if lat is None or lon is None:
                continue
            out.append({
                "lon": float(lon), "lat": float(lat),
                "source_record_id": str(o.get("key")),
                "basis_of_record": o.get("basisOfRecord"),
                "event_date": _safe_date(o.get("eventDate")),
                "license": o.get("license"),
                "coordinate_uncertainty_m": o.get("coordinateUncertaintyInMeters"),
                "dataset_key": o.get("datasetKey"),
            })
        offset += len(results)
        if d.get("endOfRecords"):
            break
        time.sleep(0.15)
    return out[:max_records]


def fetch_occurrences(taxon_key: int, max_records: int = 250) -> list[dict]:
    out: list[dict] = []
    offset = 0
    while len(out) < max_records:
        limit = min(300, max_records - len(out))
        r = requests.get(
            f"{GBIF}/occurrence/search",
            params={
                "taxonKey": taxon_key,
                "hasCoordinate": "true",
                "hasGeospatialIssue": "false",
                "decimalLatitude": LAT_RANGE,
                "decimalLongitude": LON_RANGE,
                "limit": limit,
                "offset": offset,
            },
            timeout=60,
        )
        r.raise_for_status()
        d = r.json()
        results = d.get("results", [])
        if not results:
            break
        for o in results:
            if o.get("basisOfRecord") in _SKIP_BASIS:
                continue
            if (o.get("establishmentMeans") or "").upper() in _SKIP_ESTABLISHMENT:
                continue
            lat, lon = o.get("decimalLatitude"), o.get("decimalLongitude")
            if lat is None or lon is None:
                continue
            out.append(
                {
                    "lon": float(lon),
                    "lat": float(lat),
                    "source_record_id": str(o.get("key")),
                    "basis_of_record": o.get("basisOfRecord"),
                    "event_date": _safe_date(o.get("eventDate")),
                    "license": o.get("license"),
                    "coordinate_uncertainty_m": o.get("coordinateUncertaintyInMeters"),
                    "dataset_key": o.get("datasetKey"),
                }
            )
        offset += len(results)
        if d.get("endOfRecords"):
            break
        time.sleep(0.2)
    return out[:max_records]


def _safe_date(raw):
    """Best-effort YYYY-MM-DD from GBIF's varied eventDate strings; else None."""
    if not raw or not isinstance(raw, str) or len(raw) < 10:
        return None
    head = raw[:10]
    parts = head.split("-")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        import datetime as dt
        try:
            return dt.date(int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            return None
    return None
