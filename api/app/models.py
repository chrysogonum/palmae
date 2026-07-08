"""SQLAlchemy ORM models — the Palmae data model (PostGIS-backed).

Mirrors the project spec (`palms-spec.md` §14). The stable join key is the internal
integer `taxon.species_id`; external identifiers (IPNI LSID, WCVP id, GBIF taxonKey,
IUCN id) hang off it. Every incoming record from any source resolves through
`name_alias` to an accepted `species_id` before it is linked.

Palms are a family, not a genus, so placement is subfamily -> tribe -> genus (Genera
Palmarum classification), where the oak model used subgenus -> section. Oak-only
tables (cpDNA haplotypes, the keystone-food-web interactions, phenology) are gone;
palm-native tables (ethnobotanical `use`, `climate_profile` for the frost-line and
hardiness work) take their place, and conservation carries both a formal IUCN
category and a peer-reviewed predicted category (Bellot et al. 2022).
"""
from __future__ import annotations

import datetime as dt

from geoalchemy2 import Geometry
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Taxon(Base):
    __tablename__ = "taxon"

    species_id: Mapped[int] = mapped_column(primary_key=True)
    # External identity
    ipni_lsid: Mapped[str | None] = mapped_column(String, unique=True)
    wcvp_id: Mapped[str | None] = mapped_column(String, index=True)
    gbif_taxon_key: Mapped[int | None] = mapped_column(Integer, index=True)
    iucn_taxon_id: Mapped[str | None] = mapped_column(String)
    # Names & placement (Genera Palmarum: subfamily -> tribe -> genus)
    scientific_name: Mapped[str] = mapped_column(String, index=True)
    authorship: Mapped[str | None] = mapped_column(String)
    common_name: Mapped[str | None] = mapped_column(String)
    genus: Mapped[str | None] = mapped_column(String, index=True)
    tribe: Mapped[str | None] = mapped_column(String, index=True)
    subfamily: Mapped[str | None] = mapped_column(String, index=True)
    rank: Mapped[str] = mapped_column(String, default="species")
    is_hybrid: Mapped[bool] = mapped_column(Boolean, default=False)
    accepted: Mapped[bool] = mapped_column(Boolean, default=True)
    # A short handle used by the frontend (e.g. "pritchardia-martii"); unique.
    slug: Mapped[str | None] = mapped_column(String, unique=True, index=True)

    aliases: Mapped[list["NameAlias"]] = relationship(back_populates="taxon")


class NameAlias(Base):
    """The reconciliation linchpin: synonyms, former genus placements & vernaculars
    -> accepted taxon. Palm genera are actively reshuffled (Dypsis/Chrysalidocarpus,
    Wallichia/Arenga), so name history is first-class."""

    __tablename__ = "name_alias"

    alias_id: Mapped[int] = mapped_column(primary_key=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("taxon.species_id"), index=True)
    raw_name: Mapped[str] = mapped_column(String, index=True)
    authorship: Mapped[str | None] = mapped_column(String)
    # synonym | basionym | misapplied | former-genus-placement | vernacular | accepted
    name_status: Mapped[str] = mapped_column(String)
    source: Mapped[str | None] = mapped_column(String)
    source_id: Mapped[str | None] = mapped_column(String)

    taxon: Mapped[Taxon] = relationship(back_populates="aliases")


class Occurrence(Base):
    """Point evidence (GBIF / iNaturalist). Kept distinct from range regions.

    Cultivated palms are everywhere, so `establishment_means` is load-bearing: the
    frost-line reveal must be driven by native occurrences, not garden specimens."""

    __tablename__ = "occurrence"

    occurrence_id: Mapped[int] = mapped_column(primary_key=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("taxon.species_id"), index=True)
    source: Mapped[str] = mapped_column(String)
    source_record_id: Mapped[str | None] = mapped_column(String)
    geom: Mapped[object] = mapped_column(Geometry("POINT", srid=4326))
    coordinate_uncertainty_m: Mapped[float | None] = mapped_column(Float)
    basis_of_record: Mapped[str | None] = mapped_column(String)
    event_date: Mapped[dt.date | None] = mapped_column(Date)
    license: Mapped[str | None] = mapped_column(String)
    quality_flags: Mapped[dict | None] = mapped_column(JSON)
    dataset_key: Mapped[str | None] = mapped_column(String)  # GBIF publishing dataset
    in_native_range: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    # native | introduced | cultivated | managed (GBIF establishmentMeans; cleaned)
    establishment_means: Mapped[str | None] = mapped_column(String, index=True)
    place: Mapped[str | None] = mapped_column(String)  # reverse-geocoded locality
    # Coldest-month mean temperature at the point (°C), for the frost-line map.
    cmmt: Mapped[float | None] = mapped_column(Float)


