"""API contract tests — every endpoint returns 200 and the design's data shape."""


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_sources(client):
    r = client.get("/sources")
    assert r.status_code == 200
    d = r.json()
    assert len(d) >= 5
    assert {"id", "name", "role", "license", "note",
            "authors", "year", "title", "venue", "doi", "url"} <= set(d[0])


def test_sources_bibliography(client):
    """Every source is citable: a stable link (doi or url) and a licence."""
    d = client.get("/sources").json()
    by_id = {s["id"]: s for s in d}
    # The primary scientific sources carry their verified DOI.
    assert by_id["hipp2020"]["doi"] == "10.1111/nph.16162"
    assert by_id["petit"]["doi"] == "10.1016/S0378-1127(01)00645-4"
    for s in d:
        assert s["license"], f"{s['id']} has no licence"
        assert s["doi"] or s["url"], f"{s['id']} has no citable link"


def test_haplotypes(client):
    d = client.get("/haplotypes").json()
    assert len(d) == 3
    assert {"code", "label", "color", "refugium"} <= set(d[0])
    assert len(d[0]["refugium"]) == 2


def test_tree(client):
    t = client.get("/tree").json()
    assert t["kind"] == "section"
    assert t["children"]
    # the conflicted hybridization node must be present somewhere in the tree
    def has_conflict(n):
        return n.get("conflict") or any(has_conflict(c) for c in n.get("children", []))
    assert has_conflict(t)


def test_occurrences(client):
    d = client.get("/occurrences").json()
    assert {"id", "sp", "lon", "lat", "haplo", "source", "native"} <= set(d[0])
    # Workbench default is the five-species section slice — NOT the whole genus.
    # (Guards a regression where adding the genus tree widened this to ~234 species
    # and shipped ~47k points to the Europe-projected map.)
    species = {p["sp"] for p in d}
    assert species == {"robur", "petraea", "pubescens", "faginea", "frainetto"}
    assert len(d) < 5000  # small payload; genus-wide points live at /occurrences/genus


def test_occurrence_detail(client):
    occ = client.get("/occurrences").json()[0]
    d = client.get(f"/occurrence/{occ['id']}").json()
    assert d["species"] and d["source"] in ("GBIF", "iNaturalist")
    assert "record_url" in d


def test_occurrences_filter(client):
    d = client.get("/occurrences?species=faginea").json()
    assert len(d) >= 250
    assert all(o["sp"] == "faginea" for o in d)


def test_taxa_list(client):
    d = client.get("/taxa").json()
    assert len(d) >= 500  # genus-wide accepted species, not the five-species slice
    assert {"slug", "latin", "common", "section", "iucn", "color", "completeness", "rich"} <= set(d[0])
    # the five richly-featured slice species carry occurrences (rich=True)
    assert sum(1 for t in d if t["rich"]) >= 5
    assert any(t["slug"] == "robur" for t in d)


def test_tree_genus(client):
    d = client.get("/tree/genus").json()

    def tips(n):
        return [n] if n["tip"] else [t for c in n["children"] for t in tips(c)]
    leaves = tips(d)
    assert len(leaves) >= 200  # full-genus species-level phylogeny
    assert {"support", "tip", "sp", "latin", "iucn"} <= set(leaves[0])
    assert sum(1 for t in leaves if t["iucn"]) >= 150  # most tips carry IUCN status
    # the section-Quercus tree (/tree) stays the small workbench tree
    sect = client.get("/tree").json()

    def count(n):
        return 1 if not n["children"] else sum(count(c) for c in n["children"])
    assert count(sect) == 5


def test_occurrences_genus(client):
    d = client.get("/occurrences/genus").json()
    assert len(d) >= 10000  # genus-wide points for the world atlas
    assert {"lon", "lat", "sp", "native"} <= set(d[0])
    assert any(not p["native"] for p in d) and any(p["native"] for p in d)


def test_occurrences_genus_species_filter(client):
    # Clade-focus map fetches points for a specific species set only.
    d = client.get("/occurrences/genus?species=alba,rubra").json()
    assert 0 < len(d) < len(client.get("/occurrences/genus").json())
    assert {p["sp"] for p in d} <= {"alba", "rubra"}


def test_taxon_detail(client):
    d = client.get("/taxa/robur").json()
    assert d["latin"] == "Quercus robur"
    assert d["glance"] and d["links"]
    assert "photo" in d and "photoNote" in d


def test_coverage(client):
    d = client.get("/taxa/coverage").json()
    assert d["total_species"] >= 500  # genus-wide
    assert d["photos_pct"] >= 20  # iNaturalist photos across the genus, not just the slice
    assert 0 <= d["assessed_pct"] <= 100


def test_genus_species_enriched_and_attributed(client):
    # A non-slice species carries iNaturalist/Wikipedia enrichment, properly attributed.
    d = client.get("/taxa/alba").json()
    assert d["photo"] and d["region"]
    assert d["blurb"] and "Wikipedia" in (d["blurbSource"] or "")
    assert (d["blurbUrl"] or "").startswith("http")
    # a hand-written slice blurb is NOT attributed to Wikipedia
    robur = client.get("/taxa/robur").json()
    assert "Wikipedia" not in (robur["blurbSource"] or "")


def test_search_synonym(client):
    d = client.get("/search?q=conferta").json()
    assert d and d[0]["slug"] == "frainetto"
    assert "synonym" in (d[0]["sub"] or "")


def test_search_vernacular(client):
    d = client.get("/search?q=sessile").json()
    assert d and d[0]["slug"] == "petraea"


def test_lenses(client):
    assert client.get("/lens/climate").status_code == 200
    syn = client.get("/lens/syngameon").json()
    assert syn["nodes"] and syn["edges"]
    key = client.get("/lens/keystone").json()
    assert key["focal"] == "robur" and key["bands"]
    con = client.get("/lens/conservation").json()
    assert con["hotspots"] and con["genus_threatened_pct"]
