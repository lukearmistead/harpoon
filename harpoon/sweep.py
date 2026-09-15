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

from harpoon.boards import FETCHERS, ChannelError

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


def load_catalog():
    rows, text = [], (ROOT / "me/channels.md").read_text()
    for line in text.splitlines():
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2:
            kind, _, arg = cells[1].partition(":")
            if kind in FETCHERS:
                rows.append((cells[0], kind, arg))
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


def fetch_all(catalog):
    def run(row):
        name, kind, arg = row
        try:
            return name, FETCHERS[kind](arg), None
        except ChannelError as e:
            return name, [], str(e)
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(run, catalog))


def sweep(audit=False):
    """audit=True reruns every gate but the seen-cache and touches nothing,
    so the prediction logs cover all live postings, not just today's new."""
    catalog = load_catalog()
    if not catalog:
        sys.exit("no machine channels in me/channels.md; add Endpoint cells first")
    seen = {} if audit else (json.loads(SEEN.read_text()) if SEEN.exists() else {})
    ctx = {"seen": seen, "decided": decided_names()}
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
    print_digest(fresh, drops, errors)


STEPS = (
    ("seen-before", lambda l, ctx: l.key() in ctx["seen"]),
    ("already-decided", lambda l, ctx: norm(l.company) in ctx["decided"]),
    ("wrong-metro", lambda l, ctx: not LOCATION_OK.search(l.location)),
    ("title-class", lambda l, ctx: not TITLE_OK.search(l.title)),
    ("ic-seat", lambda l, ctx: bool(NOT_IC.search(l.title))),
    ("tooling-or-gtm", lambda l, ctx: bool(TOOLING_OR_GTM.search(l.title))),
    ("foreign-remote", lambda l, ctx: bool(FOREIGN.search(l.location))
        and not IN_US.search(l.location)),
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


def print_digest(fresh, drops, errors):
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
