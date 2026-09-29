"""A judgment row that decided something has to name the criterion it decided on.

    python3 -m tools.learn.judgmentcriterion

The `why` cell is prose, so a run reads well and a hundred runs answer nothing:
of 311 rejects in the log, 202 carry no reason at all and the rest invent a
phrase apiece. The `criterion` cell is the same reasoning in two values a query
can group on, the criteria bullet and its label force, and a row written without
it is a verdict nobody can revisit when that bullet moves.

Only the newest run is read, because that is the one being written now, and only
when its header has the column: every run before it predates the column and no
grep will ever fill those in.
"""

import csv
import sys

from tools.core import repo

ROOT = repo.ROOT
RUNS = "learn/runs"


def absent_inputs(root):
    """The run log is written per instance, so a fresh clone of the template
    has none. A check that fails there teaches everyone who clones it to ignore
    the checks."""
    return [] if (root / RUNS).is_dir() else [RUNS]


def newest_judgment(root):
    """The judgment file of the latest run that has one.

    A run directory is named for the second it started, so newest is lexical,
    the way every other reader of the run log sorts them. A run with only a
    sweep.csv is not a gap: the judgment pass is a person, and a sweep whose
    survivors nobody ruled on is what `reconcile` is for.
    """
    files = sorted((root / RUNS).glob("*/judgment.csv"))
    return files[-1] if files else None


def unnamed(path):
    """Every decided row here whose criterion cell is empty.

    The verdict's position in the file is reported alongside the company,
    because company is blank on some rows and a problem line naming nothing
    cannot be acted on.
    """
    with open(path, newline="") as f:
        rows = csv.DictReader(f)
        if "criterion" not in (rows.fieldnames or ()):
            return []
        return [f"{RUNS}/{path.parent.name}/{path.name}: verdict {n} "
                f"({row['company'] or 'no company'}) is `{row['decision']}` "
                "with no criterion"
                for n, row in enumerate(rows, 1)
                if row["decision"] and not (row["criterion"] or "").strip()]


def check(root=ROOT):
    """Every decided row in the newest judgment file that names no criterion."""
    if absent_inputs(root):
        return []
    path = newest_judgment(root)
    return unnamed(path) if path else []


def main():
    skipped = absent_inputs(ROOT)
    if skipped:
        print(f"skipped: no {' or '.join(skipped)} in this instance yet")
        return
    problems = check(ROOT)
    for problem in problems:
        print(problem)
    if problems:
        sys.exit(f"\n{len(problems)} verdict(s) with no criterion. Name the "
                 "criteria bullet it failed, in that file's own opening words, "
                 "and the bullet's label force beside it.")


if __name__ == "__main__":
    main()
