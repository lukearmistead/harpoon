"""Questions only the candidate can answer, checked against the page he reads.

    python3 -m tools.questions

`[ask: Tenure]` marks such a question wherever it lives, and this asserts each
one is also a line in board.md's Todo, so the fact base cannot accumulate a
private backlog he never sees. It went 20 to 3 that way once.

The key is the word after the marker. Square brackets and no parentheses, so
tools/citations.py does not read it as a markdown link, and because the prose
around it is too long and too fluid to match on. An untagged open question is
not a failure: tagging is a per-entry decision, and a check that fires on
everything gets ignored.
"""

import re
import sys

from tools import repo

ROOT = repo.ROOT
BOARD = "board.md"
ASK = re.compile(r"\[ask: *([^\]]+)\]")
# A placeholder names the shape the marker takes and is not a real question,
# the same exemption tools/citations.py makes for `YYYY-MM-DD-topic.md`.
PLACEHOLDER = re.compile(r"<[^>]*>")


def asked(text):
    """Every key the file tags, with the line it sits on."""
    return [(number, match.group(1))
            for number, line in enumerate(text.splitlines(), 1)
            for match in ASK.finditer(line)
            if not PLACEHOLDER.search(match.group(1))]


def absent_board(root):
    """The board is written per instance, so a fresh clone of the template has
    none. A check that fails there teaches everyone who clones it to ignore
    the checks."""
    return not (root / BOARD).exists()


def check(root=ROOT):
    """Every tagged question that reaches no line on the board."""
    if absent_board(root):
        return []
    board = (root / BOARD).read_text().lower()
    return [f"{file}:{number}: [ask: {key}] reaches no line in {BOARD}"
            for file in repo.markdown(root) if file != BOARD
            for number, key in asked((root / file).read_text())
            if key.lower() not in board]


def main():
    if absent_board(ROOT):
        print(f"skipped: no {BOARD} in this instance yet")
        return
    problems = check(ROOT)
    for problem in problems:
        print(problem)
    if problems:
        sys.exit(f"\n{len(problems)} question(s) for the candidate that he "
                 f"cannot see. Put each on {BOARD}'s Todo.")


if __name__ == "__main__":
    main()