class RangeRegion(Base):
    """Range authority as TDWG (WGSRPD level-3) botanical countries from WCVP /
    PalmTraits. Rendered separately from points; few fine expert polygons exist."""

    __tablename__ = "range_region"

    range_id: Mapped[int] = mapped_column(primary_key=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("taxon.species_id"), index=True)
    geom: Mapped[object | None] = mapped_column(Geometry("MULTIPOLYGON", srid=4326))
    source: Mapped[str] = mapped_column(String)
    origin: Mapped[str | None] = mapped_column(String)  # native | introduced
    tdwg_code: Mapped[str | None] = mapped_column(String, index=True)  # WGSRPD level-3


class Tree(Base):
    __tablename__ = "tree"

    tree_id: Mapped[int] = mapped_column(primary_key=True)
    citation_doi: Mapped[str | None] = mapped_column(String)
    method: Mapped[str | None] = mapped_column(String)  # faurby-supertree | paftol
    source_url: Mapped[str | None] = mapped_column(String)

    nodes: Mapped[list["PhylogenyNode"]] = relationship(back_populates="tree")


class PhylogenyNode(Base):
    __tablename__ = "phylogeny_node"

    node_id: Mapped[int] = mapped_column(primary_key=True)
    tree_id: Mapped[int] = mapped_column(ForeignKey("tree.tree_id"), index=True)
    parent_node_id: Mapped[int | None] = mapped_column(ForeignKey("phylogeny_node.node_id"))
    is_tip: Mapped[bool] = mapped_column(Boolean, default=False)
    name: Mapped[str | None] = mapped_column(String)  # display label
    kind: Mapped[str | None] = mapped_column(String)  # subfamily|tribe|genus|clade|tip
    branch_length: Mapped[float | None] = mapped_column(Float)
    support: Mapped[float | None] = mapped_column(Float)
    conflict: Mapped[bool] = mapped_column(Boolean, default=False)
    # molecular | constraint — Faurby places data-poor species by taxonomic
    # constraint; those terminal placements are shown as uncertain.
    placement: Mapped[str | None] = mapped_column(String)
    note: Mapped[str | None] = mapped_column(String)
    tip_label: Mapped[str | None] = mapped_column(String)
    species_id: Mapped[int | None] = mapped_column(ForeignKey("taxon.species_id"))
    clade_label: Mapped[str | None] = mapped_column(String)

    tree: Mapped[Tree] = relationship(back_populates="nodes")


class Trait(Base):
    """PalmTraits 1.0 — growth form, stem, armature, leaf type, fruit. EAV shape."""

    __tablename__ = "trait"

    trait_record_id: Mapped[int] = mapped_column(primary_key=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("taxon.species_id"), index=True)
    trait_name: Mapped[str] = mapped_column(String, index=True)
    value_num: Mapped[float | None] = mapped_column(Float)
    value_cat: Mapped[str | None] = mapped_column(String)
    unit: Mapped[str | None] = mapped_column(String)
    source: Mapped[str | None] = mapped_column(String)
    n_observations: Mapped[int | None] = mapped_column(Integer)
    license: Mapped[str | None] = mapped_column(String)


class Use(Base):
    """Ethnobotanical / economic use of a palm (Lens D — People & palms).

    Curated from the literature (no single open use database), each row cited."""

    __tablename__ = "use"

    use_id: Mapped[int] = mapped_column(primary_key=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("taxon.species_id"), index=True)
    # cane | thatch | heart | food | oil | wax | wine | fiber | construction |
    # ornamental | medicine | ritual
    use_category: Mapped[str] = mapped_column(String, index=True)
    part_used: Mapped[str | None] = mapped_column(String)
    region: Mapped[str | None] = mapped_column(String)
    note: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String)
    evidence_ref: Mapped[str | None] = mapped_column(String)


