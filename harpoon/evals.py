"""The eval log: one directory per sweep instance, one file per step.

A run directory is named for the second it started, because two runs in a
day used to share a filename and the later one won. Inside it, sweep.csv is
one row per lead whose decision is the gate that fired or "kept", and
judgment.csv is one row per posting the judgment step ruled on. Every row
carries empty adjudication columns: filling one in is how a gate's error
rate becomes measurable, and it is the only place a grade belongs.
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

from harpoon.contract import Lead, norm

ROOT = Path(__file__).resolve().parent.parent

ADJUDICATION = ("adjudication", "judge", "adjudicated", "shape", "fix", "note")
SWEEP_COLUMNS = ("decision", *ADJUDICATION, "company", "title", "location",
                 "band", "url", "source")

# The judgment step runs in the main thread, so nothing here writes this file.
# Name its columns anyway: reconcile reads company and url, and a judgment
# pass that invents its own headers makes reconcile find nothing and say so.
#
# "why" is the deciding pass's own reasoning and it is outside ADJUDICATION on
# purpose. It used to be written into "note", which belongs to whoever grades
# the row later, so the first grader had to overwrite the evidence they were
# grading. A sweep row needs no such column, because there the gate is the
# reason; only judgment writes prose at decision time.
JUDGMENT_COLUMNS = ("decision", "why", *ADJUDICATION, "company", "title", "url")


def prior_adjudications(run_dir):
    """Every label written by an earlier run, keyed by lead and decision.

    Every gate is a regex over text that does not change between runs, so a
    label stays true and nobody should have to write it twice. All earlier
    runs are read, newest first, because a posting is not in every run and a
    label read only from the last one dies the first time its lead is absent.
    A row whose decision moved is not carried: that is the case where the gate
    changed, and the old label is exactly what must not survive it.
    """
    labels = {}
    for run in sorted((d for d in run_dir.parent.glob("*")
                       if d.name < run_dir.name and (d / "sweep.csv").exists()),
                      reverse=True):
        with open(run / "sweep.csv", newline="") as f:
            for row in csv.DictReader(f):
                if not row["adjudication"]:
                    continue
                key = Lead(row["company"], row["title"], row["location"], None,
                           row["url"] or None, row["source"]).key()
                labels.setdefault((key, row["decision"]),
                                  [row[c] for c in ADJUDICATION])
    return labels


def revision():
    """Which code produced this run, and whether that is even knowable.

    A run directory is evidence, and a sha on its own overstates it: a dirty
    tree means the commit does not describe what ran, and commits that never
    left the machine cannot be fetched by whoever reads the run later. Git runs
    against this file's own repo rather than the working directory, so a test
    writing into a tmp path still stamps the engine it exercised. Every field
    is null where there is no git and no repo, which is the fresh clone of the
    template.
    """
    def git(*args):
        try:
            done = subprocess.run(("git", "-C", str(ROOT), *args),
                                  capture_output=True, text=True)
        except OSError:
            return None
        return done.stdout.strip() if done.returncode == 0 else None

    commit = git("rev-parse", "--short", "HEAD")
    status = git("status", "--porcelain")
    unpushed = git("rev-list", "--count", "@{upstream}..HEAD")
    return {"commit": commit,
            "dirty": None if status is None else status != "",
            "unpushed": None if unpushed is None else int(unpushed)}


def write_run(rows, run_dir, meta):
    """One directory per sweep instance: what the run did, and what it read
    to do it. sweep.csv is one row per lead, and its adjudication columns
    start empty for a human or a model to fill in later. The revision is
    stamped here rather than by the caller, so no caller can forget it."""
    run_dir.mkdir(parents=True, exist_ok=True)
    carried = prior_adjudications(run_dir)
    blank = [""] * len(ADJUDICATION)
    with open(run_dir / "sweep.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(SWEEP_COLUMNS)
        for decision, l in rows:
            w.writerow([decision, *carried.get((l.key(), decision), blank),
                        l.company, l.title, l.location, l.band or "",
                        l.url or "", l.source])
    meta = meta | {"revision": revision()}
    (run_dir / "run.json").write_text(json.dumps(meta, indent=2) + "\n")


def graded_rows(evals):
    """Every adjudicated row in every run, sweep and judgment alike."""
    for run in sorted(evals.glob("*")):
        for name in ("sweep.csv", "judgment.csv"):
            if not (run / name).exists():
                continue
            with open(run / name, newline="") as f:
                for row in csv.DictReader(f):
                    if row.get("adjudication"):
                        yield run.name, name.removesuffix(".csv"), row


def calls(rows):
    """Group graded rows into the calls they came from.

    One call gets one row per posting it touched and one more per run that
    carried the label forward, so nine peninsula postings graded in one sitting
    are nine rows and a single call. A shape reaching three is what amends a
    skill, and counting rows would reach three on the first sitting every time.

    The cost is that two genuinely separate calls of one shape, graded the same
    day, read as one. That undercounts, which is the safe direction: it delays an
    amendment rather than triggering one nothing supports.
    """
    grouped = {}
    for run, step, row in rows:
        # .get, because judgment.csv is written by hand and a missing column
        # should cost a label, not the whole report
        key = (row.get("shape") or "unlabeled", row.get("adjudicated", ""), step)
        grouped.setdefault(key, {"companies": set(), "rows": 0, "hit": 0})
        c = grouped[key]
        c["companies"].add(row["company"])
        c["rows"] += 1
        c["hit"] += row["adjudication"] == row["decision"]
    return grouped


def grades(evals):
    """What the loop has measured: error rate per decision, shapes by count."""
    rows = list(graded_rows(evals))
    if not rows:
        sys.exit(f"nothing adjudicated under {evals}; a gate nobody labels has "
                 "no measured error rate")
    by_decision = {}
    for _, _, row in rows:
        d = by_decision.setdefault(row["decision"], [0, 0])
        d[0] += 1
        d[1] += row["adjudication"] == row["decision"]
    grouped = calls(rows)
    print(f"## Graded: {len(rows)} rows, {len(grouped)} calls\n")
    print("| Decision | rows | confirmed | overturned |")
    print("|---|---|---|---|")
    for decision, (n, hit) in sorted(by_decision.items(), key=lambda kv: -kv[1][0]):
        print(f"| {decision} | {n} | {hit} | {n - hit} |")
    print("\n## Shapes, counting toward a third\n")
    tally = {}
    for (shape, _, _), c in grouped.items():
        tally.setdefault(shape, []).append(c)
    for shape, cs in sorted(tally.items(), key=lambda kv: -len(kv[1])):
        names = sorted({n for c in cs for n in c["companies"]})
        flag = "  <- three, so the skill changes" if len(cs) >= 3 else ""
        print(f"- **{len(cs)}** {shape}: {', '.join(names[:6])}{flag}")


def reconcile(evals, boarded):
    """Leads the newest run kept and nobody ever ruled on.

    A kept lead is printed in the digest and then lives only in whoever read
    it. The seen-cache remembers it either way, so an unjudged survivor is
    not pending, it is gone: the next run drops it at seen-before and it
    never surfaces again. A lead was lost exactly this way, which is why
    this exists.
    """
    # audit mode keeps every live posting that passes the gates, which nobody
    # promised to judge; only a sweep run's kept set is a digest someone read
    runs = sorted(d for d in evals.glob("*") if (d / "sweep.csv").exists()
                  and json.loads((d / "run.json").read_text())["mode"] == "sweep")
    if not runs:
        sys.exit(f"no sweep run under {evals}; audit runs are not reconciled")
    run = runs[-1]
    judged, urls = set(), set()
    if (run / "judgment.csv").exists():
        with open(run / "judgment.csv", newline="") as f:
            for row in csv.DictReader(f):
                judged.add(norm(row["company"]))
                if row.get("url"):
                    urls.add(row["url"])
    with open(run / "sweep.csv", newline="") as f:
        # a url-less lead must not match a url-less judgment row: that is
        # every posting an aggregator gave no link, silently marked judged
        orphans = [r for r in csv.DictReader(f) if r["decision"] == "kept"
                   and not (r["url"] and r["url"] in urls)
                   and norm(r["company"]) not in judged | boarded]
    print(f"## Kept and never judged in {run.name} ({len(orphans)})\n")
    for r in orphans:
        print(f"- **{r['company']}**: {r['title']} | {r['location']} | "
              f"{r['band'] or 'no band'} | {r['url']}")
    if orphans:
        print("\nEach needs a verdict in judgment.csv and a row on pipeline.md, "
              "or it is lost to the seen-cache.")
