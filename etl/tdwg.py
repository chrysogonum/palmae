"""Native range from WCVP's TDWG botanical countries (WGSRPD Level 3).

Two jobs:
  1. `native_regions(wcvp_key)` — the set of TDWG Level-3 codes where WCVP records
     a species as *native* (establishmentMeans not INTRODUCED), from the GBIF-hosted
     WCVP checklist distributions.
  2. `region_of(lon, lat)` — which TDWG Level-3 botanical country a point falls in,
     via the bundled WGSRPD polygons (data/tdwg_level3.geojson).

Together they replace the five hardcoded native-range bounding boxes with a real,
per-species native/introduced split for the whole genus.
"""
from __future__ import annotations

import json
import time
import urllib.request
from functools import lru_cache
from pathlib import Path

from shapely import STRtree
from shapely.geometry import Point, shape

_GEOJSON = Path(__file__).resolve().parent.parent / "data" / "tdwg_level3.geojson"


# WGSRPD Level-1 (continental) region names.
_LEVEL1 = {
    1: "Europe", 2: "Africa", 3: "Asia (temperate)", 4: "Asia (tropical)",
    5: "Australasia", 6: "Pacific", 7: "Northern America", 8: "Southern America",
    9: "Antarctic",
}


class _Regions:
    """Spatial index of the 369 WGSRPD Level-3 polygons for point-in-region lookup."""

    def __init__(self) -> None:
        data = json.loads(_GEOJSON.read_text())
        self.geoms = [shape(f["geometry"]) for f in data["features"]]
        self.codes = [f["properties"]["LEVEL3_COD"] for f in data["features"]]
        self.tree = STRtree(self.geoms)
        # L3 code -> Level-1 continental region name
        self.l1 = {f["properties"]["LEVEL3_COD"]: _LEVEL1.get(f["properties"]["LEVEL1_COD"])
                   for f in data["features"]}

    def code_for(self, lon: float, lat: float) -> str | None:
        pt = Point(lon, lat)
        for i in self.tree.query(pt):  # bbox candidates, then exact test
            if self.geoms[i].covers(pt):
                return self.codes[i]
        return None


_INDEX: _Regions | None = None


def region_of(lon: float, lat: float) -> str | None:
    global _INDEX
    if _INDEX is None:
        _INDEX = _Regions()
    return _INDEX.code_for(lon, lat)


def _get(url: str) -> dict:
    last: Exception | None = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "quercus-etl"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception as ex:  # noqa: BLE001
            last = ex
            time.sleep(1.2 * (attempt + 1))
    raise RuntimeError(f"distributions fetch failed: {url}") from last


def native_label(wcvp_key: int) -> str | None:
    """A readable continental native-range string from the species' TDWG regions,
    e.g. 'Northern America' or 'Europe; Asia (temperate)'."""
    global _INDEX
    if _INDEX is None:
        _INDEX = _Regions()
    codes = native_regions(wcvp_key)
    regions = sorted({_INDEX.l1.get(c) for c in codes if _INDEX.l1.get(c)})
    return "; ".join(regions) if regions else None


@lru_cache(maxsize=2048)
def native_regions(wcvp_key: int) -> frozenset[str]:
    """TDWG Level-3 codes where WCVP records the species as native."""
    url = f"https://api.gbif.org/v1/species/{wcvp_key}/distributions?limit=300"
    recs = _get(url).get("results", [])
    out: set[str] = set()
    for r in recs:
        loc = r.get("locationId") or ""
        if not loc.startswith("TDWG:"):
            continue
        means = (r.get("establishmentMeans") or "").upper()
        if means == "INTRODUCED":
            continue
        out.add(loc.split(":", 1)[1])
    return frozenset(out)
