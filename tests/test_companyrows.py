"""The `## Companies` table against the board and the rejection log."""

import pytest

from tools.core.contract import Lead
from tools.source import companyrows, sweep

BOARD = "## Board\n\n| Company | Status |\n|---|---|\n"
CHANNELS = ("## Catalog\n\n| Channel | Endpoint | Works from |\n|---|---|---|\n"
            "\n## Companies\n\n"
            "| Company | Endpoint | A posting matters when | Notes |\n"
            "|---|---|---|---|\n")
LOG = "# Swept and rejected\n\n### 2026-09-04\n\n"


def logged(repo, entries):
    """The rejection log, which lives in its own file rather than on the board:
    a dated `###` block sits inside it and must not end the read of it."""
    repo.write("learn/rejections.md", LOG + entries)


def test_a_rejected_row_with_no_company_row_is_named(repo):
    repo.write("board.md", BOARD + "| Vercel | rejected |\n")
    repo.write("source/channels.md", CHANNELS)
    assert companyrows.check(repo.root) == [
        "board.md: Vercel is `rejected` with no row in source/channels.md's "
        "`## Companies` table"]


def test_a_passed_row_is_closed_too(repo):
    repo.write("board.md", BOARD + "| Nuna | passed |\n")
    repo.write("source/channels.md", CHANNELS)
    assert len(companyrows.check(repo.root)) == 1


def test_a_row_in_the_table_answers_the_board(repo):
    repo.write("board.md", BOARD + "| Vercel | rejected |\n| Nuna | passed |\n")
    repo.write("source/channels.md", CHANNELS
               + "| Vercel | | `never` | no operator whose work he would measure |\n"
               + "| Nuna | | | the seat was below the floor |\n")
    assert companyrows.check(repo.root) == []


def test_a_board_row_that_says_watch_is_named(repo):
    """Watching moved into the table on 2026-09-27, because a board row is one
    company and one seat and a watched company has no seat."""
    repo.write("board.md", BOARD + "| Waymark | watch |\n")
    repo.write("source/channels.md", CHANNELS)
    problem, = companyrows.check(repo.root)
    assert "Waymark is `watch`" in problem


def test_a_table_row_does_not_excuse_a_watch_status(repo):
    repo.write("board.md", BOARD + "| Waymark | watch |\n")
    repo.write("source/channels.md", CHANNELS
               + "| Waymark | `greenhouse:waymark` | | 21 postings |\n")
    assert len(companyrows.check(repo.root)) == 1


def test_every_other_status_is_left_alone(repo):
    repo.write("board.md", BOARD + "| Waymark | lead |\n| Honor | applied |\n")
    repo.write("source/channels.md", CHANNELS)
    assert companyrows.check(repo.root) == []


def test_one_row_carries_both_a_fetch_and_a_condition(repo):
    """What replaced the two tables. Rad AI sat in both, watched at `band > 260`
    and closed at `band > 260`, and a check existed to keep the pair equal.
    Here the endpoint says it is fetched and the condition says what would
    matter, which is the whole of what the two rows were saying."""
    repo.write("board.md", BOARD + "| Rad AI | passed |\n")
    repo.write("source/channels.md", CHANNELS
               + "| Rad AI | `ashby:radai` | `band > 260` | demoted on peer band |\n")
    assert companyrows.check(repo.root) == []
    assert companyrows.fetched(CHANNELS + "| Rad AI | `ashby:radai` | | x |\n") \
        == {"radai"}


def test_a_row_with_no_endpoint_is_not_fetched(repo):
    channels = CHANNELS + "| Vercel | | `never` | no operator |\n"
    assert companyrows.fetched(channels) == set()


def test_a_bolded_name_in_the_log_is_a_closed_company(repo):
    repo.write("board.md", BOARD)
    logged(repo, "- **Vercel**. No operator here.\n")
    repo.write("source/channels.md", CHANNELS)
    assert companyrows.check(repo.root) == [
        "learn/rejections.md names Vercel, which has no row in "
        "source/channels.md's `## Companies` table"]


def test_a_bolded_opener_that_runs_into_prose_is_cut_back_to_the_company(repo):
    repo.write("board.md", BOARD)
    logged(repo, "- **Cresta. Came back 2026-09-11 and is in Working now.**\n")
    repo.write("source/channels.md", CHANNELS)
    assert "names Cresta," in companyrows.check(repo.root)[0]


def test_a_sentence_bolded_in_the_log_is_not_a_company(repo):
    """Entries open with a bolded sentence about the market as well as with a
    name, and a sentence is not a company to demand a row for."""
    repo.write("board.md", BOARD)
    logged(repo, "- **The Applied AI Architect family is settled at both "
                 "labs, and it fails.** Every one of them is a delivery seat.\n")
    repo.write("source/channels.md", CHANNELS)
    assert companyrows.check(repo.root) == []


def test_a_bolded_name_with_a_board_row_is_answered_by_that_row(repo):
    """Anthropic is still bolded in the log and still being worked, so the
    board's own status decides, and it is not asked for twice."""
    repo.write("board.md", BOARD + "| Anthropic | lead |\n")
    logged(repo, "- **Anthropic** has no health footprint.\n")
    repo.write("source/channels.md", CHANNELS)
    assert companyrows.check(repo.root) == []


def test_an_empty_table_is_not_itself_a_failure(repo):
    repo.write("board.md", BOARD + "| Waymark | lead |\n")
    repo.write("source/channels.md", CHANNELS)
    assert companyrows.check(repo.root) == []


