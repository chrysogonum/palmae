"""Fetch a representative, CC-licensed photo per species from the open iNaturalist API.

Uses the public taxa endpoint (no token required). Only Creative-Commons-licensed
default photos are accepted; all-rights-reserved photos are skipped. Attribution and
license are stored and surfaced in the UI.
"""
from __future__ import annotations

import datetime as dt
import re
import time

import requests

INAT = "https://api.inaturalist.org/v1"
_HEADERS = {"User-Agent": "Palmae-Atlas/1.0 (educational, non-commercial)"}
# Creative Commons license codes we may display (non-commercial project).
_CC_OK = {"cc0", "cc-by", "cc-by-nc", "cc-by-sa", "cc-by-nc-sa", "cc-by-nd", "cc-by-nc-nd"}
_TAG = re.compile(r"<[^>]+>")


def _blurb(summary: str | None) -> str | None:
    """Plain-text, ~2-sentence lead from an iNaturalist wikipedia_summary."""
    if not summary:
        return None
    text = _TAG.sub("", summary).strip()
    if len(text) > 340:
        cut = text[:340]
        dot = cut.rfind(". ")
        text = (cut[: dot + 1] if dot > 120 else cut).rstrip() + " …"
    return text or None


def fetch_taxon(scientific_name: str) -> dict | None:
    """One iNaturalist lookup → photo (CC only), common name, Wikipedia blurb,
    observation count, and the iNat taxon id. Returns None if the name doesn't match."""
    r = requests.get(
        f"{INAT}/taxa",
        params={"q": scientific_name, "rank": "species", "per_page": 5},
        headers=_HEADERS, timeout=30,
    )
    r.raise_for_status()
    for t in r.json().get("results", []):
        if (t.get("name") or "").lower() != scientific_name.lower():
            continue
        dp = t.get("default_photo") or {}
        lic = (dp.get("license_code") or "").lower()
        photo = None
        if lic in _CC_OK and (dp.get("medium_url") or dp.get("url")):
            photo = {"url": dp.get("medium_url") or dp.get("url"),
                     "attribution": dp.get("attribution"), "license": lic.upper()}
        return {
            "photo": photo,
            "common_name": t.get("preferred_common_name"),
            "blurb": _blurb(t.get("wikipedia_summary")),
            "obs_count": t.get("observations_count"),
            "wikipedia_url": t.get("wikipedia_url"),
            "inat_taxon_id": t.get("id"),
        }
    return None


_CC_LICENSES = "cc0,cc-by,cc-by-nc,cc-by-sa,cc-by-nc-sa,cc-by-nd,cc-by-nc-nd"


def _obs_media(scientific_name: str) -> dict | None:
    """Best research-grade CC-photo observation for a species → its photo + the URL
    of that observation on iNaturalist."""
    r = requests.get(f"{INAT}/observations", params={
        "taxon_name": scientific_name, "quality_grade": "research", "photos": "true",
        "photo_license": _CC_LICENSES, "order_by": "votes", "order": "desc", "per_page": 5,
    }, headers=_HEADERS, timeout=30)
    r.raise_for_status()
    for o in r.json().get("results", []):
        for ph in (o.get("photos") or []):
            lic = (ph.get("license_code") or "").lower()
            url = ph.get("url")
            if lic in _CC_OK and url:
                return {
                    "url": url.replace("square", "medium"),
                    "attribution": ph.get("attribution"), "license": lic.upper(),
                    "source_url": f"https://www.inaturalist.org/observations/{o.get('id')}",
                    "common_name": (o.get("taxon") or {}).get("preferred_common_name"),
                }
    return None


def fetch_media(scientific_name: str) -> dict | None:
    """A CC photo + where it lives on iNaturalist, + common name. Prefers a research-
    grade observation photo (linked to that observation); falls back to the taxon's
    curated default photo (linked to the taxon page). Returns None on no name match."""
    try:
        m = _obs_media(scientific_name)
    except requests.RequestException:
        m = None
    if m:
        return m
    t = fetch_taxon(scientific_name)  # fallback: taxon default photo + common name
    if not t:
        return None
    p = t.get("photo")
    if p:
        return {"url": p["url"], "attribution": p["attribution"], "license": p["license"],
                "source_url": f"https://www.inaturalist.org/taxa/{t.get('inat_taxon_id')}",
                "common_name": t.get("common_name")}
    return {"url": None, "attribution": None, "license": None, "source_url": None,
            "common_name": t.get("common_name")}


def fetch_summaries(ids: list[int]) -> dict[int, dict]:
    """Wikipedia blurb + source article URL for many iNat taxon ids, batched 30 at a
    time (detail endpoint). Keyed by iNat id: {id: {"blurb": str, "url": str|None}}."""
    out: dict[int, dict] = {}
    uniq = [i for i in dict.fromkeys(ids) if i]
    for i in range(0, len(uniq), 30):
        chunk = uniq[i:i + 30]
        try:
            r = requests.get(f"{INAT}/taxa/" + ",".join(map(str, chunk)),
                             headers=_HEADERS, timeout=40)
            r.raise_for_status()
        except requests.RequestException:
            continue
        for t in r.json().get("results", []):
            b = _blurb(t.get("wikipedia_summary"))
            if b:
                url = t.get("wikipedia_url")
                out[t["id"]] = {"blurb": b, "url": url.replace(" ", "_") if url else None}
        time.sleep(0.4)
    return out


def fetch_taxon_photo(scientific_name: str) -> dict | None:
    r = requests.get(
        f"{INAT}/taxa",
        params={"q": scientific_name, "rank": "species", "per_page": 5},
        headers=_HEADERS, timeout=30,
    )
    r.raise_for_status()
    for t in r.json().get("results", []):
        if (t.get("name") or "").lower() != scientific_name.lower():
            continue
        dp = t.get("default_photo") or {}
        lic = (dp.get("license_code") or "").lower()
        if lic not in _CC_OK:
            return None  # taxon matched but its default photo is all-rights-reserved
        url = dp.get("medium_url") or dp.get("url")
        if not url:
            return None
        return {
            "url": url,
            "attribution": dp.get("attribution"),
            "license": lic.upper(),
            "inat_taxon_id": t.get("id"),
        }
    return None


def fetch_observations(scientific_name: str, limit: int = 150) -> list[dict]:
    """Research-grade, publicly-georeferenced iNaturalist observations for a species."""
    r = requests.get(
        f"{INAT}/observations",
        params={
            "taxon_name": scientific_name, "quality_grade": "research", "geo": "true",
            "per_page": min(200, limit), "order_by": "observed_on", "order": "desc",
        },
        headers=_HEADERS, timeout=40,
    )
    r.raise_for_status()
    out: list[dict] = []
    for o in r.json().get("results", []):
        if o.get("obscured") or o.get("geoprivacy"):
            continue
        geo = o.get("geojson") or {}
        if geo.get("type") != "Point":
            continue
        lon, lat = geo["coordinates"]
        out.append({
            "lon": float(lon), "lat": float(lat),
            "source_record_id": str(o.get("id")),
            "event_date": _obs_date(o.get("observed_on")),
            "license": (o.get("license_code") or "").upper() or None,
        })
        if len(out) >= limit:
            break
    return out


def _obs_date(s):
    if not s or len(s) < 10:
        return None
    try:
        return dt.date.fromisoformat(s[:10])
    except ValueError:
        return None