class ConservationAssessment(Base):
    """Conservation status, led by the peer-reviewed predicted risk (Bellot et al.
    2022) with the formal IUCN category as a display-only overlay for the assessed
    subset. `risk_basis` records which is authoritative for a given species."""

    __tablename__ = "conservation_assessment"

    assessment_id: Mapped[int] = mapped_column(primary_key=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("taxon.species_id"), index=True)
    risk_basis: Mapped[str | None] = mapped_column(String)  # assessed | predicted
    iucn_category: Mapped[str | None] = mapped_column(String)  # LC|NT|VU|EN|CR|DD|... (assessed)
    predicted_category: Mapped[str | None] = mapped_column(String)  # threatened | not-threatened (Bellot)
    prediction_probability: Mapped[float | None] = mapped_column(Float)
    criteria: Mapped[str | None] = mapped_column(String)
    assessment_year: Mapped[int | None] = mapped_column(Integer)
    population_trend: Mapped[str | None] = mapped_column(String)
    threats: Mapped[dict | None] = mapped_column(JSON)
    exsitu_collections_count: Mapped[int | None] = mapped_column(Integer)  # BGCI (tree subset)
    scope: Mapped[str | None] = mapped_column(String)  # global
    source: Mapped[str | None] = mapped_column(String)


class ClimateProfile(Base):
    """Per-species climate envelope derived from native occurrences × WorldClim.

    Powers the palm-line lens and the grower 'will it grow where I live?' surface.
    Everything here is DERIVED (occurrence × climate), never authoritative — flagged
    as such in the UI."""

    __tablename__ = "climate_profile"

    profile_id: Mapped[int] = mapped_column(primary_key=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("taxon.species_id"), index=True, unique=True)
    cmmt_mean: Mapped[float | None] = mapped_column(Float)  # mean coldest-month temp (°C)
    cmmt_min: Mapped[float | None] = mapped_column(Float)   # coldest occupied (°C) — the hardiness edge
    precip_mean_mm: Mapped[float | None] = mapped_column(Float)
    n_occurrences: Mapped[int | None] = mapped_column(Integer)
    hardiness_c: Mapped[float | None] = mapped_column(Float)  # estimated cold tolerance (°C)
    hardiness_zone: Mapped[str | None] = mapped_column(String)  # USDA-equivalent
    derived: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str | None] = mapped_column(String)


class GeneticResource(Base):
    """Reference genome / sequence link-outs (oil palm, date, coconut, betel, rattan)."""

    __tablename__ = "genetic_resource"

    resource_id: Mapped[int] = mapped_column(primary_key=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("taxon.species_id"), index=True)
    resource_type: Mapped[str | None] = mapped_column(String)  # genome | SRA
    accession: Mapped[str | None] = mapped_column(String)
    genome_size_bp: Mapped[int | None] = mapped_column(Integer)
    ploidy: Mapped[int | None] = mapped_column(Integer)
    chromosome_2n: Mapped[int | None] = mapped_column(Integer)
    source_url: Mapped[str | None] = mapped_column(String)


class DataSource(Base):
    """Provenance registry — powers the Sources panel and per-field attribution.
    Seeded from `etl/sources.py`."""

    __tablename__ = "data_source"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g. "wcvp"
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str | None] = mapped_column(String)
    license: Mapped[str | None] = mapped_column(String)
    note: Mapped[str | None] = mapped_column(Text)
    # Full citation fields (bibliography / data-reference surface).
    authors: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(Text)
    venue: Mapped[str | None] = mapped_column(Text)
    doi: Mapped[str | None] = mapped_column(String)
    url: Mapped[str | None] = mapped_column(String)


class Photo(Base):
    """Cached species photo with attribution (iNaturalist CC / PD plate / illustration)."""

    __tablename__ = "photo"

    photo_id: Mapped[int] = mapped_column(primary_key=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("taxon.species_id"), index=True)
    url: Mapped[str | None] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String, default="photo")  # photo|plate|illustration
    attribution: Mapped[str | None] = mapped_column(String)
    license: Mapped[str | None] = mapped_column(String)
    source: Mapped[str | None] = mapped_column(String)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
