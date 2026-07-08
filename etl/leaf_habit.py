"""Leaf habit (deciduous / evergreen / semi-) for Quercus, from two sources with
per-value provenance:

  1. GIFT (Global Inventory of Floras and Traits) — trait 'Deciduousness' (2.4.1),
     authoritative, aggregated from regional floras, carries reference counts.
  2. Wikipedia — high-precision parse of the article's "Quercus X is a[n] {habit}
     tree/shrub" statement, used only where GIFT is silent.

GIFT wins on overlap. Ambiguous Wikipedia intros (both habits mentioned, or none)
are skipped rather than guessed. Returns rows ready for the trait table, each with a
`source` tag so the two origins stay distinguishable.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request

UA = "QuercusAtlas/1.0 (educational project; contact peter.repetti@gmail.com)"
GIFT_API = "https://gift.uni-goettingen.de/api/extended/index.php"

# canonical value vocabulary
_NORM = {
    "deciduous": "deciduous", "evergreen": "evergreen",
    "semi-deciduous": "semi-deciduous", "semideciduous": "semi-deciduous",
    "semi-evergreen": "semi-evergreen", "semievergreen": "semi-evergreen",
    "variable": "variable",
}
# "Quercus x[, appositive,|(paren)] is a[n] [up to 4 words] {habit} [..] tree/shrub/oak"
_WIKI_RE = re.compile(
    r"Quercus\s+[\w-]+"
    r"(?:\s*,[^.]{0,70}?,|\s+\([^)]*\))?"          # optional common-name appositive
    r"\s+is\s+(?:an?|the)\s+"
    r"(?:[\w.,'’/-]+\s+){0,4}?"
    r"(semi-?deciduous|semi-?evergreen|deciduous|evergreen)"
    r"(?:[\w\s,'’/-]{0,30}?)(?:tree|shrub|oak)",
    re.IGNORECASE,
)
_HABIT_ANY = re.compile(r"\b(semi-?deciduous|semi-?evergreen|deciduous|evergreen)\b", re.I)


def _get(url: str):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": UA}), timeout=180).read())


def gift_habits() -> dict[str, dict]:
    """{ 'Quercus robur': {value, n_refs} } from GIFT Deciduousness (2.4.1)."""
    # Quercus work_ID -> name
    qmap: dict[str, str] = {}
    start = 0
    while True:
        page = _get(f"{GIFT_API}?query=species&startat={start}")
        if not page:
            break
        for r in page:
            if r.get("work_genus") == "Quercus":
                qmap[r["work_ID"]] = r["work_species"]
        if len(page) < 100000:
            break
        start += 100000
        time.sleep(0.2)
    dec = {r["work_ID"]: r for r in _get(f"{GIFT_API}?query=traits&traitid=2.4.1")}
    out: dict[str, dict] = {}
    for wid, name in qmap.items():
        r = dec.get(wid)
        if not r or not r.get("trait_value"):
            continue
        val = _NORM.get(str(r["trait_value"]).lower())
        if not val:
            continue
        refs = str(r.get("references") or "").strip("+")
        n = len([x for x in refs.split(",") if x]) or None
        out[name] = {"value": val, "n": n}
    return out


def _wiki_full(title: str) -> str:
    """Full plain-text article (habit usually lives in the Description section)."""
    q = urllib.parse.urlencode({
        "action": "query", "prop": "extracts", "explaintext": 1,
        "format": "json", "redirects": 1, "titles": title,
    })
    d = _get(f"https://en.wikipedia.org/w/api.php?{q}")
    pages = d.get("query", {}).get("pages", {})
    return next(iter(pages.values()), {}).get("extract", "") if pages else ""


def _canon(word: str) -> str | None:
    w = word.lower().replace("semideciduous", "semi-deciduous").replace("semievergreen", "semi-evergreen")
    return _NORM.get(w)


def wiki_habit(extract: str) -> str | None:
    """High-precision single-habit read of a Wikipedia article; None if ambiguous/absent.
    Primary: the "Quercus X … is a[n] {habit} tree/shrub" statement (anywhere in the
    article — usually the lead or the Description section). Fallback: a single
    unambiguous habit word in the lead only (first 400 chars), to avoid false context
    like "unlike deciduous oaks" deeper in the text."""
    m = _WIKI_RE.search(extract)
    if m:
        return _canon(m.group(1))
    lead = extract[:400]
    hits = {_canon(h) for h in _HABIT_ANY.findall(lead)} - {None}
    base = {h for h in hits if h in ("deciduous", "evergreen")}
    if len(base) == 1 and not any("semi" in h for h in hits):
        return base.pop()
    return None  # both or neither -> don't guess


def build(names: list[str], article_names: list[str] | None = None) -> list[dict]:
    """names = accepted scientific names to resolve. article_names = the subset known
    to have a Wikipedia article (from the stored blurb_url), fetched full-text for the
    backfill. Returns [{name, value, source, n}] with GIFT preferred."""
    g = gift_habits()
    rows: list[dict] = []
    have = set()
    for name in names:
        if name in g:
            rows.append({"name": name, "value": g[name]["value"], "source": "gift", "n": g[name]["n"]})
            have.add(name)
    # Wikipedia backfill (full text) for article-having species GIFT didn't cover
    todo = [n for n in (article_names or names) if n not in have]
    for name in todo:
        try:
            val = wiki_habit(_wiki_full(name))
        except Exception:
            val = None
        if val:
            rows.append({"name": name, "value": val, "source": "wikipedia", "n": None})
        time.sleep(0.15)
    return rows


if __name__ == "__main__":
    import sys
    payload = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {"names": ["Quercus robur"]}
    names = payload["names"] if isinstance(payload, dict) else payload
    articles = payload.get("articles") if isinstance(payload, dict) else None
    r = build(names, articles)
    json.dump(r, open("/tmp/leaf_habit_rows.json", "w"))
    import collections
    print("rows:", len(r), "| by source:", dict(collections.Counter(x["source"] for x in r)),
          "| by value:", dict(collections.Counter(x["value"] for x in r)))
