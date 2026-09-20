"""The words each sweep gate reads, from source/gates.md rather than from Python.

The funnel stays in tools/sweep.py, because the order of the gates and what
each one reads are the engine. The words are the candidate's search, and a
search compiled into the engine is one nobody can see or change: a template
shipping one person's metro and title class hands everyone else an empty
digest that reads like a quiet market.

Format, which the setup skill writes and this module is the only reader of:
a `## <gate>` heading per list, prose under it for whoever opens the file, and
the words in a fenced block, separated by commas or newlines.
"""

import re
import sys

# Every list the file has to carry. in-us is not a gate of its own: it is the
# exception foreign-remote checks before dropping, so a seat open across the US
# and Canada survives a list that names Canada.
REQUIRED = ("wrong-metro", "title-class", "ic-seat", "tooling-or-gtm",
            "foreign-remote", "in-us")

SECTION = re.compile(r"^## +(\S+)[^\n]*\n(.*?)(?=^## |\Z)", re.M | re.S)
FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.M | re.S)


def compile_terms(terms):
    """A quoted word has to stand alone; a bare one matches anywhere.

    Bare is the default because both kinds of list fail silently when a word
    is too strict: an allowlist gap kills a posting nobody will ever see, and
    a denylist gap lets one through. "europe" has to catch "European" and
    "data scien" has to catch "Data Scientist". Quoting is for the short words
    that would otherwise match inside a longer one, "ai" and "sf" and "uk",
    and roughly one word in five needs it.
    """
    parts = []
    for term in terms:
        if len(term) > 2 and term.startswith('"') and term.endswith('"'):
            parts.append(r"\b" + re.escape(term[1:-1]) + r"\b")
        else:
            parts.append(re.escape(term))
    return re.compile("(?i)" + "|".join(parts))


def load(root):
    """Each list in source/gates.md compiled, keyed by heading. Empty list, None.

    None is a gate switched off, which is a real answer: somebody who will
    work anywhere wants no metro list at all. The two callers in sweep.py read
    it in the direction their gate runs, so an empty allowlist keeps
    everything and an empty denylist drops nothing.
    """
    path = root / "source/gates.md"
    if not path.exists():
        sys.exit(f"{path} is missing, so the sweep does not know what you are "
                 "looking for: where you will work, what kind of work, what is "
                 "never right. Type /setup, or ask for the setup skill, and it "
                 "writes the file with you.")
    gates = {}
    for slug, body in SECTION.findall(path.read_text()):
        fence = FENCE.search(body)
        if fence:
            terms = [t.strip() for t in re.split(r"[,\n]", fence.group(1))]
            terms = [t for t in terms if t]
            gates[slug] = compile_terms(terms) if terms else None
    missing = [s for s in REQUIRED if s not in gates]
    if missing:
        sys.exit(f"{path} has no fenced word list under " +
                 ", ".join(f"## {s}" for s in missing) +
                 ". Every gate needs its heading and a fenced block under it, "
                 "even when the list inside is empty.")
    return gates
