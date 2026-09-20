"""Index the directories an agent would otherwise have to open file by file.

    python3 -m tools.notes            rewrite every index
    python3 -m tools.notes --check    fail if one is stale or unsummarized

Four directories, two shapes. `profile/meetings/` and `profile/interviews/` hold dated
notes, one file per conversation, and their index is one line per note, newest
first. `profile/documents/` and `profile/network/` hold imported material, 257 files of
it, mostly spreadsheets and documents nothing here can read: their index is one
line per directory that holds files, plus the loose files at the top.

The generator owns the skeleton and never touches the prose. Dates, links and
file counts come from the filesystem and from git; the summary is carried
forward verbatim, because it is the one thing no script can write. A new note
or a new directory arrives with its summary set to a placeholder, and `--check`
fails until a person replaces it. That split is the point: the script proves the
index is complete, and the reader writes the line that makes it worth reading.

Material entries come from `git ls-files` rather than from the disk, so the
index reads the same on every clone. `profile/network/export/` is gitignored and
therefore absent from it, which is right: it is re-exportable, and the header
prose above the markers is where it is described.

Write a summary by hand and the line stops matching the generator's wrapping, so
`--check` calls the file stale until the generator runs again. That is the
intended loop: edit the prose, re-run, commit what the generator produced.
"""

import re
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATED_DIRS = ("profile/meetings", "profile/interviews")
MATERIAL_DIRS = ("profile/documents", "profile/network")
START, END = "<!-- index:start -->", "<!-- index:end -->"
# one token on purpose: wrapped across two lines it could not be grepped,
# replaced, or matched by whoever comes to fill it in
NEEDS_A_LINE = "**[needs-a-summary]**"
DATED = re.compile(r"(\d{4}-\d{2}-\d{2})-.+\.md$")
DATED_ENTRY = re.compile(r"\]\((.+?)\)\s+-\s+(.+)", re.S)
MATERIAL_ENTRY = re.compile(r"\*\*(.+?)\*\*(?:\s+\(\d+ files?\))?\s+-\s+(.+)", re.S)
WIDTH = 79


def notes(directory):
    """Every dated note in the directory, newest first."""
    return sorted((p for p in directory.glob("*.md") if DATED.match(p.name)),
                  key=lambda p: p.name, reverse=True)


def title(path):
    """The note's own first heading, with the date it repeats taken off."""
    for line in path.read_text().splitlines():
        if line.startswith("# "):
            return re.sub(r"^\d{4}-\d{2}-\d{2}[,]?\s*", "", line[2:].strip())
    return path.stem


def tracked(directory):
    """What git has under this directory, which is what a fresh clone gets.

    A file deleted but not yet staged is still in git's index, so the ones that
    no longer exist are dropped: an index that lists a file somebody deleted an
    hour ago is worse than no index.

    index.md is dropped for a different reason and it only bites once: the
    index is untracked until the commit that adds it, and the run after that
    commit listed the index inside itself.
    """
    inside = directory.relative_to(ROOT)
    done = subprocess.run(("git", "-C", str(ROOT), "ls-files", "-z", "--",
                           str(inside)), capture_output=True, text=True)
    return sorted(Path(p).relative_to(inside) for p in done.stdout.split("\0")
                  if p and Path(p).name not in ("index.md", "README.md",
                                                ".gitkeep")
                  and (ROOT / p).exists())


def material(directory):
    """One entry per group of files, plus the loose files at the top.

    A group is the first two directory levels, and everything below them counts
    toward it. Indexing every directory instead produced thirty-nine entries
    for `profile/documents/`, several of them five levels down and holding nine
    files, which is a summary nobody will write and a line nobody will read.
    Two levels is where the tree stops being worth a line each.
    """
    files, groups = [], {}
    for inner in tracked(directory):
        if len(inner.parts) == 1:
            files.append((str(inner), None))
        else:
            key = "/".join(inner.parts[:-1][:2]) + "/"
            groups[key] = groups.get(key, 0) + 1
    return sorted(files) + sorted(groups.items())


