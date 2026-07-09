"""IUCN Red List conservation status for the palms (Red List API v4).

We pull the whole Arecaceae family in ~19 paged calls and keep the latest Global
assessment per species — far lighter than per-species lookups. The API is behind
Cloudflare, which blocks the default urllib User-Agent, so a browser-like UA is
required alongside the Bearer token.
"""
from __future__ import annotations

import json
import time
import urllib.request

from app.config import settings

_BASE = "https://api.iucnredlist.org/api/v4"
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) palmae-etl/1.0"

# Category → the threatened/not-threatened binary used for the risk colour.
# CR/EN/VU are IUCN "threatened"; EW/EX are worse (not safe); LC/NT/LR-* are not
# threatened; DD (Data Deficient) is a genuine unknown, shown as not-evaluated.
_THREATENED = {"CR", "EN", "VU", "EW", "EX"}
_NOT_THREATENED = {"LC", "NT", "LR/nt", "LR/lc", "LR/cd"}


def available() -> bool:
    return bool(settings.iucn_api_token)


def binary_category(cat: str | None) -> str:
    if cat in _THREATENED:
        return "threatened"
    if cat in _NOT_THREATENED:
        return "not-threatened"
    return "not-evaluated"


def _get(path: str) -> dict:
    url = _BASE + path
    headers = {
        "Authorization": f"Bearer {settings.iucn_api_token}",
        "Accept": "application/json",
        "User-Agent": _UA,
    }
    last: Exception | None = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception as ex:  # noqa: BLE001
            last = ex
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"IUCN fetch failed: {url}") from last


def _is_global(assessment: dict) -> bool:
    return any(s.get("code") == "1" for s in assessment.get("scopes", []))


def _year(raw) -> int | None:
    try:
        return int(str(raw)[:4])
    except (TypeError, ValueError):
        return None


def fetch_family_assessments(family: str = "Arecaceae") -> dict[str, dict]:
    """Latest assessment per species in `family`:
    {scientific_name: {category, year, criteria, url, sis_taxon_id, possibly_extinct}}.

    Prefers the Global-scope assessment where a species has several latest rows.
    """
    best: dict[str, dict] = {}
    page = 1
    while True:
        rows = _get(f"/taxa/family/{family}?page={page}").get("assessments", [])
        if not rows:
            break
        for a in rows:
            name = a.get("taxon_scientific_name", "")
            if not name or not a.get("latest"):
                continue
            cat = a.get("red_list_category_code")
            if not cat:
                continue
            cand = {
                "category": cat,
                "year": _year(a.get("year_published") or a.get("assessment_date")),
                "criteria": a.get("criteria"),
                "url": a.get("url"),
                "sis_taxon_id": a.get("sis_taxon_id"),
                "possibly_extinct": bool(a.get("possibly_extinct")),
                "global": _is_global(a),
            }
            prev = best.get(name)
            # keep the first, but upgrade to a Global-scope assessment if we find one
            if prev is None or (cand["global"] and not prev["global"]):
                best[name] = cand
        if len(rows) < 100:
            break
        page += 1
        time.sleep(0.2)
    return best
