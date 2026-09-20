"""Every path this repo cites, checked against what is actually here.

    python3 -m tools.citations

A rule that points at a missing file is a rule that silently never runs, so
every backticked path and every markdown link has to resolve, whether it is
prose in the rulebook or a link on the board.

Two kinds of absence are not failures. Imported source material is
deliberately gitignored, so a fresh clone does not have it; derived work
product inside an ignored directory is re-included in .gitignore precisely so
this still covers it. And the per-instance paths below carry the candidate's
own content, so the public template ships the rules that name them without the
files themselves. Both get counted and reported rather than failing, because a
template whose own checks fail teaches everyone who clones it to ignore them.
"""

import re
import sys
from typing import NamedTuple

from tools import repo

ROOT = repo.ROOT

# Everything the candidate writes rather than clones. The setup skill and the
# first sweep create these, so the template ships the rules that name them
# without the files themselves. Adding a template citation to one of them means
# adding it here in the same turn: that has now been the bug three times, and
# the third time it was 118 dead citations in the exported template, because the
# rules cite the board and the criteria on nearly every page and neither was
# ever on this list.
PER_INSTANCE = ("board.md", "learn/lessons.md",
                "profile/criteria.md", "profile/experience.md",
                "profile/resume.md", "profile/voice.md",
                "profile/positioning.md",
                "source/gates.md", "source/channels.md",
                "profile/meetings/", "profile/interviews/",
                "profile/documents/", "profile/network/",
                "profile/meetings/index.md", "profile/interviews/index.md",
                "profile/documents/index.md", "profile/network/index.md",
                # bare, because four directories carry one and the rules name
                # the file generically rather than picking one of the four
                "index.md")

# `profile/experience.md`, `apply/`, `board.md`
BACKTICKED = re.compile(
    r"`([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_. -]+)+/?|[A-Za-z0-9_.-]+\.(?:md|sh))`")
# [file](apply/acme-health/company.md). The character class excludes the colon
# and the hash, which is what keeps URLs and anchors out.
LINKED = re.compile(r"\]\(([A-Za-z0-9_.][A-Za-z0-9_./ -]*)\)")
# A naming convention is not a citation. `YYYY-MM-DD-topic.md` names the shape
# a file should take, and no file of that literal name should ever exist.
PLACEHOLDER = re.compile(r"YYYY|MM-DD|<[^>]+>|\{[^}]+\}")
BULLET_MAP = "## What backs each bullet"


class Citation(NamedTuple):
    file: str
    line: int
    path: str


def cited(file, text):
    """Every path the file names, in the order a reader would meet them."""
    found = [Citation(file, number, match.group(1))
             for number, line in enumerate(text.splitlines(), 1)
             for pattern in (BACKTICKED, LINKED)
             for match in pattern.finditer(line)
             if not PLACEHOLDER.search(match.group(1))]
    return list(dict.fromkeys(found))  # the same path twice on a line is one


def resolves(citation, root):
    """A markdown link resolves against the file that carries it, not against
    the repo root, so both are tried. profile/meetings/index.md links a sibling
    note by bare filename, which is right for whoever opens it and invisible
    from here."""
    beside = (root / citation.file).parent / citation.path
    return (root / citation.path).exists() or beside.exists()


def bullet_map_gaps(root):
    """The resume's map names sections of the fact base rather than paths, so
    the scan above cannot see it. Every drafting skill reaches
    profile/experience.md through that map, which makes a stale entry a bullet
    with nothing behind it. Absent in a fresh clone, so this no-ops there."""
    resume, experience = root / "profile/resume.md", root / "profile/experience.md"
    if not (resume.exists() and experience.exists()):
        return []
    lines = resume.read_text().splitlines()
    start = next((i for i, line in enumerate(lines)
                  if line.startswith(BULLET_MAP)), None)
    if start is None:
        return []
    headings = "\n".join(lines[start:])
    known = experience.read_text().splitlines()
    return [f"profile/resume.md: the bullet map names {section}, which "
            "profile/experience.md does not have"
            for section in sorted(set(re.findall(r"`(## [^`\n]+)`", headings)))
            if section not in known]


def check(root=ROOT):
    """The dead citations, and how many absences were local by design."""
    absent = [c for file in repo.markdown(root)
              for c in cited(file, (root / file).read_text())
              if not resolves(c, root)]
    local = repo.ignored({c.path for c in absent}, root).union(PER_INSTANCE)
    dead = [f"{c.file}:{c.line}: missing {c.path}"
            for c in absent if c.path not in local]
    local_only = len(absent) - len(dead)
    return dead + bullet_map_gaps(root), local_only


def main():
    dead, local_only = check(ROOT)
    for problem in dead:
        print(problem)
    if local_only:
        print(f"{local_only} citation(s) point at imported material or at a "
              "file created per instance. Absent from a fresh clone by design.")
    if dead:
        sys.exit(f"\n{len(dead)} dead citation(s). Fix the path or drop the claim.")


if __name__ == "__main__":
    main()
