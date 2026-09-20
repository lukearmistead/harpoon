"""The machine lane of the sweep: fetch, dedupe, filter, digest.

    python3 -m tools.sweep            sweep every cataloged channel
    python3 -m tools.sweep audit      rerun every gate, ignoring the cache
    python3 -m tools.sweep probe X    find company X's ATS board and seats
    python3 -m tools.sweep reconcile  kept leads the newest run never judged
    python3 -m tools.sweep grades     what the adjudications have measured

Reads the catalog from source/channels.md (rows with an Endpoint cell), drops
what the repo has already decided and what earlier runs already surfaced
(.sweep-seen.json, gitignored), applies the deterministic gates whose words
live in source/gates.md, and prints only what is new. Judgment against
profile/criteria.md stays in the main thread; this prints facts.

Every run writes learn/runs/<run-id>/, one directory per sweep instance: run.json
and sweep.csv, one row per lead, its decision the gate that fired or "kept".
The adjudication columns start empty and are what makes each gate's error
rate measurable, so fill them in rather than writing prose elsewhere.
"""

import datetime
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple

from tools import tables
from tools.boards import FETCHERS, ChannelError
from tools.contract import norm
from tools.evals import grades, reconcile, write_run
from tools.gates import load as load_gates
from tools.watch import meets

ROOT = Path(__file__).resolve().parent.parent
SEEN = ROOT / ".sweep-seen.json"
RUNS = ROOT / "learn/runs"

# The gate words are source/gates.md, not this file: a search compiled into the
# engine is a search nobody but its author can see. What stays here is the
# funnel, which gate reads which field and in which direction, because an
# allowlist gap is a posting that dies unseen and a denylist gap is one that
# reaches the digest, and that asymmetry is engine behavior rather than taste.
#
# The metro list was once widened past the criteria on the strength of an
# adjudication whose fix cell claimed the criteria had been rewritten to match;
# it had not, and judgment then spent its verdicts rejecting those postings by
# hand, one at a time. Widen a list only when profile/criteria.md says so in its own
# words, and sample that gate's drops afterwards.


class Channel(NamedTuple):
    name: str
    kind: str
    arg: str
    watching: str  # a watchlist row's pass condition; "" for a catalog row


def load_catalog():
    """Rows whose Endpoint cell names a fetcher.

    A four-cell row is a watchlist row and its third cell is the criterion; a
    three-cell catalog row carries prose there instead, so cell count is what
    tells them apart.
    """
    rows = []
    for cells in tables.rows((ROOT / "source/channels.md").read_text()):
        if len(cells) >= 2:
            kind, _, arg = cells[1].partition(":")
            if kind in FETCHERS:
                rows.append(Channel(cells[0], kind, arg,
                                    cells[2] if len(cells) >= 4 else ""))
    return rows


def decided_names():
    """Exact normalized names only: a substring match against the pipeline
    text drops every company whose name occurs in prose ("Ada", "Remote")."""
    names = {norm(d.name) for d in (ROOT / "apply").iterdir() if d.is_dir()}
    text = (ROOT / "board.md").read_text()
    for cells in tables.rows(text):
        names.add(norm(cells[0]))
    names |= {norm(b) for b in re.findall(r"\*\*([^*]+?)\*\*", text)}
    return names - {"", norm("Company")}


EMPLOYER_KINDS = {"ashby", "greenhouse", "lever", "smartrecruiters", "workable"}


def watched_names(catalog):
    """Companies cataloged as their own channel in source/channels.md.

    A promising company with no seat sits on the board and is swept anyway, so
    that a new posting is noticed the run it appears. Without this, its own
    board row would drop it as already-decided and the watch would be silent.
    Fund and aggregator channels are excluded: their leads are portfolio
    companies, not the channel itself. The exemption lasts as long as the
    catalog row does, so deleting the row is how watching stops.
    """
    return {norm(ch.arg) for ch in catalog if ch.kind in EMPLOYER_KINDS} | \
           {norm(ch.name) for ch in catalog if ch.kind in EMPLOYER_KINDS}


