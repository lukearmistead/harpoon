"""The gate words, read from a file the candidate owns rather than from code."""

import re
from pathlib import Path

import pytest

from tools import gates

FIXTURE = Path(__file__).resolve().parent / "fixtures/gates.md"

MINIMAL = """# Gates

## wrong-metro

```
san francisco, "sf"
```

## title-class

```
machine learning
```

## ic-seat

```
"manager"
```

## tooling-or-gtm

```
```

## foreign-remote

```
europe
```

## in-us

```
united states
```
"""


def write(tmp_path, text):
    (tmp_path / "source").mkdir(exist_ok=True)
    (tmp_path / "source/gates.md").write_text(text)
    return tmp_path


def test_a_bare_word_matches_inside_a_longer_one():
    """Both kinds of list fail silently when a word is too strict, so a bare
    word is a substring: "europe" has to catch "European"."""
    words = gates.compile_terms(["europe", "data scien"])
    assert words.search("European Remote")
    assert words.search("Staff Data Scientist")


def test_a_quoted_word_has_to_stand_alone():
    """The short ones are why quoting exists: an unquoted "ai" matches
    "said" and an unquoted "sf" matches "sfo"."""
    words = gates.compile_terms(['"ai"', '"sf"'])
    assert words.search("AI Engineer")
    assert not words.search("she said so")
    assert not words.search("SFO ground crew")


def test_a_term_with_punctuation_is_not_a_pattern():
    """A period in "u.s." is a period. Nobody writing a place name is
    writing a regex, and an unescaped one matches any character."""
    words = gates.compile_terms(["u.s."])
    assert words.search("Remote, U.S.")
    assert not words.search("uxsy")


def test_every_list_is_compiled_and_an_empty_one_is_none(tmp_path):
    loaded = gates.load(write(tmp_path, MINIMAL))
    assert set(loaded) == set(gates.REQUIRED)
    assert loaded["tooling-or-gtm"] is None
    assert loaded["wrong-metro"].search("Berkeley") is None
    assert loaded["wrong-metro"].search("San Francisco, CA")


def test_a_missing_file_names_the_file_and_the_skill(tmp_path):
    """The first run of a fresh instance is the one that hits this, and the
    error text is the whole of what that person has to go on."""
    with pytest.raises(SystemExit) as stop:
        gates.load(tmp_path)
    assert "source/gates.md" in str(stop.value)
    assert "setup" in str(stop.value)


def test_a_missing_list_names_which_one(tmp_path):
    with pytest.raises(SystemExit) as stop:
        gates.load(write(tmp_path, MINIMAL.replace("## in-us", "## someday")))
    assert "## in-us" in str(stop.value)


def test_the_shipped_lists_still_say_what_the_regexes_said(tmp_path):
    """The lift out of Python is only honest if the words survived it.

    These are the cases the old comments in sweep.py were paid for: a
    peninsula address, an Austrian seat that said so only in its title, and a
    US and Canada posting that must not die on the word Canada.
    """
    loaded = gates.load(write(tmp_path, FIXTURE.read_text()))
    metro, foreign, in_us = (loaded["wrong-metro"], loaded["foreign-remote"],
                             loaded["in-us"])
    assert metro.search("Oakland, CA") and metro.search("Remote (US)")
    assert not metro.search("Palo Alto, CA")
    assert foreign.search("Forward Deployed AI Engineer - based in Austria")
    assert foreign.search("Austria; Remote (Remote)")
    assert not in_us.search("Austria; Remote (Remote)")
    assert in_us.search("Staff ML Engineer, US and Canada")
    assert loaded["title-class"].search("Staff Data Scientist")
    assert loaded["ic-seat"].search("Engineering Manager, Machine Learning")
    assert loaded["tooling-or-gtm"].search("Staff AI Platform Engineer")


def test_the_fixture_and_the_real_file_agree(tmp_path):
    """The fixture is a frozen copy, and a copy that drifts proves nothing.

    It is the tests' only gates file because a fresh clone of the template has
    no source/gates.md at all, so this check no-ops there rather than failing.
    """
    real = Path(__file__).resolve().parent.parent / "source/gates.md"
    if not real.exists():
        pytest.skip("a fresh clone of the template has no source/gates.md yet")

    def lists(text):
        return {slug: sorted(t.strip() for t in re.split(r"[,\n]", body) if t.strip())
                for slug, body in
                ((s, re.search(r"^```[^\n]*\n(.*?)^```", b, re.M | re.S).group(1))
                 for s, b in gates.SECTION.findall(text))}

    assert lists(real.read_text()) == lists(FIXTURE.read_text())
