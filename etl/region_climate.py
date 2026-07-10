"""Per-TDWG-region climate summary — mean annual rainfall and coldest-month mean
temperature (CMMT) — for the World Atlas rainfall layer and the richness×rainfall
anomaly view (CMMT lets us control for 'too cold for palms' vs 'genuinely palm-poor').

Zonal means over WGSRPD level-3 polygons:
  - rain: WorldClim 2.1 bio_12 (annual precipitation, mm)
  - cmmt: per-pixel min of the 12 monthly tavg rasters (coldest-month mean, °C) —
          the same frost-line variable the Palm Line uses (Reichgelt et al. 2018)

Static reference data (raster × geometry, both fixed) → data/region_climate.json.

Run:  PYTHONPATH=api .venv/bin/python -m etl.region_climate
"""
from __future__ import annotations

import glob
import json
import pathlib

import numpy as np
import rasterio
import rasterio.mask
from rasterio.io import MemoryFile
from shapely.geometry import shape

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_WC = _ROOT / "data" / "worldclim"
_GEO = _ROOT / "data" / "tdwg_level3.geojson"
_OUT = _ROOT / "data" / "region_climate.json"
_NODATA = -1e30


def _zonal_mean(src, geom) -> float | None:
    try:
        arr, _ = rasterio.mask.mask(src, [geom], crop=True, all_touched=True)
    except Exception:  # noqa: BLE001
        return None
    a = arr[0].astype("float64")
    if src.nodata is not None:
        a[a == src.nodata] = np.nan
    a[a < -1e10] = np.nan
    v = a[~np.isnan(a)]
    return float(v.mean()) if v.size else None


def compute() -> dict[str, dict]:
    geo = json.loads(_GEO.read_text())

    # Build the CMMT raster in memory: per-pixel minimum across the 12 tavg months.
    tavg = sorted(glob.glob(str(_WC / "wc2.1_10m_tavg_*.tif")))
    if len(tavg) != 12:
        raise FileNotFoundError(f"expected 12 tavg rasters in {_WC}, found {len(tavg)}")
    with rasterio.open(tavg[0]) as s0:
        profile = s0.profile.copy()
    stack = []
    for p in tavg:
        with rasterio.open(p) as s:
            b = s.read(1).astype("float64")
            b[b <= _NODATA] = np.nan
            b[b < -1e10] = np.nan
            stack.append(b)
    cmmt = np.nanmin(np.where(np.isnan(stack), np.inf, np.stack(stack)), axis=0)
    cmmt[np.isinf(cmmt)] = np.nan
    profile.update(dtype="float32", nodata=float("nan"), count=1)

    out: dict[str, dict] = {}
    with rasterio.open(_WC / "wc2.1_10m_bio_12.tif") as rain_src, MemoryFile() as mem:
        with mem.open(**profile) as w:
            w.write(cmmt.astype("float32"), 1)
        with mem.open() as cmmt_src:
            for f in geo["features"]:
                code = f["properties"]["LEVEL3_COD"]
                geom = f["geometry"]
                entry: dict = {}
                r = _zonal_mean(rain_src, geom)
                t = _zonal_mean(cmmt_src, geom)
                if r is not None:
                    entry["rain"] = int(round(r))
                if t is not None:
                    entry["cmmt"] = round(t, 1)
                try:  # rough polygon area (sq degrees) — used to drop tiny isolated islands
                    entry["area"] = round(shape(geom).area, 2)
                except Exception:  # noqa: BLE001
                    pass
                if entry:
                    out[code] = entry
    _OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"  climate: {len(out)} regions written to {_OUT.name} (rain + cmmt)")
    return out


if __name__ == "__main__":
    compute()
