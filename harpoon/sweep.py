"""The machine lane of the sweep: fetch, dedupe, filter, digest.

    python3 -m harpoon.sweep            sweep every cataloged channel
    python3 -m harpoon.sweep probe X    find company X's ATS board and seats

Reads the catalog from me/channels.md (rows with an Endpoint cell), drops
what the repo has already decided and what earlier runs already surfaced
(.sweep-seen.json, gitignored), applies the two deterministic gates
(location hard line, title class), and prints only what is new. Judgment
against me/criteria.md stays in the main thread; this prints facts.
"""

import csv
import datetime
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple

from harpoon.boards import FETCHERS, ChannelError
from harpoon.watch import meets

ROOT = Path(__file__).resolve().parent.parent
SEEN = ROOT / ".sweep-seen.json"
EVALS = ROOT / "evals"

LOCATION_OK = re.compile(r"(?i)san francisco|\bsf\b|bay area|berkeley|oakland|remote")
NOT_IC = re.compile(r"(?i)\bmanager\b|\bdirector\b|\bvp\b|vice president|head of|"
                    r"\bchief\b|\bintern\b|internship|new grad")
TOOLING_OR_GTM = re.compile(
    r"(?i)platform|infrastructure|\binfra\b|devops|\bsre\b|reliability|"
    r"solutions architect|account executive|\bsales\b|\bgtm\b|go-to-market|"
    r"support engineer|support specialist|advocate|security|appsec|\bsoc\b|"
    r"recruiter|marketing|designer|\bcounsel\b|evaluator|partnerships|enablement")
FOREIGN = re.compile(
    r"(?i)europe|\bemea\b|\beu\b|united kingdom|london|germany|france|spain|"
    r"poland|romania|belgium|netherlands|prague|israel|india|bengaluru|singapore|"
    r"japan|philippines|brazil|argentina|chile|costa rica|honduras|latin america|"
    r"australia|canada")
IN_US = re.compile(r"(?i)united states|\busa?\b|u\.s\.|san francisco|berkeley|"
                   r"oakland|bay area|america|\bpst\b|\bcalifornia\b")
TITLE_OK = re.compile(
    r"(?i)machine learning|\bml\b|\bai\b|data scien|applied scien|research scien|"
    r"data engineer|deep learning|\bnlp\b|\bllm\b|forward deployed|decision scien")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


class Channel(NamedTuple):
    name: str
    kind: str
    arg: str
    watching: str  # a watchlist row's pass condition; "" for a catalog row


def load_catalog():
    """Rows whose Endpoint cell names a fetcher.

    A four-cell row is a watchlist row and its third cell is the criterion; a
    three-cell catalog row carries prose there instead, so cell count is what
    tells them apart. Cells split on an unescaped pipe, because a title regex
    needs a literal one for alternation and a markdown table spells that \\|.
    """
    rows, text = [], (ROOT / "me/channels.md").read_text()
    for line in text.splitlines():
        cells = [c.strip().strip("`").replace("\\|", "|")
                 for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) >= 2:
            kind, _, arg = cells[1].partition(":")
            if kind in FETCHERS:
                rows.append(Channel(cells[0], kind, arg,
                                    cells[2] if len(cells) >= 4 else ""))
    return rows


def decided_names():
    """Exact normalized names only: a substring match against the pipeline
    text drops every company whose name occurs in prose ("Ada", "Remote")."""
    names = {norm(d.name) for d in (ROOT / "applications").iterdir() if d.is_dir()}
    text = (ROOT / "pipeline.md").read_text()
    for line in text.splitlines():
        if line.startswith("|"):
            names.add(norm(line.strip("|").split("|")[0]))
    names |= {norm(b) for b in re.findall(r"\*\*([^*]+?)\*\*", text)}
    return names - {"", norm("Company")}


EMPLOYER_KINDS = {"ashby", "greenhouse", "lever", "smartrecruiters", "workable"}


def watched_names(catalog):
    """Companies cataloged as their own channel in me/channels.md.

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
    something near the slug ("Zipline" against flyzipline). Keying on one of
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
    so the prediction logs cover all live postings, not just today's new."""
    catalog = load_catalog()
    if not catalog:
        sys.exit("no machine channels in me/channels.md; add Endpoint cells first")
    seen = {} if audit else (json.loads(SEEN.read_text()) if SEEN.exists() else {})
    watching = watch_criteria(catalog)
    ctx = {"seen": seen, "decided": decided_names() - watched_names(catalog),
           "watching": watching}
    today = datetime.date.today().isoformat()
    fresh, drops, errors, per_step = [], {}, [], {}

    for name, leads, err in fetch_all(catalog):
        if err:
            errors.append(f"{name}: {err}")
        for lead in leads:
            reason = judge(lead, ctx, per_step)
            seen.setdefault(lead.key(), today)
            if reason:
                drops.setdefault(reason, []).append(lead)
            else:
                fresh.append(lead)

    if not audit:
        SEEN.write_text(json.dumps(seen, indent=0))
    write_predictions(per_step, "audit" if audit else "sweep", today)
    hits = [(l, watching[norm(l.company)]) for l in fresh
            if norm(l.company) in watching]
    print_digest([l for l in fresh if norm(l.company) not in watching],
                 drops, errors, hits)


STEPS = (
    ("seen-before", lambda l, ctx: l.key() in ctx["seen"]),
    ("already-decided", lambda l, ctx: norm(l.company) in ctx["decided"]),
    ("wrong-metro", lambda l, ctx: not LOCATION_OK.search(l.location)),
    ("title-class", lambda l, ctx: not TITLE_OK.search(l.title)),
    ("ic-seat", lambda l, ctx: bool(NOT_IC.search(l.title))),
    ("tooling-or-gtm", lambda l, ctx: bool(TOOLING_OR_GTM.search(l.title))),
    ("foreign-remote", lambda l, ctx: bool(FOREIGN.search(l.location))
        and not IN_US.search(l.location)),
    ("watch-criterion", watch_miss),
)


def judge(lead, ctx, per_step):
    """Walk the funnel; log a prediction at every step the lead reaches."""
    for slug, drops_it in STEPS:
        outcome = "drop" if drops_it(lead, ctx) else "pass"
        per_step.setdefault(slug, []).append((outcome, lead))
        if outcome == "drop":
            return slug
    return None


def write_predictions(per_step, run_slug, today):
    """One CSV per step per run: every lead the step saw, with its call.
    These are the predictions evals/grades.csv later grades."""
    EVALS.mkdir(exist_ok=True)
    for slug, rows in per_step.items():
        with open(EVALS / f"{today}-{run_slug}-{slug}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["prediction", "company", "title", "location", "band",
                        "url", "source"])
            for outcome, l in rows:
                w.writerow([outcome, l.company, l.title, l.location,
                            l.band or "", l.url or "", l.source])


def print_digest(fresh, drops, errors, hits=()):
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
    for e in errors:
        print(f"- ERROR {e} (a dead channel is not an empty one; fix or note it "
              "in me/channels.md)")
    print(f"\nPer-step prediction logs: {EVALS}/<date>-<run>-<step>.csv")


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


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "probe":
        probe(" ".join(sys.argv[2:]) or sys.exit("probe needs a company name"))
    else:
        sweep(audit="audit" in sys.argv[1:])