def watch_criteria(catalog):
    """Each watched company's pass condition, keyed the two ways
    watched_names keys its set.

    A lead's company comes back from the ATS as the display name or as
    something near the slug ("Acme" against flyacme). Keying on one of
    the two leaves the criterion unfound, and that fails open: the company is
    already exempt from already-decided, so its postings would reach the
    digest unchecked while the watch looked like it worked.
    """
    criteria = {}
    for ch in catalog:
        if ch.watching and ch.kind in EMPLOYER_KINDS:
            criteria[norm(ch.name)] = ch.watching
            criteria[norm(ch.arg)] = ch.watching
    return criteria


def watch_miss(lead, ctx):
    """True when the company is watched for something this posting is not."""
    criterion = ctx["watching"].get(norm(lead.company))
    return bool(criterion) and not meets(lead, criterion)


def fetch_all(catalog):
    def run(ch):
        try:
            return ch.name, FETCHERS[ch.kind](ch.arg), None
        except ChannelError as e:
            return ch.name, [], str(e)
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(run, catalog))


def sweep(audit=False):
    """audit=True reruns every gate but the seen-cache and touches nothing,
    so the prediction log covers all live postings, not just today's new."""
    catalog = load_catalog()
    if not catalog:
        sys.exit("no machine channels in source/channels.md; add Endpoint cells first")
    seen = {} if audit else (json.loads(SEEN.read_text()) if SEEN.exists() else {})
    watching = watch_criteria(catalog)
    ctx = {"seen": seen, "decided": decided_names() - watched_names(catalog),
           "watching": watching, "gates": load_gates(ROOT)}
    started = datetime.datetime.now()
    today = started.date().isoformat()
    rows, fresh, drops, errors, channels, this_run = [], [], {}, [], {}, set()

    for name, leads, err in fetch_all(catalog):
        if err:
            errors.append(f"{name}: {err}")
        channels[name] = len(leads)
        for lead in leads:
            decision = "duplicate" if lead.key() in this_run else judge(lead, ctx)
            this_run.add(lead.key())
            seen.setdefault(lead.key(), today)
            rows.append((decision, lead))
            if decision == "kept":
                fresh.append(lead)
            else:
                drops.setdefault(decision, []).append(lead)

    if not audit:
        SEEN.write_text(json.dumps(seen, indent=0))
    run_dir = RUNS / started.strftime("%Y-%m-%dT%H%M%S")
    write_run(rows, run_dir, {
        "run": run_dir.name, "mode": "audit" if audit else "sweep",
        "started": started.isoformat(timespec="seconds"),
        "finished": datetime.datetime.now().isoformat(timespec="seconds"),
        "decisions": list(DECISIONS), "channels": channels, "errors": errors,
        "counts": {d: len(v) for d, v in sorted(drops.items())} | {"kept": len(fresh)},
    })
    hits = [(l, watching[norm(l.company)]) for l in fresh
            if norm(l.company) in watching]
    print_digest([l for l in fresh if norm(l.company) not in watching],
                 drops, errors, hits, run_dir)


def keeps(ctx, slug, text):
    """A keep-list gate: does this text name something the list allows?

    An empty list keeps everything, because a person who will work anywhere
    wants no metro list rather than a metro list that matches nothing.
    """
    words = ctx["gates"][slug]
    return words is None or bool(words.search(text))


def names(ctx, slug, text):
    """A drop-list gate: does this text name something the list bars?"""
    words = ctx["gates"][slug]
    return words is not None and bool(words.search(text))


STEPS = (
    ("seen-before", lambda l, ctx: l.key() in ctx["seen"]),
    ("already-decided", lambda l, ctx: norm(l.company) in ctx["decided"]),
    ("wrong-metro", lambda l, ctx: not keeps(ctx, "wrong-metro", l.location)),
    ("title-class", lambda l, ctx: not keeps(ctx, "title-class", l.title)),
    ("ic-seat", lambda l, ctx: names(ctx, "ic-seat", l.title)),
    ("tooling-or-gtm", lambda l, ctx: names(ctx, "tooling-or-gtm", l.title)),
    # Title as well as location, because a posting that means it says so there:
    # "Forward Deployed AI Engineer (Senior/Principal) - based in Austria".
    ("foreign-remote",
        lambda l, ctx: names(ctx, "foreign-remote", l.title + " " + l.location)
        and not names(ctx, "in-us", l.title + " " + l.location)),
    ("watch-criterion", watch_miss),
)


DECISIONS = ("duplicate", *(slug for slug, _ in STEPS), "kept")

