"""The sitting's batch and the employer list, read from the repo's own markdown."""

import pytest

from tools.profile import histories
from tools.source import sweep

FRIENDS = ("# Friends\n\n| friend | how | connected on | profile |\n|---|---|---|---|\n"
           "| Ada Quill | roster | 2019-03-14 | linkedin.com/in/ada-quill |\n"
           "| Bo Farrow | messages | 2020-01-02 | linkedin.com/in/bo-farrow |\n"
           "| Cy Lund | endorsed | 2021-05-06 | linkedin.com/in/cy-lund |\n")


def section(name, date, rows):
    table = "".join(f"| {c} | {t} | {f} | {to} |\n" for c, t, f, to in rows)
    return (f"## {name}, read {date}, ten years\n\nlinkedin.com/in/x, connected 2017-06-08\n\n"
            f"| company | title | from | to |\n|---|---|---|---|\n{table}\n")


def seed(tmp_path, monkeypatch, histories_text=None, board=""):
    (tmp_path / "profile/network").mkdir(parents=True)
    (tmp_path / "profile/network/friends.md").write_text(FRIENDS)
    if histories_text is not None:
        (tmp_path / "profile/network/histories.md").write_text(histories_text)
    (tmp_path / "board.md").write_text(board)
    (tmp_path / "apply").mkdir()
    monkeypatch.setattr(sweep, "ROOT", tmp_path)
    monkeypatch.setattr(histories, "FRIENDS", tmp_path / "profile/network/friends.md")
    monkeypatch.setattr(histories, "HISTORIES", tmp_path / "profile/network/histories.md")


def test_next_skips_friends_already_read(tmp_path, monkeypatch, capsys):
    """Order is friends.md order and the size caps the batch, so the three
    clauses of the batch rule are one test."""
    seed(tmp_path, monkeypatch, section("Bo Farrow", "2001-01-01",
                                        [("Acme", "Eng", "2010-01", "now")]))
    histories.main(["next", "--size", "1"], today="2026-09-21")
    assert capsys.readouterr().out == "Ada Quill linkedin.com/in/ada-quill\n"
    histories.main(["next"], today="2026-09-21")
    assert capsys.readouterr().out == ("Ada Quill linkedin.com/in/ada-quill\n"
                                       "Cy Lund linkedin.com/in/cy-lund\n")


def test_next_refuses_a_second_sitting_today(tmp_path, monkeypatch, capsys):
    seed(tmp_path, monkeypatch, section("Bo Farrow", "2026-09-21",
                                        [("Acme", "Eng", "2010-01", "now")]))
    with pytest.raises(SystemExit) as stop:
        histories.main(["next"], today="2026-09-21")
    assert stop.value.code == ("a sitting already happened today "
                               "(Bo Farrow, read 2026-09-21); one a day")
    assert capsys.readouterr().out == ""


def test_next_with_no_histories_file_lists_everyone(tmp_path, monkeypatch, capsys):
    """No histories.md means nobody has been read, which is where every
    instance starts, not an error."""
    seed(tmp_path, monkeypatch)
    histories.main(["next"], today="2026-09-21")
    assert capsys.readouterr().out.splitlines() == [
        "Ada Quill linkedin.com/in/ada-quill", "Bo Farrow linkedin.com/in/bo-farrow",
        "Cy Lund linkedin.com/in/cy-lund"]


def test_next_skips_a_friend_with_no_profile(tmp_path, monkeypatch, capsys):
    """A friend added by name with no export row has no page to load, so the
    batch leaves them out."""
    seed(tmp_path, monkeypatch)
    (tmp_path / "profile/network/friends.md").write_text(
        FRIENDS + "| Nobody Here | outside work |  |  |\n")
    histories.main(["next"], today="2026-09-21")
    assert capsys.readouterr().out.splitlines() == [
        "Ada Quill linkedin.com/in/ada-quill", "Bo Farrow linkedin.com/in/bo-farrow",
        "Cy Lund linkedin.com/in/cy-lund"]


def test_employers_drops_decided_companies_and_groups_friends(tmp_path, monkeypatch, capsys):
    """Two friends at Northwind under two spellings are one row with two
    friends; Acme is on the board and Dovetail has an apply/ directory, so
    neither is printed. Most friends first, then by name."""
    seed(tmp_path, monkeypatch,
         section("Ada Quill", "2001-01-01", [("Acme", "Eng", "2010-01", "now"),
                                            ("Northwind", "PM", "2005-02", "2010-01")])
         + section("Bo Farrow", "2001-01-02", [("Zephyr", "Eng", "2012-01", "now"),
                                              ("northwind", "Eng", "2008-03", "2012-01")])
         + section("Cy Lund", "2001-01-03", [("Dovetail", "Eng", "2015-01", "now")]),
         board="| Company | Stage |\n|---|---|\n| Acme | applied |\n")
    (tmp_path / "apply/dovetail").mkdir()
    histories.main(["employers"])
    assert capsys.readouterr().out.splitlines() == [
        "| Northwind | Ada Quill (2005-02 to 2010-01); Bo Farrow (2008-03 to 2012-01) |",
        "| Zephyr | Bo Farrow (2012-01 to now) |"]
