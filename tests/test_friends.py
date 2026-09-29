"""Ranking the network so the candidate strikes names instead of recalling them."""

import datetime
from pathlib import Path

import pytest

from tools.profile import friends

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def export(monkeypatch, tmp_path):
    """The synthetic export beside the roster fixture, friends.md absent."""
    monkeypatch.setattr(friends, "EXPORT", FIXTURES / "export")
    monkeypatch.setattr(friends, "NETWORK", FIXTURES)
    monkeypatch.setattr(friends, "FRIENDS", tmp_path / "friends.md")
    return tmp_path


def printed(capsys, *argv):
    friends.main(list(argv))
    return capsys.readouterr().out.splitlines()


def test_roster_members_score_three_and_name_the_file(export, capsys):
    assert ("| Tess Marlow | Acme colleague, per roster-acme.md | 2015-03-02 "
            "| https://www.linkedin.com/in/tess-marlow |") in printed(capsys)


def scores(export):
    return {row.name: row.score for row in friends.rank()}


def test_message_conversations_count_once_and_ignore_strangers(export):
    """Sable Finch has four conversations, one of them started by the
    candidate; Mira Solano has three messages in one; Quincy Thorne writes
    five times and is not a connection."""
    scored = scores(export)
    assert scored["Sable Finch"] == 3
    assert scored["Mira Solano"] == 1
    assert "Quincy Thorne" not in scored


def hows(export):
    return {row.name: row.how for row in friends.rank()}


def test_recommendations_score_three_and_name_the_year(export):
    assert scores(export)["Orin Vale"] == 3
    assert hows(export)["Orin Vale"] == "recommended you, 2019"
    assert scores(export)["Wren Halloway"] == 3
    assert hows(export)["Wren Halloway"] == "you recommended, 2021"


def test_age_scores_nothing(export):
    """Early-career connections are a sign-up spree, so a long-standing
    connection earns no point; the first run kept 8 to 39% of connections
    from the candidate's first four working years and 31 to 77% after."""
    assert scores(export)["Ren Okafor"] == 0
    assert scores(export)["Tess Marlow"] == 3, "roster alone"


def test_employer_in_positions_scores_three(export):
    """Ada and Bo work at Lumen Ops, an employer in Positions.csv, now; Cy
    works at Marrow Bio, a past one. Ren's Fjord Inc is nobody's employer."""
    assert scores(export)["Ada Brook"] == 3
    assert hows(export)["Ada Brook"] == "Lumen Ops colleague"
    assert scores(export)["Cy Dunmore"] == 3
    assert hows(export)["Ren Okafor"] == "Fjord Inc, connected 2019"


def test_endorsements_score_two_given_and_one_received(export):
    """Two endorsements given to Dov count once; one received from Ilsa."""
    assert scores(export)["Dov Kestrel"] == 2
    assert hows(export)["Dov Kestrel"] == "you endorsed, 2018"
    assert scores(export)["Ilsa Brannock"] == 1
    assert hows(export)["Ilsa Brannock"] == "endorsed you, 2020"


def test_ties_break_by_connection_date_newest_first(export):
    """Tess, Sable, Wren, Orin and the Lumen Ops and Marrow Bio four all
    score three; within a score the newest connection comes first."""
    names = [row.name for row in friends.rank()]
    assert names[:4] == ["Dee Ellery", "Cy Dunmore", "Bo Castell", "Ada Brook"]
    assert names[4:8] == ["Orin Vale", "Wren Halloway", "Sable Finch", "Tess Marlow"]
    assert names[8:11] == ["Dov Kestrel", "Mira Solano", "Ilsa Brannock"]


def test_excludes_names_already_in_friends_md(export, capsys):
    """The header and separator rows are not names, and only the first
    column counts: a name in the how column is not a friend yet."""
    (export / "friends.md").write_text(
        "| friend | how | connected on | profile |\n|---|---|---|---|\n"
        "| Tess Marlow | Acme | 2015-03-02 | https://x |\n")
    names = [row.split(" | ")[0].strip("| ") for row in printed(capsys)]
    assert "Tess Marlow" not in names
    assert names[0] == "Dee Ellery"


def test_struck_names_stay_struck_across_runs(export, capsys):
    """A strike the candidate made once is not offered again: the Struck
    list under the table is a bullet list, so tools.profile.histories, which reads
    only table rows, never mistakes it for a friend."""
    (export / "friends.md").write_text(
        "| friend | how | connected on | profile |\n|---|---|---|---|\n"
        "| Tess Marlow | Acme | 2015-03-02 | https://x |\n\n"
        "## Struck\n\n- Sable Finch\n")
    names = [row.split(" | ")[0].strip("| ") for row in printed(capsys)]
    assert "Sable Finch" not in names
    assert "Tess Marlow" not in names


def test_batch_flag_slices_fifteen(export, capsys):
    everything = printed(capsys)
    assert len(everything) == 31
    assert printed(capsys, "--batch", "0") == everything[:15]
    assert printed(capsys, "--batch", "1") == everything[15:30]
    assert printed(capsys, "--batch", "2") == everything[30:]
    assert printed(capsys, "--batch", "3") == []


def test_size_flag_sets_the_batch_length(export, capsys):
    everything = printed(capsys)
    assert printed(capsys, "--batch", "0", "--size", "20") == everything[:20]
    assert printed(capsys, "--batch", "1", "--size", "20") == everything[20:]


def test_nameless_export_rows_are_dropped(export, capsys, monkeypatch):
    """LinkedIn blanks the name of a connection who hides their data; the
    row still carries a date and would otherwise rank among real people."""
    rows = friends.read_connections() + [{"First Name": "", "Last Name": "",
                                          "URL": "", "Company": "",
                                          "Connected On": "01 Jan 2010"}]
    monkeypatch.setattr(friends, "read_connections", lambda: rows)
    assert all(not line.startswith("|   |") for line in printed(capsys))


def test_blank_connection_date_prints_empty_and_sorts_last():
    row = friends.tally({"First Name": "No", "Last Name": "Date", "URL": "u",
                         "Company": "Zed Co", "Connected On": ""}, [])
    assert friends.line(row) == "| No Date | Zed Co |  | u |"
    assert row.connected == datetime.date.min