def judge(lead, ctx):
    """Walk the funnel and name what happened: the gate that fired, or kept.

    A lead dies at one gate, so one row says everything the eight per-gate
    files used to say between them, as long as run.json keeps the order.
    """
    for slug, drops_it in STEPS:
        if drops_it(lead, ctx):
            return slug
    return "kept"


def why_nothing_survived(drops):
    """The one line a run of zero leads owes whoever asked for leads.

    A heading reading "New leads (0)" over a column of counts looks like a
    quiet market, and it is almost never a quiet market: it is one gate eating
    everything, and the words that gate reads are in a file the candidate
    owns. So name the gate, name the file, and say what to do about it.
    """
    reason, leads = max(drops.items(), key=lambda kv: len(kv[1]))
    total = sum(len(v) for v in drops.values())
    line = f"\nNothing survived: {len(leads)} of {total} postings died at {reason}"
    if reason in ("wrong-metro", "title-class", "ic-seat", "tooling-or-gtm",
                  "foreign-remote"):
        return (f"{line}, which is the `## {reason}` list in source/gates.md. "
                "Change that list to change what the sweep keeps.")
    if reason == "seen-before":
        return (f"{line}, so an earlier run already showed them. "
                "`python3 -m tools.sweep audit` replays every live posting.")
    if reason == "already-decided":
        return f"{line}, so board.md already carries a row for each of them."
    return line + "."


def print_digest(fresh, drops, errors, hits=(), run_dir=None):
    if hits:
        print(f"## Watchlist hits ({len(hits)})\n")
        for l, criterion in sorted(hits, key=lambda h: h[0].company.lower()):
            print(f"- **{l.company}**: {l.title} | {l.band or 'no band'} | "
                  f"{l.url or ''}")
            print(f"  matched `{criterion}`")
        print()
    print(f"## New leads ({len(fresh)})\n")
    if fresh:
        print("| Company | Title | Location | Band | URL | Source |")
        print("|---|---|---|---|---|---|")
        for l in sorted(fresh, key=lambda l: l.company.lower()):
            cells = (l.company, l.title, l.location, l.band or "", l.url or "",
                     l.source)
            print("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    print("\n## Dropped")
    for reason, leads in sorted(drops.items()):
        line = f"- {len(leads)} {reason}"
        if reason == "already-decided":
            line += ": " + ", ".join(sorted({l.company for l in leads}))
        print(line)
    if not fresh and not hits and drops:
        print(why_nothing_survived(drops))
    for e in errors:
        print(f"- ERROR {e} (a dead channel is not an empty one; fix or note it "
              "in source/channels.md)")
    if run_dir:
        print(f"\nPrediction log: {run_dir}/sweep.csv. Adjudicate a row by "
              "filling its adjudication column with the decision the gate "
              "should have made.")


def probe(company):
    variants = {norm(company), norm(company).replace(" ", ""),
                re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-"),
                company.lower().replace(" ", "")}
    ats_kinds = ("ashby", "greenhouse", "lever", "smartrecruiters", "workable")
    def run(pair):
        kind, slug = pair
        try:
            return kind, slug, FETCHERS[kind](slug)
        except ChannelError:
            return kind, slug, None
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = pool.map(run, [(k, s) for k in ats_kinds for s in variants])
    hit = False
    for kind, slug, leads in results:
        if leads is None:
            continue
        hit = True
        print(f"## {kind}:{slug} ({len(leads)} open)")
        for l in leads:
            print(f"- {l.title} | {l.location} | {l.band or 'no band'} | {l.url}")
    if not hit:
        print(f"no ATS board answered for {company!r}; the slug may be unusual: "
              "check the apply link on their careers page")


def reconcile_board():
    """Reconcile the newest sweep against everything the repo already knows.

    A slug is not a display name: a company is boarded under the name a person
    types and its leads arrive under the ATS slug, numeric suffix and all, so
    the catalog keys both ways. Match on one of the two and a company that has
    sat on the board for weeks is reported unjudged, every single run.
    """
    reconcile(RUNS, decided_names() | watched_names(load_catalog()))


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "probe":
        probe(" ".join(sys.argv[2:]) or sys.exit("probe needs a company name"))
    elif command == "reconcile":
        reconcile_board()
    elif command == "grades":
        grades(RUNS)
    else:
        sweep(audit=command == "audit")
