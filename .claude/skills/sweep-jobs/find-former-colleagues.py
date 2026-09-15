"""Find which LinkedIn connections are former colleagues from one company.

Connections.csv stores only a connection's current employer, never their
history, so "used to work with me at <company>" has to be sourced from the
candidate's own corpus: source documents in me/experience/, the fact base, and
me/meetings/. A connection named in that corpus whose current company is not
the one given is a sourced ex-colleague.

Run from the repo root:

    python3 .claude/skills/sweep-jobs/find-former-colleagues.py "Acme Health"

The report prints to stdout. Review it by hand, then write the survivors to
me/network/roster-<slug>.md with a line per person naming the source that
places them at the company. The review matters: a name can appear in the
corpus for reasons unrelated to working there, and each false positive you
strike should be recorded in the roster so it is not re-litigated next run.

PDF sources need pypdf. Without it the script still runs and says which files
it skipped.
"""

import csv
import glob
import re
import sys
import zipfile

CORPUS_GLOBS = [
    "me/experience/**/*.pdf",
    "me/experience/**/*.ipynb",
    "me/experience/**/*.md",
    "me/experience/**/*.docx",
    "me/experience/**/*.xlsx",
    "me/experience/**/*.pptx",
    "me/meetings/*.md",
    "me/experience.md",
]

CONNECTIONS_CSV = "me/network/export/Connections.csv"

# Credentials and generational suffixes that are not last names.
NAME_SUFFIXES = {"md", "phd", "rdn", "cdces", "mph", "ndtr", "jr", "sr",
                 "ii", "iii", "mba", "pmp", "msn", "rn", "ctts", "ms", "rd", "ldn"}


def read_docx_family(path):
    """Strip XML tags out of every part of an Office file."""
    with zipfile.ZipFile(path) as archive:
        parts = [archive.read(n).decode("utf8", "ignore")
                 for n in archive.namelist() if n.endswith(".xml")]
    return re.sub(r"<[^>]+>", " ", " ".join(parts))


def read_pdf(path):
    from pypdf import PdfReader
    return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)


def read_corpus():
    """Map each source file to its lowercased text."""
    paths = sorted({p for g in CORPUS_GLOBS for p in glob.glob(g, recursive=True)})
    corpus = {}
    for path in paths:
        try:
            if path.endswith(".pdf"):
                text = read_pdf(path)
            elif path.endswith((".docx", ".xlsx", ".pptx")):
                text = read_docx_family(path)
            else:
                text = open(path, errors="ignore").read()
        except Exception as exc:
            print(f"skipped {path}: {exc}", file=sys.stderr)
            continue
        corpus[path] = re.sub(r"\s+", " ", text.lower())
    return corpus


def name_variants(first, last):
    """Every "first last" spelling the corpus might use.

    Connections.csv writes names as their owner does, so "A Raad Shebib" has
    to reach "Raad Shebib" and "Carolyn Bradner Jasik, MD" has to reach
    "Carolyn Jasik".
    """
    firsts = [t for t in re.split(r"[^A-Za-z\-]+", first) if len(t) > 1]
    lasts = [t for t in re.split(r"[^A-Za-z\-]+", last)
             if len(t) > 1 and t.lower() not in NAME_SUFFIXES]
    return {f"{f} {l}".lower() for f in firsts for l in lasts}


def read_connections():
    lines = open(CONNECTIONS_CSV).read().split("\n")
    header = next(i for i, l in enumerate(lines) if l.startswith("First Name,Last Name,URL"))
    return list(csv.DictReader(lines[header:]))


def match(connections, corpus):
    """Pair each connection named in the corpus with the files naming them."""
    found = []
    for person in connections:
        variants = name_variants(person["First Name"] or "", person["Last Name"] or "")
        sources = sorted({path for path, text in corpus.items()
                          if any(v in text for v in variants)})
        if sources:
            found.append((person, sources))
    return found


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip().split("\n")[0])
        print(f'usage: python3 {sys.argv[0]} "<company name>"')
        sys.exit(1)
    company = sys.argv[1].lower()

    corpus = read_corpus()
    if not corpus:
        print("no corpus: drop source documents in me/experience/ first")
        sys.exit(1)
    matched = match(read_connections(), corpus)

    def still_there(person):
        return company in (person["Company"] or "").lower()

    control = [p for p, _ in matched if still_there(p)]
    departed = [(p, s) for p, s in matched if not still_there(p)]

    print(f"{len(corpus)} corpus files, {len(matched)} connections named in them\n")
    print(f"Control, still at {sys.argv[1]} ({len(control)}). "
          "Names you know should be here; an empty list means the corpus is thin:")
    for person in sorted(control, key=lambda p: p["Last Name"]):
        print(f"  {person['First Name']} {person['Last Name']} | {person['Position']}")

    print(f"\nDeparted ({len(departed)}), review by hand before writing the roster:")
    for person, sources in sorted(departed, key=lambda x: x[0]["Company"] or "zz"):
        files = ", ".join(s.split("/")[-1] for s in sources[:2])
        print(f"  {person['First Name']} {person['Last Name']} | {person['Company']} "
              f"| {person['Position']} | {files}")


if __name__ == "__main__":
    main()
