"""A `watch` row on the board against the channel that does the watching."""

import pytest

from tools import watchrows

BOARD = "| Company | Status |\n|---|---|\n"
CHANNELS = "| Channel | Endpoint | Works from |\n|---|---|---|\n"


def test_a_watch_row_with_no_channel_is_named(repo):
    repo.write("board.md", BOARD + "| Waymark | watch |\n")
    repo.write("source/channels.md", CHANNELS)
    assert watchrows.check(repo.root) == [
        "board.md: Waymark is `watch` with no row in source/channels.md"]


def test_a_channel_row_of_any_kind_is_a_watcher(repo):
    """A fetcher watches it and so does a person opening the page by hand."""
    repo.write("board.md", BOARD + "| Waymark | watch |\n| Claimable | watch |\n")
    repo.write("source/channels.md", CHANNELS
               + "| Waymark | `greenhouse:waymark` | 21 postings |\n"
               + "| Claimable | https://getclaimable.com/careers | Webflow, no ATS |\n")
    assert watchrows.check(repo.root) == []


def test_a_company_spelled_two_ways_is_still_one_company(repo):
    """The sweep matches names through contract.norm, so this does too:
    punctuation on one side of the pair is not a blind watch."""
    repo.write("board.md", BOARD + "| Acme, Inc. | watch |\n")
    repo.write("source/channels.md", CHANNELS + "| Acme Inc | `ashby:acme` | 4 postings |\n")
    assert watchrows.check(repo.root) == []


def test_a_merged_row_passes_on_either_half(repo):
    """The row names two companies; a channel on one of them is a real
    watcher on that half, and the row's own cell says which is blind."""
    repo.write("board.md", BOARD + "| Honor / Waymark | watch |\n")
    repo.write("source/channels.md", CHANNELS + "| Honor | `greenhouse:honor` | 17 postings |\n")
    assert watchrows.check(repo.root) == []


def test_a_linked_company_name_is_read_as_the_company(repo):
    repo.write("board.md", BOARD + "| [Waymark](apply/waymark/company.md) | watch |\n")
    repo.write("source/channels.md", CHANNELS + "| Waymark | `greenhouse:waymark` | 21 |\n")
    assert watchrows.check(repo.root) == []


def test_every_other_status_is_left_alone(repo):
    repo.write("board.md", BOARD + "| Waymark | lead |\n| Honor | applied |\n")
    repo.write("source/channels.md", CHANNELS)
    assert watchrows.check(repo.root) == []


def test_a_fresh_instance_with_neither_file_is_quiet(repo):
    """Both files are written per instance, so a clone of the template has
    neither, and a check that fails there gets ignored everywhere."""
    repo.write("AGENTS.md", "the board delegates a company to the sweep\n")
    assert watchrows.check(repo.root) == []


def test_an_unwatched_row_exits_non_zero(repo, monkeypatch, capsys):
    repo.write("board.md", BOARD + "| Waymark | watch |\n")
    repo.write("source/channels.md", CHANNELS)
    monkeypatch.setattr(watchrows, "ROOT", repo.root)
    with pytest.raises(SystemExit):
        watchrows.main()
    assert "Waymark" in capsys.readouterr().out
