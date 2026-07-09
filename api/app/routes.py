"""API routes — serve the palm atlas data contracts over the PostGIS database.

The workbench's two anchors are the phylogeny (/tree) and the map (/ranges +
/occurrences). Everything joins through the accepted-taxon key; the categorical
encoding is subfamily; conservation is led by the Bellot predicted risk with the
formal IUCN category as an overlay.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import palette, reference
from .db import get_session

router = APIRouter()

FAURBY = "faurby-supertree"


def _square(url: str | None) -> str | None:
    """iNaturalist photo URL → its 75px square variant (for list thumbnails)."""
    return url.replace("/medium.", "/square.") if url else None


def _load_tdwg_names() -> dict[str, str]:
    """TDWG level-3 code → readable botanical-country name (from the shared geometry)."""
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "data" / "tdwg_level3.geojson"
    try:
        feats = json.loads(path.read_text())["features"]
        return {f["properties"]["LEVEL3_COD"]: f["properties"]["LEVEL3_NAM"]
                for f in feats if f["properties"].get("LEVEL3_COD")}
    except Exception:  # noqa: BLE001
        return {}


_TDWG_NAMES = _load_tdwg_names()


# --------------------------------------------------------------------------- #
# meta: sources, search
# --------------------------------------------------------------------------- #
@router.get("/sources")
def sources(db: Session = Depends(get_session)):
    cols = ("id", "name", "role", "license", "note",
            "authors", "year", "title", "venue", "doi", "url")
    rows = db.execute(text(
        f"select {', '.join(cols)} from data_source order by name")).all()
    return [dict(zip(cols, r)) for r in rows]


@router.get("/search")
def search(q: str = Query(..., min_length=1), db: Session = Depends(get_session)):
    """Resolve a query through the NameAlias table (accepted names + synonyms)."""
    like = f"%{q.lower()}%"
    rows = db.execute(text("""
        select t.slug, t.scientific_name, t.common_name, t.subfamily,
               a.raw_name, a.name_status
        from name_alias a join taxon t on t.species_id = a.species_id
        where lower(a.raw_name) like :like and t.accepted
        order by (a.name_status='accepted') desc, length(a.raw_name), a.raw_name
        limit 14
    """), {"like": like}).all()
    seen, out = set(), []
    for slug, sci, common, subfamily, raw, status in rows:
        if slug in seen:
            continue
        seen.add(slug)
        sub = None
        if status == "synonym":
            sub = f'≡ synonym "{raw}"'
        elif status == "vernacular":
            sub = f'common name "{raw}"'
        out.append({"slug": slug, "latin": sci, "common": common,
                    "color": palette.subfamily_color(subfamily), "sub": sub})
    return out


# --------------------------------------------------------------------------- #
# phylogeny: the Faurby complete tree
# --------------------------------------------------------------------------- #
@router.get("/tree")
def tree(db: Session = Depends(get_session)):
    """The Faurby 2016 species-level supertree (nested). Tips carry their species
    slug, name, subfamily (colour), and predicted risk; internal nodes are clades."""
    rows = db.execute(text("""
        select n.node_id, n.parent_node_id, n.is_tip, n.branch_length,
               t.slug, t.scientific_name, t.subfamily, t.genus,
               c.predicted_category, c.risk_basis
        from phylogeny_node n
        join tree tr on tr.tree_id = n.tree_id and tr.method = :m
        left join taxon t on t.species_id = n.species_id
        left join conservation_assessment c on c.species_id = n.species_id
        order by n.node_id
    """), {"m": FAURBY}).all()
    nodes, root = {}, None
    for nid, parent, is_tip, blen, slug, latin, subfamily, genus, risk, basis in rows:
        node = {"children": []}
        if blen is not None:
            node["len"] = round(blen, 4)
        if is_tip:
            node["sp"] = slug
            node["latin"] = latin
            node["subfamily"] = subfamily
            node["genus"] = genus
            node["color"] = palette.subfamily_color(subfamily)
            node["risk"] = risk or "not-evaluated"
            node["basis"] = basis
        nodes[nid] = (node, parent)
    for nid, (node, parent) in nodes.items():
        if parent is None:
            root = node
        else:
            nodes[parent][0]["children"].append(node)
    return root or {}


@router.get("/tree/genera")
def tree_genera(db: Session = Depends(get_session)):
    """The Yao et al. 2023 plastid phylogenomic backbone as a genus-level tree —
    modern and bootstrap-supported (unlike the species-complete Faurby tree). Tips
    are genera (coloured by subfamily, with a species count and native regions for
    brushing); internal clades carry bootstrap support."""
    n_species = dict(db.execute(text(
        "select genus, count(*) from taxon where accepted and genus is not null "
        "group by genus")).all())
    regions: dict[str, list[str]] = {}
    for genus, code in db.execute(text("""
        select t.genus, r.tdwg_code from range_region r
        join taxon t on t.species_id = r.species_id
        where r.origin='native' and t.accepted and t.genus is not null
    """)):
        regions.setdefault(genus, [])
        if code not in regions[genus]:
            regions[genus].append(code)

    rows = db.execute(text("""
        select node_id, parent_node_id, is_tip, branch_length, support, name, clade_label
        from phylogeny_node n
        join tree tr on tr.tree_id = n.tree_id and tr.method = 'yao2023'
        order by node_id
    """)).all()
    nodes, root = {}, None
    for nid, parent, is_tip, blen, support, name, subfamily in rows:
        node = {"children": []}
        if blen is not None:
            node["len"] = round(blen, 5)
        if support is not None:
            node["support"] = round(support)
        if is_tip:
            node["genus"] = name
            node["subfamily"] = subfamily
            node["color"] = palette.subfamily_color(subfamily)
            node["nSpecies"] = n_species.get(name, 0)
            node["regions"] = regions.get(name, [])
        nodes[nid] = (node, parent)
    for nid, (node, parent) in nodes.items():
        if parent is None:
            root = node
        else:
            nodes[parent][0]["children"].append(node)
    return root or {}


# --------------------------------------------------------------------------- #
# map: TDWG ranges (region choropleth), occurrences (points, when loaded)
# --------------------------------------------------------------------------- #
@router.get("/ranges")
def ranges(species: str | None = None, db: Session = Depends(get_session)):
    """TDWG level-3 ranges. With ?species=slug: that species' native/introduced
    regions. Without: per-region richness (how many native species occupy it) —
    the family diversity map."""
    if species:
        rows = db.execute(text("""
            select r.tdwg_code, r.origin
            from range_region r join taxon t on t.species_id = r.species_id
            where t.slug = :slug
        """), {"slug": species}).all()
        return [{"code": c, "origin": o} for c, o in rows]
    rows = db.execute(text("""
        select tdwg_code, count(*) filter (where origin='native') as richness
        from range_region group by tdwg_code order by richness desc
    """)).all()
    return [{"code": c, "richness": n} for c, n in rows]


@router.get("/species-regions")
def species_regions(db: Session = Depends(get_session)):
    """{ slug: [native TDWG codes] } for every species — the join that lets the tree
    brush the map (select a clade → union its species' regions) and back."""
    rows = db.execute(text("""
        select t.slug, r.tdwg_code
        from range_region r join taxon t on t.species_id = r.species_id
        where r.origin = 'native' and t.accepted
    """)).all()
    out: dict[str, list[str]] = {}
    for slug, code in rows:
        out.setdefault(slug, []).append(code)
    return out


@router.get("/regions/{code}/species")
def region_species(code: str, db: Session = Depends(get_session)):
    """Every palm native to one TDWG region — for the click-a-region → see-its-species
    drill-down, coloured by subfamily and risk."""
    rows = db.execute(text("""
        select t.slug, t.scientific_name, t.subfamily, c.predicted_category
        from range_region r
        join taxon t on t.species_id = r.species_id
        left join conservation_assessment c on c.species_id = t.species_id
        where r.tdwg_code = :code and r.origin = 'native' and t.accepted
        order by t.scientific_name
    """), {"code": code}).all()
    return [{"slug": s, "latin": n, "subfamily": sf, "risk": risk or "not-evaluated",
             "color": palette.subfamily_color(sf), "riskColor": palette.risk_color(risk)}
            for s, n, sf, risk in rows]


@router.get("/occurrences")
def occurrences(species: str | None = None, db: Session = Depends(get_session)):
    """GBIF/iNaturalist points for the map (empty until the occurrence ingest)."""
    sql = ("select o.occurrence_id, t.slug, ST_X(o.geom), ST_Y(o.geom), "
           "o.source, o.in_native_range, o.cmmt "
           "from occurrence o join taxon t on t.species_id = o.species_id")
    params: dict = {}
    if species:
        sql += " where t.slug = :slug"
        params["slug"] = species
    rows = db.execute(text(sql), params).all()
    return [{"id": r[0], "sp": r[1], "lon": r[2], "lat": r[3],
             "source": r[4], "native": r[5], "cmmt": r[6]} for r in rows]


# --------------------------------------------------------------------------- #
# the palm line — occurrences × coldest-month temperature (the money shot)
# --------------------------------------------------------------------------- #
@router.get("/palm-line")
def palm_line(introduced: int = 0, per_species: int = 6,
              db: Session = Depends(get_session)):
    """The frost-line reveal: native palm occurrences with the coldest-month mean
    temperature (CMMT, °C) sampled at each. Down-sampled to `per_species` points per
    species so the family-scale cloud stays legible and light. With ?introduced=1 the
    garden/naturalised points come in too (they scatter past the line).

    Also returns the Reichgelt et al. 2018 frost-line calibration and the curated
    renegade slugs, so the client can draw the line and light up what breaks it."""
    where = "o.cmmt is not null" + ("" if introduced else " and o.in_native_range")
    rows = db.execute(text(f"""
        select slug, lon, lat, cmmt, subfamily, native from (
          select t.slug, ST_X(o.geom) as lon, ST_Y(o.geom) as lat, o.cmmt,
                 t.subfamily, o.in_native_range as native,
                 row_number() over (partition by o.species_id
                                    order by o.in_native_range desc, random()) as rn
          from occurrence o join taxon t on t.species_id = o.species_id
          where {where}
        ) s where rn <= :k
    """), {"k": per_species}).all()
    points = [{"sp": s, "lon": round(lon, 3), "lat": round(lat, 3), "cmmt": c,
               "sub": sub, "native": nat} for s, lon, lat, c, sub, nat in rows]
    renegade_slugs = [r["slug"] for r in _renegade_rows(db)]
    return {
        "points": points,
        "frostLine": {"band": list(reference.FROST_LINE_C),
                      "pivot": reference.FROST_LINE_PIVOT_C},
        "renegadeSlugs": renegade_slugs,
        "note": "Each point is a cleaned native GBIF record, coloured by the WorldClim "
                "coldest-month mean temperature where it sits — a derived climate layer, "
                "not a measured cold tolerance.",
    }


def _renegade_rows(db: Session) -> list[dict]:
    """Resolve the curated renegades to slugs + their data-derived cold edge."""
    out: list[dict] = []
    for r in reference.RENEGADES:
        row = db.execute(text("""
            select t.slug, t.scientific_name, t.subfamily,
                   cp.cmmt_min, cp.cmmt_mean, cp.n_occurrences
            from taxon t
            left join name_alias a on a.species_id = t.species_id
            left join climate_profile cp on cp.species_id = t.species_id
            where t.accepted and (lower(t.scientific_name) = lower(:n)
                                  or lower(a.raw_name) = lower(:n))
            limit 1
        """), {"n": r["name"]}).first()
        if not row:
            continue
        slug, sci, sub, cmin, cmean, n = row
        out.append({
            "slug": slug, "latin": sci, "common": r["common"],
            "subfamily": sub, "color": palette.subfamily_color(sub),
            "note": r["note"], "cmmtMin": cmin, "cmmtMean": cmean, "n": n,
        })
    return out


@router.get("/renegades")
def renegades(db: Session = Depends(get_session)):
    """The cold-hardy palms that break the frost line, each with its data-derived
    coldest-month edge (°C) so the claim is checkable."""
    return {
        "frostLine": {"band": list(reference.FROST_LINE_C),
                      "pivot": reference.FROST_LINE_PIVOT_C},
        "species": _renegade_rows(db),
    }


# --------------------------------------------------------------------------- #
# taxa: catalogue + detail (field guide)
# --------------------------------------------------------------------------- #
@router.get("/taxa")
def taxa(db: Session = Depends(get_session)):
    rows = db.execute(text("""
        select t.species_id, t.slug, t.scientific_name, t.common_name,
               t.genus, t.tribe, t.subfamily,
               c.predicted_category, c.risk_basis
        from taxon t
        left join conservation_assessment c on c.species_id = t.species_id
        where t.accepted
        order by t.scientific_name
    """)).all()
    region_n = dict(db.execute(text(
        "select species_id, count(*) from range_region where origin='native' "
        "group by species_id")).all())
    with_traits = {sid for (sid,) in db.execute(
        text("select distinct species_id from trait"))}
    on_tree = {sid for (sid,) in db.execute(
        text("select distinct species_id from phylogeny_node where species_id is not null"))}
    thumbs = dict(db.execute(text(
        "select species_id, url from photo where source='iNaturalist'")).all())
    out = []
    for sid, slug, sci, common, genus, tribe, subfamily, risk, basis in rows:
        out.append({
            "slug": slug, "latin": sci, "common": common,
            "genus": genus, "tribe": tribe, "subfamily": subfamily,
            "color": palette.subfamily_color(subfamily),
            "risk": risk or "not-evaluated", "riskBasis": basis,
            "riskColor": palette.risk_color(risk),
            "nRegions": region_n.get(sid, 0),
            "endemic": region_n.get(sid, 0) == 1,
            "hasTraits": sid in with_traits, "onTree": sid in on_tree,
            "thumb": _square(thumbs.get(sid)),
        })
    return out


@router.get("/taxa/coverage")
def taxa_coverage(db: Session = Depends(get_session)):
    total = db.execute(text("select count(*) from taxon where accepted")).scalar() or 1
    q = lambda s: db.execute(text(s)).scalar()  # noqa: E731
    traited = q("select count(distinct species_id) from trait")
    ranged = q("select count(distinct species_id) from range_region")
    assessed = q("select count(*) from conservation_assessment")
    on_tree = q("select count(distinct species_id) from phylogeny_node where species_id is not null")
    threatened = q("select count(*) from conservation_assessment where predicted_category='threatened'")
    return {
        "total_species": total,
        "traits_pct": round(100 * traited / total),
        "ranges_pct": round(100 * ranged / total),
        "conservation_pct": round(100 * assessed / total),
        "tree_pct": round(100 * on_tree / total),
        "threatened_of_assessed": threatened,
        "note": "Family-complete names (WCVP), traits (PalmTraits 1.0), TDWG ranges "
                "(WCVP/POWO), the Faurby 2016 phylogeny, and predicted extinction risk "
                "(Bellot et al. 2022). Conservation risk is a model prediction where no "
                "formal IUCN assessment exists.",
    }


def _traits(db: Session, species_id: int) -> dict:
    rows = db.execute(text(
        "select trait_name, value_num, value_cat, unit from trait where species_id = :sid"),
        {"sid": species_id}).all()
    return {name: {"num": num, "cat": cat, "unit": unit} for name, num, cat, unit in rows}


@router.get("/taxa/{slug}")
def taxon_detail(slug: str, db: Session = Depends(get_session)):
    row = db.execute(text("""
        select t.species_id, t.slug, t.scientific_name, t.authorship, t.common_name,
               t.genus, t.tribe, t.subfamily, t.is_hybrid,
               c.predicted_category, c.risk_basis, c.prediction_probability,
               c.iucn_category, c.assessment_year
        from taxon t
        left join conservation_assessment c on c.species_id = t.species_id
        where t.slug = :slug
    """), {"slug": slug}).first()
    if not row:
        raise HTTPException(404, f"unknown species '{slug}'")
    (sid, slug, sci, auth, common, genus, tribe, subfamily, is_hybrid,
     risk, basis, prob, iucn, iucn_year) = row
    tr = _traits(db, sid)

    def cat(name):
        return tr.get(name, {}).get("cat")

    def num(name):
        return tr.get(name, {}).get("num")

    # habit summary from the growth-form flags
    habit_bits = []
    if cat("climbing") == "yes":
        habit_bits.append("climbing (rattan)")
    if cat("acaulescent") == "yes":
        habit_bits.append("stemless")
    elif cat("erect") == "yes":
        habit_bits.append("erect")
    if cat("stem_solitary") == "yes":
        habit_bits.append("solitary")
    elif cat("stem_solitary") == "no":
        habit_bits.append("clustered")

    regions = db.execute(text("""
        select tdwg_code, origin from range_region r join taxon t on t.species_id=r.species_id
        where t.slug=:slug order by origin, tdwg_code
    """), {"slug": slug}).all()
    native = [{"code": c, "name": _TDWG_NAMES.get(c, c)} for c, o in regions if o == "native"]
    introduced = [{"code": c, "name": _TDWG_NAMES.get(c, c)} for c, o in regions if o == "introduced"]

    on_tree = db.execute(text(
        "select 1 from phylogeny_node where species_id=:sid limit 1"), {"sid": sid}).scalar()

    stem_h = num("max_stem_height")
    fruit = " ".join(x for x in [cat("fruit_size_class"), cat("fruit_shape")] if x)
    glance = [
        {"k": "Placement", "v": f"{subfamily} · {tribe or '—'}"},
        {"k": "Habit", "v": ", ".join(habit_bits) or None},
        {"k": "Strata", "v": cat("strata")},
        {"k": "Max stem height", "v": f"{stem_h:g} m" if stem_h is not None else None},
        {"k": "Fruit", "v": (f"{fruit} · {cat('fruit_color')}" if fruit else cat("fruit_color"))},
        {"k": "Native range", "v": f"{len(native)} region(s)" + (" — endemic" if len(native) == 1 else "")},
    ]
    conservation = {
        "risk": risk or "not-evaluated",
        "riskLabel": palette.RISK_LABEL.get(risk or "not-evaluated"),
        "riskColor": palette.risk_color(risk),
        "basis": basis,
        "probability": round(prob, 2) if prob is not None else None,
        "iucn": iucn, "iucnLabel": palette.IUCN_LABEL.get(iucn),
        "iucnColor": palette.IUCN_COLOR.get(iucn) if iucn else None,
        "assessmentYear": iucn_year,
        "source": ("IUCN Red List" if basis == "assessed" else "Bellot et al. 2022") if basis else None,
    }

    # Derived climate envelope (coldest-month edge) — the palm-line / grower layer.
    cp = db.execute(text("""
        select cmmt_mean, cmmt_min, n_occurrences from climate_profile where species_id=:sid
    """), {"sid": sid}).first()
    climate = None
    if cp and cp[1] is not None:
        cmean, cmin, n = cp
        band_lo, band_hi = reference.FROST_LINE_C
        climate = {
            "cmmtMean": cmean, "cmmtMin": cmin, "n": n,
            "belowFrostLine": cmin < band_hi,
            "frostBand": [band_lo, band_hi],
            "note": "Coldest-month mean temperature across this species' native "
                    "occurrences (WorldClim × GBIF) — derived, not a measured cold "
                    "tolerance.",
        }

    ph = db.execute(text(
        "select url, attribution, license, source_url from photo where species_id=:sid "
        "and source='iNaturalist' order by is_default desc limit 1"), {"sid": sid}).first()
    photo = {"url": ph[0], "attribution": ph[1], "license": ph[2], "sourceUrl": ph[3]} if ph else None

    return {
        "slug": slug, "latin": sci, "authority": auth, "common": common,
        "genus": genus, "tribe": tribe, "subfamily": subfamily, "isHybrid": is_hybrid,
        "color": palette.subfamily_color(subfamily),
        "glance": glance, "conservation": conservation, "climate": climate, "photo": photo,
        "nativeRegions": native, "introducedRegions": introduced,
        "onTree": bool(on_tree),
        "traits": {k: (v["num"] if v["num"] is not None else v["cat"]) for k, v in tr.items()},
    }


# --------------------------------------------------------------------------- #
# lenses
# --------------------------------------------------------------------------- #
@router.get("/lens/traits")
def lens_traits(db: Session = Depends(get_session)):
    """Form & function: per-species stem height, fruit length, climbing habit,
    coloured by subfamily — the trait-space scatter."""
    rows = db.execute(text("""
        select t.slug, t.subfamily,
               max(case when tr.trait_name='max_stem_height' then tr.value_num end) as height,
               max(case when tr.trait_name='avg_fruit_length' then tr.value_num end) as fruit,
               max(case when tr.trait_name='climbing' then tr.value_cat end) as climbing
        from taxon t join trait tr on tr.species_id = t.species_id
        group by t.slug, t.subfamily
    """)).all()
    return {r[0]: {"height": r[2], "fruit": r[3], "climbing": r[4] == "yes",
                   "subfamily": r[1], "color": palette.subfamily_color(r[1])}
            for r in rows}


@router.get("/lens/conservation")
def lens_conservation(db: Session = Depends(get_session)):
    """Real conservation cross-cut: threatened share by subfamily, and the
    assessed-vs-predicted split — driven by the loaded Bellot data."""
    by_sub = db.execute(text("""
        select t.subfamily,
               count(*) filter (where c.predicted_category='threatened') as threatened,
               count(*) as total
        from conservation_assessment c join taxon t on t.species_id=c.species_id
        where t.subfamily is not null
        group by t.subfamily order by threatened desc
    """)).all()
    split = dict(db.execute(text(
        "select risk_basis, count(*) from conservation_assessment group by risk_basis")).all())
    totals = db.execute(text("""
        select count(*) filter (where predicted_category='threatened'),
               count(*) from conservation_assessment
    """)).first()
    return {
        "bySubfamily": [{"subfamily": s, "threatened": th, "total": tot,
                         "color": palette.subfamily_color(s)} for s, th, tot in by_sub],
        "assessed": split.get("assessed", 0), "predicted": split.get("predicted", 0),
        "threatened": totals[0], "covered": totals[1],
        "note": "Threatened = IUCN threatened category (assessed) or predicted threatened "
                "(Bellot et al. 2022 high-sensitivity model). Species with no assessment are "
                "shown as not evaluated, not as safe.",
    }
