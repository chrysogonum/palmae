"""IUCN Red List conservation status for the oaks (Red List API v4).

We pull the whole Fagaceae family in ~10 paged calls and keep the latest Global
assessment per Quercus species — far lighter than 685 per-species lookups. The
API is behind Cloudflare, which blocks the default urllib User-Agent, so a
browser-like UA is required alongside the Bearer token.
"""
from __future__ import annotations

import json
import time
import urllib.request

from app.config import settings

_BASE = "https://api.iucnredlist.org/api/v4"
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) quercus-etl/1.0"


def available() -> bool:
    return bool(settings.iucn_api_token)


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


def fetch_quercus_assessments() -> dict[str, dict]:
    """Latest assessment per Quercus species: {scientific_name: {category, year, url}}.

    Prefers the Global-scope assessment where a species has several latest rows.
    """
    best: dict[str, dict] = {}
    page = 1
    while True:
        rows = _get(f"/taxa/family/Fagaceae?page={page}").get("assessments", [])
        if not rows:
            break
        for a in rows:
            name = a.get("taxon_scientific_name", "")
            if not name.startswith("Quercus ") or not a.get("latest"):
                continue
            cat = a.get("red_list_category_code")
            if not cat:
                continue
            cand = {
                "category": cat,
                "year": _year(a.get("year_published")),
                "url": a.get("url"),
                "sis_taxon_id": a.get("sis_taxon_id"),
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


def _year(raw) -> int | None:
    try:
        return int(str(raw)[:4])
    except (TypeError, ValueError):
        return None