def test_a_condition_the_watch_language_cannot_read_fails_here_first(repo):
    """meets() raises on a term it cannot parse and the sweep is where that
    lands, so one cell of prose would end a run before it printed anything.
    A failed commit is the cheaper place to find out."""
    repo.write("board.md", BOARD)
    repo.write("source/channels.md", CHANNELS
               + "| Omni | | `stack ~ python` | no Python seat |\n")
    problem, = companyrows.check(repo.root)
    assert "Omni's condition reads 'stack ~ python'" in problem


def test_a_broken_regex_is_caught_as_well_as_broken_prose(repo):
    """A bad pattern raises re.error, which is not a ValueError, so catching
    the one the term parser raises would have let this through."""
    repo.write("board.md", BOARD)
    repo.write("source/channels.md", CHANNELS
               + "| Omni | | `title ~ staff(` | no Python seat |\n")
    problem, = companyrows.check(repo.root)
    assert "title ~ staff(" in problem


def test_a_malformed_condition_would_have_crashed_the_gate():
    """Why the check exists rather than a rescue inside the gate: swallowing
    this would reopen the company silently, which is the failure the whole
    conditional gate is built to avoid."""
    channels = CHANNELS + "| Acme Health | | `stack ~ python` | no seat |\n"
    ctx = {"companies": sweep.company_criteria(channels, []), "decided": set()}
    posting = Lead(company="Acme Health", title="Staff ML Engineer",
                   location="Remote", band=None, url=None, source="test")
    with pytest.raises(ValueError):
        sweep.criterion_miss(posting, ctx)


def test_never_and_an_empty_cell_never_reach_the_parser(repo):
    repo.write("board.md", BOARD)
    repo.write("source/channels.md", CHANNELS
               + "| Vercel | | `never` | no operator |\n"
               + "| Arintra | | | when a seat exists |\n")
    assert companyrows.check(repo.root) == []


def test_a_fresh_instance_with_neither_file_is_quiet(repo):
    """Both files are written per instance, so a clone of the template has
    neither, and a check that fails there gets ignored everywhere."""
    repo.write("AGENTS.md", "a decided company says what would reopen it\n")
    assert companyrows.check(repo.root) == []


def test_a_problem_exits_non_zero(repo, monkeypatch, capsys):
    repo.write("board.md", BOARD + "| Vercel | rejected |\n")
    repo.write("source/channels.md", CHANNELS)
    monkeypatch.setattr(companyrows, "ROOT", repo.root)
    with pytest.raises(SystemExit):
        companyrows.main()
    assert "Vercel" in capsys.readouterr().out


def test_the_log_s_full_name_is_the_board_s_short_one(repo):
    """The log writes `Apella Health` where the board writes `Apella`, and
    writing it a closed row would shut a company somebody is watching."""
    repo.write("board.md", BOARD + "| Apella | lead |\n")
    logged(repo, "- **Apella Health**, from Sable Finch. Fully remote.\n")
    repo.write("source/channels.md", CHANNELS)
    assert companyrows.check(repo.root) == []


def test_a_cataloged_company_with_no_board_row_is_not_closed(repo):
    """A catalog row is somebody watching, which the board cannot say when the
    company has no row on it at all."""
    repo.write("board.md", BOARD)
    logged(repo, "- **EliseAI**. Both seats are wrong.\n")
    repo.write("source/channels.md",
               "## Catalog\n\n| Channel | Endpoint | Works from |\n|---|---|---|\n"
               "| EliseAI | `ashby:eliseai` | their own board |\n"
               "\n## Companies\n\n"
               "| Company | Endpoint | A posting matters when | Notes |\n"
               "|---|---|---|---|\n")
    assert companyrows.check(repo.root) == []


def test_a_sentence_that_fits_a_name_s_length_is_not_a_name(repo):
    """`Lumenai is Luminai` survives the four-word cut and is still prose."""
    repo.write("board.md", BOARD)
    logged(repo, "- **Lumenai is Luminai**, already on the board, and stale.\n")
    repo.write("source/channels.md", CHANNELS)
    assert companyrows.check(repo.root) == []


def test_a_parenthetical_alias_is_asked_about_once(repo):
    """No job board returns `Superhuman (Grammarly)`, so the row carries the
    name a board would return and the alias lives in its sentence."""
    repo.write("board.md", BOARD)
    logged(repo, "- **Superhuman (Grammarly)**. A wrapper.\n")
    repo.write("source/channels.md", CHANNELS
               + "| Superhuman | | `never` | no operator, and Grammarly bought them |\n")
    assert companyrows.check(repo.root) == []


def test_a_cataloged_name_comes_back_spelled_as_the_file_spells_it():
    """Normalizing first and slugging after gives `anglehealth`, which matches
    no directory, and that reported four watched companies as gaps."""
    channels = CHANNELS + "| Angle Health | `ashby:anglehealth` | | 1 posting |\n"
    assert "Angle Health" in companyrows.cataloged_names(channels)
    assert "anglehealth" in companyrows.cataloged(channels)


def test_a_linked_company_name_is_read_as_the_company(repo):
    repo.write("board.md",
               BOARD + "| [Waymark](apply/waymark/company.md) | watch |\n")
    repo.write("source/channels.md", CHANNELS)
    problem, = companyrows.check(repo.root)
    assert "Waymark is `watch`" in problem
