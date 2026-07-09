"""Mean annual rainfall per TDWG level-3 region — the "wet tropics" layer for the
World Atlas, to sit alongside palm richness.

Zonal mean of WorldClim 2.1 bio_12 (annual precipitation, mm, 10 arc-minute) over each
WGSRPD level-3 polygon. Static reference data (raster × geometry, both fixed), so it is
computed once into data/region_rainfall.json and merged into the /ranges richness rows
at serve time — no new table, same static-bake path as everything else.

Run:  PYTHONPATH=api .venv/bin/python -m etl.region_rainfall
"""
from __future__ import annotations

import json
import pathlib

import numpy as np
import rasterio
import rasterio.mask

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_RASTER = _ROOT / "data" / "worldclim" / "wc2.1_10m_bio_12.tif"
_GEO = _ROOT / "data" / "tdwg_level3.geojson"
_OUT = _ROOT / "data" / "region_rainfall.json"


def compute() -> dict[str, int]:
    geo = json.loads(_GEO.read_text())
    out: dict[str, int] = {}
    missed: list[str] = []
    with rasterio.open(_RASTER) as src:
        nodata = src.nodata
        for f in geo["features"]:
            code = f["properties"]["LEVEL3_COD"]
            geom = f["geometry"]
            try:
                # all_touched so tiny island regions still catch at least one cell
                arr, _ = rasterio.mask.mask(src, [geom], crop=True, all_touched=True)
            except (ValueError, Exception):  # noqa: B014
                missed.append(code)
                continue
            a = arr[0].astype("float64")
            if nodata is not None:
                a[a == nodata] = np.nan
            a[a < -1e10] = np.nan          # WorldClim large-negative sentinel
            vals = a[~np.isnan(a)]
            if vals.size:
                out[code] = int(round(float(vals.mean())))
            else:
                missed.append(code)
    _OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"  rainfall: {len(out)} regions written to {_OUT.name} "
          f"({len(missed)} with no raster cell)")
    return out


if __name__ == "__main__":
    compute()
