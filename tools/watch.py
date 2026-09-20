"""The watch criterion language.

A watchlist row in source/channels.md says what a qualifying seat looks like, in
two primitives comma-joined as AND: `band > 260` and `title ~ staff|principal`.
This module reads that language and nothing else, so it depends on no other
part of the engine; the catalog side of the watch lives in sweep.py.
"""

import re


def band_floor(band):
    """The bottom of a posted band in dollars, or None when none is posted.

    Equity percentages are stripped before parsing rather than excluded by
    size, and a k anywhere means every bare figure is thousands too, so
    "$300-350k" starts at $300K rather than at $300.
    """
    if not band:
        return None
    figures = re.findall(r"(\d[\d,]*\.?\d*)\s*([kK])?",
                         re.sub(r"[\d.,]+\s*%", " ", band))
    scale = 1000 if any(suffix for _, suffix in figures) else 1
    dollars = [float(n.replace(",", "")) * scale for n, _ in figures]
    plausible = [d for d in dollars if d >= 10_000]
    return int(min(plausible)) if plausible else None


TERM = re.compile(r"\s*(title|band)\s*([~>])\s*(.+?)\s*$")


def meets(lead, criterion):
    """Every comma-separated term has to hold.

    `band >` reads the floor rather than the top on purpose: a seat topping
    higher while starting lower is worse than the one that caused the pass,
    and comparing tops would call it a hit. An unposted band passes, because
    an unknown is not a known miss.
    """
    for term in criterion.split(","):
        match = TERM.match(term)
        if not match:
            raise ValueError(f"source/channels.md: cannot read watch term {term!r}")
        key, _, value = match.groups()
        if key == "title" and not re.search(value, lead.title, re.I):
            return False
        if key == "band":
            floor = band_floor(lead.band)
            if floor is not None and floor <= float(value) * 1000:
                return False
    return True
