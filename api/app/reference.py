"""Curated palm reference data — cited facts kept in code, not per-record source rows.

The hardy renegades are the point of the palm-line story: the handful of palms that
hold on well past the family's frost line. They are named here with a one-line note on
*where* they break the line; the app pairs each with its data-derived coldest-month
edge (from `climate_profile`) so the claim is checkable, never asserted.

Keyed by accepted scientific name; the API resolves each to its slug through the
NameAlias spine (so former names like Butia capitata still match).
"""
from __future__ import annotations

# The cold-hardy renegades. `note` = the human story; the numeric cold edge comes from
# the ingested WorldClim × GBIF profile, not from here.
RENEGADES = [
    {"name": "Trachycarpus fortunei",
     "common": "Chusan / windmill palm",
     "note": "The hardiest trunking palm in cultivation — grown outdoors through "
             "British and Central European winters, far north of any native palm."},
    {"name": "Rhapidophyllum hystrix",
     "common": "Needle palm",
     "note": "A clumping fan palm of the US Southeast, widely held to be the most "
             "cold-hardy palm of all, surviving hard freezes into the −20 °C range."},
    {"name": "Sabal minor",
     "common": "Dwarf palmetto",
     "note": "A near-stemless palmetto ranging up into the Carolinas and Oklahoma — "
             "one of the northernmost naturally occurring palms on Earth."},
    {"name": "Sabal palmetto",
     "common": "Cabbage palmetto",
     "note": "The cabbage palm of the US Atlantic and Gulf coasts, hardy well into "
             "the subtropical–temperate transition."},
    {"name": "Chamaerops humilis",
     "common": "Mediterranean fan palm",
     "note": "Continental Europe's only native palm, on dry Mediterranean hillsides "
             "that freeze in winter."},
    {"name": "Jubaea chilensis",
     "common": "Chilean wine palm",
     "note": "A massive palm of central Chile's cool, dry Mediterranean climate — a "
             "long way south, on the cold edge of the family's range."},
    {"name": "Nannorrhops ritchieana",
     "common": "Mazari palm",
     "note": "A desert palm of Arabia to Afghanistan enduring frosty continental "
             "winters at altitude — heat and cold in the same range."},
    {"name": "Washingtonia filifera",
     "common": "California fan palm",
     "note": "The only palm native to the western US, in Mojave and Sonoran desert "
             "oases where nights drop below freezing."},
    {"name": "Butia odorata",
     "common": "Pindo / jelly palm",
     "note": "A feather palm of subtropical South America's grasslands, hardy through "
             "frosts well south of the tropics."},
]

# Frost-line calibration (Reichgelt, West & Greenwood 2018): palms indicate a
# coldest-month mean temperature of roughly this band or warmer.
FROST_LINE_C = (2.0, 8.0)
FROST_LINE_PIVOT_C = 5.0  # the display pivot for the diverging colour scale
