"""A throwaway repo on disk, because these checks ask git what to read."""

import subprocess

import pytest


class Repo:
    """Files in a git repo that has never been committed to: everything is
    untracked, which `git ls-files --others` reports exactly like tracked
    work, and .gitignore applies either way."""

    def __init__(self, root):
        self.root = root
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        return target


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path)