def existing(index, pattern=DATED_ENTRY):
    """Summaries already written, keyed by what they describe.

    Parsed back out of the rendered list rather than kept in a sidecar,
    because a sidecar is a second copy and this file is the only copy.
    """
    if not index.exists():
        return {}
    body = index.read_text().partition(START)[2].partition(END)[0]
    found = {}
    for entry in re.split(r"\n(?=- )", body.strip()):
        match = pattern.search(entry.strip())
        if match:
            # a key may have been wrapped across lines; a path with a space
            # in it is a path that will not open
            found["".join(match.group(1).split())] = \
                " ".join(match.group(2).split())
    return found


def header(directory, kind):
    """Whatever prose sits above the markers, or a starting point for it."""
    index = directory / "index.md"
    if index.exists() and START in index.read_text():
        return index.read_text().partition(START)[0]
    what = "note" if kind == "dated" else "file"
    return (f"# {directory.name.capitalize()}\n\n"
            f"Read this file first and open only the {what} you need. What it "
            "describes is the authority; this list is a finding aid and can "
            "lag it.\n\n")


def wrap(line):
    return textwrap.fill(line, width=WIDTH, subsequent_indent="  ",
                         break_on_hyphens=False)


def render(directory, kind="dated"):
    """The index as it should be, given what is on disk right now."""
    index = directory / "index.md"
    if kind == "dated":
        known = existing(index)
        lines = [wrap(f"- **{DATED.match(n.name).group(1)}** "
                      f"[{title(n)}]({n.name}) - "
                      f"{known.get(n.name, NEEDS_A_LINE)}")
                 for n in notes(directory)]
    else:
        known = existing(index, MATERIAL_ENTRY)
        lines = []
        for name, count in material(directory):
            plural = "" if count == 1 else "s"
            files = f" ({count} file{plural})" if count else ""
            summary = known.get("".join(name.split()), NEEDS_A_LINE)
            lines.append(wrap(f"- **{name}**{files} - {summary}"))
    listing = "\n".join(lines) or "- nothing here yet"
    return f"{header(directory, kind)}{START}\n{listing}\n{END}\n"


def contents(directory, kind):
    return notes(directory) if kind == "dated" else material(directory)


def wanted_here(directory, kind="dated"):
    """Whether this directory needs an index at all.

    An empty one does not: a fresh clone of the template has all four of these
    and nothing in any of them, and a check demanding an index of nothing would
    block the first commit anyone makes in it. Once an index exists it stays
    checked, so emptying a directory still reports rather than going quiet.
    """
    return bool(contents(directory, kind)) or (directory / "index.md").exists()


def check(directory, kind="dated"):
    """What is wrong with this index, as lines a person can act on."""
    index = directory / "index.md"
    if not wanted_here(directory, kind):
        return []
    problems = []
    if not index.exists() or index.read_text() != render(directory, kind):
        problems.append(f"{index}: stale, run `python3 -m tools.notes`")
    pattern = DATED_ENTRY if kind == "dated" else MATERIAL_ENTRY
    for name, summary in existing(index, pattern).items():
        if NEEDS_A_LINE in summary:
            problems.append(f"{index}: {name} has no summary yet")
    return problems


def indexed():
    return ([(ROOT / d, "dated") for d in DATED_DIRS]
            + [(ROOT / d, "material") for d in MATERIAL_DIRS])


def main(argv):
    if "--check" in argv:
        problems = [p for d, kind in indexed() for p in check(d, kind)]
        for problem in problems:
            print(problem)
        if problems:
            sys.exit(f"\n{len(problems)} index problem(s). An index nobody "
                     "trusts costs more than no index at all.")
        print(f"{len(indexed())} index(es) current")
        return
    for directory, kind in indexed():
        if not wanted_here(directory, kind):
            print(f"skipped {directory}: nothing in it yet")
            continue
        (directory / "index.md").write_text(render(directory, kind))
        print(f"wrote {directory / 'index.md'}: "
              f"{len(contents(directory, kind))} entries")


if __name__ == "__main__":
    main(sys.argv[1:])
