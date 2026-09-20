"""What git says about the files here, for the checks that read every page.

A check that greps the repo asks git which files to read rather than walking
the disk, so that imported material and build leavings stay out of the scan
the same way they stay out of a commit.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def markdown(root=ROOT):
    """Every markdown file git tracks or would notice as new.

    A file deleted but not yet staged is still in the index, so the paths are
    filtered to what is on disk. Without that, a check prints an error per
    absent file on every run until the deletion is staged.
    """
    out = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard",
         "*.md"], cwd=root, capture_output=True, text=True).stdout
    return [p for p in out.split("\0") if p and (root / p).is_file()]


def ignored(paths, root=ROOT):
    """Which of these paths .gitignore covers.

    check-ignore exits 1 when it matches nothing, which is an answer and not
    an error, so the return code is ignored and the output is the answer.
    """
    if not paths:
        return set()
    out = subprocess.run(["git", "check-ignore", "--stdin"], cwd=root,
                         input="\n".join(paths), capture_output=True,
                         text=True).stdout
    return set(out.splitlines())
