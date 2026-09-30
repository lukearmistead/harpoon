"""Index the company files so a ranking stops costing forty file opens.

    python3 -m tools.apply.companies            rewrite apply/index.md
    python3 -m tools.apply.companies --check    fail if it is stale

Forty-eight files averaging 120 lines, and answering "which companies are
best" meant opening all of them. Twice on 2026-09-22 the answer came out of
whichever subset had been read most recently and the candidate caught it.

**Every line here is lifted verbatim from the company file.** Nothing is
summarized, because a summary is a second copy that goes stale the moment the
file changes, which is the disease this is meant to cure rather than spread.
That is also why the entries can be long: length costs nothing when it cannot
drift. `tools/profile/notes.py` carries its summaries forward because no script can
write them; here the prose already exists under headings the files share, so
the generator reads rather than remembers.

Sections are matched by heading, with aliases, because the files were written
over three weeks and the shape settled as they went. A missing section prints
as a gap rather than being hidden: a file with no operator section is a file
that never answered the question, and that is worth seeing in a list.

Status and date come from `board.md`, which owns them. A company file with no
board row, and a board row with no file, are both listed at the bottom: the
first is research nobody can see, the second is a row nobody has looked at.
"""

import re
import sys

from tools.core import tables
from tools.core.repo import ROOT
from tools.source import companyrows

INDEX = ROOT / "apply/index.md"
START, END = "<!-- index:start -->", "<!-- index:end -->"
GAP = "_not in the file_"
LIMIT = 420

SECTIONS = (
    ("Business", ("Business model, in a sentence", "Business model, in one sentence")),
    ("Seat", ("The seat", "The role", "The roles")),
    ("Operator", ("Who is on the other side of the model", "The operator question")),
    ("Moat", ("Moat", "Moat, specifically against better models")),
    ("Against", ("Against it",)),
    ("Paths", ("Warm path", "Paths")),
    ("Next", ("Next",)),
)


def slug_of(name):
    """`Cityblock / Homeward` and `cityblock-homeward` are the same company."""
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")


def board_rows(text):
    """Company name, status and date for every row in board.md's table.

    The columns are found by their header names rather than by position, because
    reading the third cell is reading whatever the table gained last: a `role`
    column was added on 2026-09-27 and a positional read put the seat title where
    the status goes in every entry here.
    """
    rows, columns = {}, {}
    for line in text.split("\n"):
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if "status" in cells:
            columns = {name: i for i, name in enumerate(cells)}
            continue
        if not columns or set(cells[0]) <= set("-:"):
            continue
        name = tables.unlink(cells[0])
        rows[name] = (cells[columns["status"]], cells[columns["date"]],
                      "](apply/" in cells[0])
    return rows


def paragraph(body):
    """First paragraph, unwrapped, capped so one entry cannot run away."""
    para = body.strip().split("\n\n")[0]
    para = " ".join(para.split())
    return para if len(para) <= LIMIT else para[:LIMIT].rsplit(" ", 1)[0] + " ..."


def section(text, names):
    """First paragraph under the first heading that starts with one of `names`.

    Prefix rather than exact match, because the files name the same section
    several ways: "The seats now open, 2026-09-11" and "Moat, specifically
    against better models" are the seat and the moat, dated or qualified by
    whoever wrote them that week.
    """
    blocks = re.split(r"^## (.+?)\s*$", text, flags=re.M)[1:]
    headings = list(zip(blocks[::2], blocks[1::2]))
    for name in names:
        for heading, body in headings:
            if heading.lower().startswith(name.lower()):
                return paragraph(body)
    return None


def verdict(text):
    """The opening verdict paragraph, which every file is required to carry."""
    match = re.search(r"^\*\*Verdict.+?(?=\n\n|\Z)", text, re.M | re.S)
    if not match:
        return None
    return re.sub(r"^\*\*Verdict[,:]?\s*", "**", paragraph(match.group(0)))


def rebase_links(text, slug):
    """Point a bare sibling link at its file, since the index sits one level up."""
    return re.sub(r"\]\(([^)/:#]+)\)", rf"](../apply/{slug}/\1)", text)


def entry(slug, text, row):
    text = rebase_links(text, slug)
    status, date, _ = row or ("**no board row**", "", False)
    head = f"### [{slug}](../apply/{slug}/company.md) . {status}"
    lines = [head + (f" . {date}" if date else ""), ""]
    lines.append(f"**Verdict:** {verdict(text) or GAP}")
    for label, names in SECTIONS:
        lines.append("")
        lines.append(f"**{label}:** {section(text, names) or GAP}")
    return "\n".join(lines)


def watched_slugs(root):
    """Companies source/channels.md watches, by slug.

    A researched company with no board row used to mean one thing, that the
    research never reached the pipeline. Since the watched companies moved off
    board.md on 2026-09-27 it can mean a second thing, that the company is being
    watched exactly as intended, and nine of them have a file. Listing those as a
    gap would report the design as a fault.
    """
    path = root / "source/channels.md"
    if not path.exists():
        return set()
    return {slug_of(name) for name in companyrows.cataloged_names(path.read_text())}


def build(root=ROOT):
    board = board_rows((root / "board.md").read_text())
    watched = watched_slugs(root)
    by_slug = {}
    for path in sorted(root.glob("apply/*/company.md")):
        by_slug[path.parent.name] = path.read_text()

    rows_by_slug = {slug_of(name): row for name, row in board.items()}
    linked = {name for name, (_, _, has_file) in board.items() if has_file}
    out = [f"{len(by_slug)} company files, against {len(board)} rows on `board.md`.", ""]
    for slug, text in by_slug.items():
        out += [entry(slug, text, rows_by_slug.get(slug)), ""]

    orphans = [s for s in by_slug if s not in rows_by_slug and s not in watched]
    watching = [s for s in by_slug if s not in rows_by_slug and s in watched]
    unresearched = sorted(n for n in board if n not in linked)
    out += ["## Researched, with no row on the board", "",
            ", ".join(orphans) if orphans else "None.", "",
            "## Researched and watched in channels, which is not a gap", "",
            ", ".join(watching) if watching else "None.", "",
            "## On the board, with no company file", "",
            ", ".join(unresearched) if unresearched else "None."]
    return "\n".join(out).rstrip() + "\n"


def render(root=ROOT):
    index = root / "apply/index.md"
    old = index.read_text() if index.exists() else (
        "# Company files\n\nGenerated by `python3 -m tools.apply.companies`. "
        "Every line is lifted verbatim from the file it names, so this is "
        "rewritten rather than edited.\n\n" + START + "\n" + END + "\n")
    head, _, rest = old.partition(START)
    _, _, tail = rest.partition(END)
    return f"{head}{START}\n\n{build(root)}\n{END}{tail}"


def absent(root=ROOT):
    """What a fresh clone is missing, so a check can skip instead of crashing.

    The template ships no board and no company files by design, and a check
    that raises there turns a first clone into a blocked first commit. That
    has been the bug three times; this one skips and says what is missing.
    """
    missing = []
    if not (root / "board.md").exists():
        missing.append("board.md")
    if not list(root.glob("apply/*/company.md")):
        missing.append("apply/<company>/company.md")
    return missing


def main(argv):
    skipped = absent()
    if skipped:
        print(f"skipped: no {' or '.join(skipped)} in this instance yet")
        return
    text = render()
    if "--check" in argv:
        current = INDEX.read_text() if INDEX.exists() else ""
        if current != text:
            sys.exit("apply/index.md is stale; run python3 -m tools.apply.companies")
        return
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(text)
    print(f"wrote {INDEX.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
