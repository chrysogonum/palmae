"""Faurby et al. 2016 complete palm supertree (TREE.nex) -> node/edge rows.

Parses the nexus into an adjacency list (each node with its parent), assigning
explicit integer node ids in preorder so parents are always numbered before their
children. Tips carry the species binomial; internal nodes are unlabelled clades
(the supertree file carries branch lengths but no node support). Tip → accepted
taxon reconciliation happens in `run.load_tree` through the NameAlias spine.
"""
from __future__ import annotations

from pathlib import Path

import dendropy

TREE = Path(__file__).resolve().parents[1] / "data" / "palmtraits" / "TREE.nex"


def parse() -> list[dict]:
    """Return node rows: node_id, parent_node_id, is_tip, tip_label, branch_length."""
    tree = dendropy.Tree.get(path=str(TREE), schema="nexus")
    ids: dict[int, int] = {}
    rows: list[dict] = []
    counter = 0
    for nd in tree.preorder_node_iter():
        counter += 1
        ids[id(nd)] = counter
        parent = nd.parent_node
        pid = ids[id(parent)] if parent is not None else None
        is_tip = nd.is_leaf()
        label = nd.taxon.label if (is_tip and nd.taxon is not None) else None
        rows.append({
            "node_id": counter,
            "parent_node_id": pid,
            "is_tip": is_tip,
            "tip_label": label,
            "branch_length": nd.edge.length if nd.edge else None,
        })
    return rows
