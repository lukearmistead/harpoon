"""The machine lane of the sweep: fetch, dedupe, filter, digest.

    python3 -m harpoon.sweep            sweep every cataloged channel
    python3 -m harpoon.sweep probe X    find company X's ATS board and seats

Reads the catalog from me/channels.md (rows with an Endpoint cell), drops
what the repo has already decided and what earlier runs already surfaced
(.sweep-seen.json, gitignored), applies the two deterministic gates
(location hard line, title class), and prints only what is new. Judgment
against me/criteria.md stays in the main thread; this prints facts.
"""

import datetime
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from harpoon.boards import FETCHERS, ChannelError

ROOT = Path(__file__).resolve().parent.parent
SEEN = ROOT / ".sweep-seen.json"

LOCATION_OK = re.compile(r"(?i)san francisco|\bsf\b|bay area|berkeley|oakland|remote")
NOT_IC = re.compile(r"(?i)\bmanager\b|\bdirector\b|\bvp\b|vice president|head of|"
                    r"\bchief\b|\bintern\b|internship|new grad")
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


def sweep():
    catalog = load_catalog()
    if not catalog:
        sys.exit("no machine channels in me/channels.md; add Endpoint cells first")
    seen = json.loads(SEEN.read_text()) if SEEN.exists() else {}
    decided = decided_names()
    today = datetime.date.today().isoformat()
    fresh, drops, errors = [], {}, []

    for name, leads, err in fetch_all(catalog):
        if err:
            errors.append(f"{name}: {err}")
        for lead in leads:
            reason = (
                "seen before" if lead.key() in seen
                else "already decided" if norm(lead.company) in decided
                else "wrong metro" if not LOCATION_OK.search(lead.location)
                else "wrong title class" if not TITLE_OK.search(lead.title)
                else "not an IC seat" if NOT_IC.search(lead.title)
                else None)
            seen.setdefault(lead.key(), today)
            if reason:
                drops.setdefault(reason, []).append(lead)
            else:
                fresh.append(lead)

    SEEN.write_text(json.dumps(seen, indent=0))
    print_digest(fresh, drops, errors)


def print_digest(fresh, drops, errors):
    print(f"## New leads ({len(fresh)})\n")
    if fresh:
        print("| Company | Title | Location | Band | URL | Source |")
        print("|---|---|---|---|---|---|")
        for l in sorted(fresh, key=lambda l: l.company.lower()):
            print(f"| {l.company} | {l.title} | {l.location} | {l.band or ''} "
                  f"| {l.url or ''} | {l.source} |")
    print("\n## Dropped")
    for reason, leads in sorted(drops.items()):
        line = f"- {len(leads)} {reason}"
        if reason == "already decided":
            line += ": " + ", ".join(sorted({l.company for l in leads}))
        print(line)
    for e in errors:
        print(f"- ERROR {e} (a dead channel is not an empty one; fix or note it "
              "in me/channels.md)")


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
        sweep()
