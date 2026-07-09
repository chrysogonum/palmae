"""Data-integrity tests — the invariants that make the slice trustworthy."""
from sqlalchemy import text

from app.db import engine


def _scalar(sql, **p):
    with engine.connect() as c:
        return c.execute(text(sql), p).scalar()


def test_genus_scale_taxonomy():
    # WCVP recognises ~685 accepted Quercus species; assert a genus-wide floor
    # (not the five-species slice) and that the slice species are still present.
    assert _scalar("select count(*) from taxon where accepted") >= 500
    slice_slugs = ("robur", "petraea", "pubescens", "faginea", "frainetto")
    present = _scalar(
        "select count(*) from taxon where accepted and slug = any(:s)",
        s=list(slice_slugs))
    assert present == 5


def test_slugs_unique():
    dupes = _scalar("""
        select count(*) from (
            select slug from taxon where slug is not null
            group by slug having count(*) > 1
        ) d
    """)
    assert dupes == 0


def test_name_reconciliation_zero_unresolved():
    # every alias resolves to an existing accepted taxon (the completion invariant)
    orphans = _scalar("""
        select count(*) from name_alias a
        left join taxon t on t.species_id = a.species_id
        where t.species_id is null
    """)
    assert orphans == 0


def test_native_occurrences_present():
    # The five-species slice carries native GBIF points; genus-agnostic floor
    # (the exact 1,250 count is a slice detail, not an invariant).
    assert _scalar("select count(*) from occurrence where in_native_range and source='GBIF'") >= 1000


def test_layers_present():
    assert _scalar("select count(*) from occurrence where source='iNaturalist'") > 0
    assert _scalar("select count(*) from occurrence where not in_native_range") > 0


def test_faginea_single_lineage():
    # the Iberian near-endemic must carry exactly one chloroplast lineage
    n = _scalar("""
        select count(distinct o.haplotype) from occurrence o
        join taxon t on t.species_id = o.species_id where t.slug = 'faginea'
    """)
    assert n == 1


def test_widespread_species_span_lineages():
    # a widespread oak carries several lineages (the "one species, many lineages" story)
    n = _scalar("""
        select count(distinct o.haplotype) from occurrence o
        join taxon t on t.species_id = o.species_id where t.slug = 'robur'
    """)
    assert n >= 2


def test_native_split_is_geographic():
    # Native/introduced is now set by WCVP's TDWG range, not bounding boxes. Sanity:
    # the Iberian near-endemic faginea keeps all its native points in the western
    # Mediterranean (Iberia + Maghreb + far S. France), and has zero native points
    # in the Americas or East Asia — i.e. the range clipping actually happened.
    with engine.connect() as c:
        outside = c.execute(text("""
            select count(*) from occurrence o join taxon t on t.species_id = o.species_id
            where t.slug = 'faginea' and o.in_native_range and (
                ST_X(o.geom) < -12 or ST_X(o.geom) > 12 or
                ST_Y(o.geom) < 25 or ST_Y(o.geom) > 48)
        """)).scalar()
        assert outside == 0, f"faginea has {outside} native points outside the W. Mediterranean"


def test_introduced_layer_spans_species():
    # Genus-wide introduced/out-of-range points exist for more than just the slice.
    n = _scalar("""
        select count(distinct species_id) from occurrence
        where not in_native_range and source='GBIF'
    """)
    assert n >= 5


def test_conflicted_node_exists():
    assert _scalar("select count(*) from phylogeny_node where conflict") >= 1


def test_conservation_assessments_valid():
    # Palm conservation is the Bellot 2022 prediction with the real IUCN Red List (API v4)
    # overlaid: one row per species, every one resolving to an accepted taxon. risk_basis
    # carries assessed vs predicted; assessed rows carry a real iucn_category.
    assert _scalar("select count(distinct species_id) from conservation_assessment") >= 300
    orphans = _scalar("""
        select count(*) from conservation_assessment c
        left join taxon t on t.species_id = c.species_id
        where t.species_id is null
    """)
    assert orphans == 0
    dupes = _scalar("""
        select count(*) from (
            select species_id from conservation_assessment
            group by species_id having count(*) > 1
        ) d
    """)
    assert dupes == 0
    # the assessed/predicted distinction is populated…
    assert _scalar("select count(*) from conservation_assessment where risk_basis is not null") >= 300
    # …and predicted rows carry a Bellot probability
    assert _scalar("""
        select count(*) from conservation_assessment
        where risk_basis = 'predicted' and prediction_probability is not null
    """) >= 1
    # real IUCN categories are loaded (v4 overlay): several distinct categories, and
    # assessed rows carry one. (This invariant was oak-valid, then briefly false during
    # the Bellot-only window, and is true again now the Red List is wired up.)
    assert _scalar("select count(distinct iucn_category) from conservation_assessment "
                   "where iucn_category is not null") >= 5
    assert _scalar("select count(*) from conservation_assessment "
                   "where risk_basis='assessed' and iucn_category is not null") >= 300


def test_infrageneric_placement():
    # Section/subgenus placement from the Hipp global-oaks classification: a genus-wide
    # floor, all eight sections present across both subgenera, and the white-oak slice
    # correctly placed in sect. Quercus.
    assert _scalar("select count(*) from taxon where accepted and section is not null") >= 180
    n_sections = _scalar(
        "select count(distinct section) from taxon where accepted and section is not null")
    assert n_sections == 8
    subgenera = _scalar(
        "select count(distinct subgenus) from taxon where accepted and subgenus is not null")
    assert subgenera == 2
    # every placed section is one of the eight recognised sections
    unknown = _scalar("""
        select count(*) from taxon
        where accepted and section is not null and section not in (
            'Quercus','Lobatae','Virentes','Protobalanus','Ponticae',
            'Cerris','Ilex','Cyclobalanopsis')
    """)
    assert unknown == 0
    # the five workbench white oaks sit in sect. Quercus
    slice_sections = _scalar("""
        select count(distinct section) from taxon
        where slug in ('robur','petraea','pubescens','faginea','frainetto')
    """)
    assert slice_sections == 1
    assert _scalar("select section from taxon where slug = 'robur'") == "Quercus"
