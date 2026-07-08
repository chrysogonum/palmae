"""Yao et al. 2023 plastid phylogenomic palm backbone -> a genus-level tree.

The Faurby 2016 supertree is species-complete but old and has no node support. Yao
et al. 2023 (BMC Biology 21:50, doi 10.1186/s12915-023-01544-y) is a modern plastid
phylogenomic framework sampling ~98% of palm genera *with* bootstrap support. It is
NOT species-complete, so it can't replace Faurby — instead it powers a second,
genus-level "modern backbone" view alongside the all-species tree.

This loads a SECOND tree (tree_id=2, method='yao2023') on top of the existing spine;
it does not touch the Faurby tree. Steps:
  1. Parse the 349-accession Newick (broadest genus sampling of the three matrices).
  2. Prune to one representative tip per genus, keeping only genera we recognise
     (this also drops the Colocasia/Araceae outgroup).
  3. Store nodes with bootstrap support on the internal clades.

    PYTHONPATH=api .venv/bin/python -m etl.yao
"""
from __future__ import annotations

import re
from pathlib import Path

import dendropy
from sqlalchemy import delete, func, insert, select, text

from app import models as m
from app.db import SessionLocal

TREE = (Path(__file__).resolve().parents[1] / "data" / "yao2023" /
        "phylogenetic trees of the plams" / "incomplete-105 regions matrix.349_105_result")
TREE_ID = 2
DOI = "10.1186/s12915-023-01544-y"
ID_OFFSET = 1_000_000  # keep node_ids clear of the Faurby tree's


def _genus(label: str) -> str:
    return re.split(r"[_ ]", label.strip())[0]


def parse(known_genera: set[str]) -> list[dict]:
    """Genus-pruned node rows: node_id, parent_node_id, is_tip, genus, support,
    branch_length. One tip per recognised genus; outgroups/unknowns dropped."""
    tree = dendropy.Tree.get(path=str(TREE), schema="newick")

    # pick one representative leaf per recognised genus
    keep_by_genus: dict[str, object] = {}
    for leaf in tree.leaf_node_iter():
        g = _genus(leaf.taxon.label)
        if g in known_genera and g not in keep_by_genus:
            keep_by_genus[g] = leaf.taxon
    tree.retain_taxa(list(keep_by_genus.values()))
    tree.suppress_unifurcations()

    ids: dict[int, int] = {}
    rows: list[dict] = []
    counter = ID_OFFSET
    for nd in tree.preorder_node_iter():
        counter += 1
        ids[id(nd)] = counter
        parent = nd.parent_node
        pid = ids[id(parent)] if parent is not None else None
        is_tip = nd.is_leaf()
        genus = _genus(nd.taxon.label) if (is_tip and nd.taxon is not None) else None
        support = None
        if not is_tip and nd.label:
            try:
                support = float(nd.label)
            except ValueError:
                support = None
        rows.append({
            "node_id": counter, "parent_node_id": pid, "is_tip": is_tip,
            "genus": genus, "support": support,
            "branch_length": nd.edge.length if nd.edge else None,
        })
    return rows


def run() -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not set — see api/.env")
    with SessionLocal() as session:
        # genus -> subfamily (for colouring) from our accepted taxa
        genus_sub = dict(session.execute(text(
            "select genus, subfamily from taxon where accepted and genus is not null "
            "group by genus, subfamily")).all())
        known = set(genus_sub)

        node_rows = parse(known)

        # wipe any prior Yao tree, keep Faurby (tree_id=1) untouched
        session.execute(delete(m.PhylogenyNode).where(m.PhylogenyNode.tree_id == TREE_ID))
        session.execute(delete(m.Tree).where(m.Tree.tree_id == TREE_ID))
        session.flush()

        session.execute(insert(m.Tree), [{
            "tree_id": TREE_ID, "method": "yao2023", "citation_doi": DOI,
            "source_url": "https://doi.org/10.6084/m9.figshare.20489916"}])

        rows = [{
            "node_id": r["node_id"], "tree_id": TREE_ID,
            "parent_node_id": r["parent_node_id"], "is_tip": r["is_tip"],
            "kind": "genus" if r["is_tip"] else "clade",
            "name": r["genus"], "tip_label": r["genus"],
            "clade_label": genus_sub.get(r["genus"]) if r["is_tip"] else None,
            "branch_length": r["branch_length"], "support": r["support"],
        } for r in node_rows]
        for i in range(0, len(rows), 500):
            session.execute(insert(m.PhylogenyNode), rows[i:i + 500])
        session.commit()

        tips = sum(1 for r in node_rows if r["is_tip"])
        supported = sum(1 for r in node_rows if r["support"] is not None)
        print(f"  yao2023: {len(node_rows)} nodes ({tips} genera), "
              f"{supported} internal clades with bootstrap support")
        placed = session.scalar(select(func.count()).select_from(m.PhylogenyNode)
                                .where(m.PhylogenyNode.tree_id == TREE_ID,
                                       m.PhylogenyNode.kind == "genus"))
        print(f"  {placed} genus tips stored (of {len(known)} genera we recognise)")


if __name__ == "__main__":
    run()
