"""The company index is only worth having if it cannot drift from the files."""

import textwrap

from tools.apply import companies


def write(root, slug, body):
    path = root / "apply" / slug / "company.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body).lstrip())


BOARD = """\
# Board

| company | status | what they do | date | next |
|---|---|---|---|---|
| [Acme Health](apply/acme-health/company.md) | applied | Widgets | 2026-09-01 | Wait |
| Beta Corp | lead | Gadgets | 2026-09-02 | Read it |
"""


def test_a_column_added_to_the_table_does_not_shift_the_status(tmp_path):
    """The `role` column went in on 2026-09-27 and a positional read printed the
    seat title where every entry's status goes."""
    (tmp_path / "board.md").write_text(
        "# Board\n\n| company | role | status | what they do | date |\n"
        "|---|---|---|---|---|\n"
        "| Beta Corp | Staff ML Engineer | lead | Gadgets | 2026-09-02 |\n")
    rows = companies.board_rows((tmp_path / "board.md").read_text())
    assert rows["Beta Corp"][:2] == ("lead", "2026-09-02")


def test_entry_lifts_prose_verbatim(tmp_path):
    (tmp_path / "board.md").write_text(BOARD)
    write(tmp_path, "acme-health", """
        # Acme Health

        **Verdict: apply.** San Francisco.

        ## Business model, in a sentence

        Hospitals pay for widgets.

        ## Next

        Send it.
        """)
    out = companies.build(tmp_path)
    assert "Hospitals pay for widgets." in out
    assert "**Verdict:** **apply.** San Francisco." in out
    assert "applied" in out and "2026-09-01" in out


def test_heading_aliases_and_prefixes_match(tmp_path):
    (tmp_path / "board.md").write_text(BOARD)
    write(tmp_path, "acme-health", """
        # Acme Health

        **Verdict: apply.**

        ## Moat, specifically against better models

        Contracts.

        ## The seats now open, 2026-09-11

        A staff one.
        """)
    out = companies.build(tmp_path)
    assert "**Moat:** Contracts." in out
    assert "**Seat:** A staff one." in out


def test_missing_section_prints_a_gap(tmp_path):
    (tmp_path / "board.md").write_text(BOARD)
    write(tmp_path, "acme-health", "# Acme Health\n\n**Verdict: apply.**\n")
    assert companies.GAP in companies.build(tmp_path)


def test_both_kinds_of_gap_are_listed(tmp_path):
    (tmp_path / "board.md").write_text(BOARD)
    write(tmp_path, "orphan-co", "# Orphan Co\n\n**Verdict: apply.**\n")
    out = companies.build(tmp_path)
    assert "orphan-co" in out.split("## Researched, with no row on the board")[1]
    assert "Beta Corp" in out.split("## On the board, with no company file")[1]


def test_slug_matches_a_name_with_punctuation(tmp_path):
    (tmp_path / "board.md").write_text(
        BOARD + "| [Cityblock / Homeward](apply/cityblock-homeward/company.md)"
        " | watch | Care | 2026-09-03 | None |\n")
    write(tmp_path, "cityblock-homeward", "# C\n\n**Verdict: watch.**\n")
    out = companies.build(tmp_path)
    assert "cityblock-homeward](../apply/cityblock-homeward/company.md) . watch" in out
    assert "cityblock-homeward" not in out.split(
        "## Researched, with no row on the board")[1]


def test_a_long_paragraph_is_capped(tmp_path):
    (tmp_path / "board.md").write_text(BOARD)
    write(tmp_path, "acme-health",
          "# A\n\n**Verdict: apply.**\n\n## Business model, in a sentence\n\n"
          + "word " * 200 + "\n")
    line = [l for l in companies.build(tmp_path).split("\n")
            if l.startswith("**Business:**")][0]
    assert line.endswith(" ...") and len(line) < companies.LIMIT + 40


def test_a_fresh_clone_skips_rather_than_crashing(tmp_path):
    assert companies.absent(tmp_path) == ["board.md", "apply/<company>/company.md"]
    (tmp_path / "board.md").write_text(BOARD)
    assert companies.absent(tmp_path) == ["apply/<company>/company.md"]
    write(tmp_path, "acme-health", "# A\n\n**Verdict: apply.**\n")
    assert companies.absent(tmp_path) == []
