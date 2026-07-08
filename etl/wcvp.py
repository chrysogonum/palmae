"""WCVP (World Checklist of Vascular Plants, Kew) taxonomy for the palm family.

WCVP is the name authority for the project. Kew publishes it as a checklist
dataset on GBIF, so we enumerate every accepted palm species and its species-level
synonymy straight from the GBIF species API — no bulk SFTP download. Each synonym
carries an `acceptedKey` pointing at its accepted usage, which is exactly the
reconciliation link the NameAlias table needs.

Family-complete: we filter to the Arecaceae node within the WCVP checklist, so this
covers all ~181 genera at once.
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

WCVP_DATASET = "f382f0ce-323a-4091-bb9f-add557f3a9a2"  # Kew WCVP on GBIF
FAMILY_NODE = 326661320  # "Arecaceae" accepted node within the WCVP checklist
_BASE = "https://api.gbif.org/v1/species/search"
_PAGE = 1000


def _get(params: dict) -> dict:
    url = _BASE + "?" + urllib.parse.urlencode(params)
    last: Exception | None = None
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "palmae-etl"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as ex:  # noqa: BLE001
            last = ex
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"WCVP fetch failed: {url}") from last


def _paginate(status: str) -> list[dict]:
    """All species-rank usages of a taxonomic status under the Arecaceae node."""
    out: list[dict] = []
    offset = 0
    while True:
        page = _get({
            "datasetKey": WCVP_DATASET, "highertaxonKey": FAMILY_NODE,
            "rank": "SPECIES", "status": status, "limit": _PAGE, "offset": offset,
        })
        out.extend(page["results"])
        if page.get("endOfRecords", True):
            break
        offset += _PAGE
    return out


def _is_hybrid(name: str, canonical: str | None) -> bool:
    return "×" in name or "×" in (canonical or "") or " x " in f" {name} "


def fetch_accepted() -> list[dict]:
    """Every accepted palm species. Keyed by GBIF checklist `key`."""
    rows = []
    for r in _paginate("ACCEPTED"):
        canonical = r.get("canonicalName") or r.get("scientificName")
        rows.append({
            "gbif_key": r["key"],
            "wcvp_id": r.get("taxonID"),
            "scientific_name": canonical,           # "Pritchardia martii"
            "full_name": r.get("scientificName"),   # with authorship
            "authorship": r.get("authorship"),
            "genus": r.get("genus"),
            "is_hybrid": _is_hybrid(r.get("scientificName", ""), canonical),
        })
    return rows


def fetch_synonyms() -> list[dict]:
    """Every species-level synonym, linked to its accepted species by acceptedKey."""
    rows = []
    for r in _paginate("SYNONYM"):
        acc = r.get("acceptedKey")
        if acc is None:
            continue
        rows.append({
            "raw_name": r.get("canonicalName") or r.get("scientificName"),
            "authorship": r.get("authorship"),
            "accepted_gbif_key": acc,
        })
    return rows


def fetch_distributions(gbif_key: int) -> list[dict]:
    """TDWG (WGSRPD level-3) native/introduced distribution for one checklist taxon.

    WCVP records distributions per accepted species; GBIF exposes them on the
    checklist usage. This is the authoritative, current range geography — preferred
    over the 2015 PalmTraits snapshot."""
    url = (f"https://api.gbif.org/v1/species/{gbif_key}/distributions"
           "?limit=200")
    last: Exception | None = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "palmae-etl"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            break
        except Exception as ex:  # noqa: BLE001
            last = ex
            time.sleep(1.0 * (attempt + 1))
    else:
        raise RuntimeError(f"distribution fetch failed: {url}") from last

    out = []
    for d in data.get("results", []):
        code = d.get("locationId") or d.get("locality")
        if code and ":" in str(code):  # "TDWG:AND" / "WGSRPD:AND" -> "AND"
            code = str(code).rsplit(":", 1)[1]
        out.append({
            "tdwg_code": code,
            "locality": d.get("locality"),
            "establishment": (d.get("establishmentMeans") or "").lower() or None,
            "status": (d.get("status") or "").lower() or None,
        })
    return out
