"""WorldClim 2.1 — coldest-month mean temperature (CMMT) sampler.

The palm-line reveal turns on CMMT: the mean temperature of the coldest month of
the year. That is the variable the paleoclimate calibration is stated in (Reichgelt,
West & Greenwood 2018 — palms indicate CMMT >= ~2-8 C, the frost line), so it is the
variable we must sample, not a proxy.

WorldClim publishes monthly `tavg` (long-term average temperature per calendar
month) as twelve GeoTIFFs. CMMT at a point = the minimum across those twelve monthly
means. That is exactly the coldest-month mean, and it differs from `bio6` (the
coldest-month *minimum* temperature) — using bio6 would understate CMMT by several
degrees, so we compute CMMT from tavg directly.

Everything CMMT-derived is flagged `[derived]` in the UI: it is occurrence x climate,
never an authoritative species attribute.

Data: `data/worldclim/wc2.1_10m_tavg_{01..12}.tif` (10 arc-minute, ~18.5 km at the
equator, CC-BY 4.0). Pulled once by the ingest; gitignored (large binary).
"""
from __future__ import annotations

import glob
import os

import numpy as np

_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "worldclim")
_NODATA = -1e30  # WorldClim uses a large negative float sentinel


def _tavg_paths() -> list[str]:
    paths = sorted(glob.glob(os.path.join(_DIR, "wc2.1_10m_tavg_*.tif")))
    if len(paths) != 12:
        raise FileNotFoundError(
            f"expected 12 WorldClim tavg rasters in {_DIR}, found {len(paths)}. "
            "Fetch wc2.1_10m_tavg.zip from geodata.ucdavis.edu and unzip it there.")
    return paths


def cmmt_at(points: list[tuple[float, float]]) -> list[float | None]:
    """Coldest-month mean temperature (C) at each (lon, lat). None where off-grid.

    Samples all twelve monthly rasters over the full point list and takes the
    per-point minimum — one pass per raster, vectorised, for tens of thousands of
    points at a time.
    """
    if not points:
        return []
    import rasterio

    coords = [(lon, lat) for lon, lat in points]
    stack = np.full((12, len(coords)), np.nan, dtype="float64")
    for m, path in enumerate(_tavg_paths()):
        with rasterio.open(path) as src:
            vals = np.array([v[0] for v in src.sample(coords)], dtype="float64")
        vals[vals <= _NODATA] = np.nan
        stack[m] = vals
    with np.errstate(invalid="ignore"):
        # off-grid points are all-NaN across months -> NaN (handled below)
        cmmt = np.nanmin(np.where(np.isnan(stack), np.inf, stack), axis=0)
    cmmt[np.isinf(cmmt)] = np.nan  # coldest monthly mean per point
    return [None if np.isnan(v) else round(float(v), 2) for v in cmmt]
