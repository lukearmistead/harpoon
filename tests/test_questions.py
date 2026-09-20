"""The questions only the candidate can answer, and the page he reads."""

import pytest

from tools import questions


def test_a_tagged_question_must_reach_the_board(repo):
    repo.write("board.md", "## Todo\n\n- nothing here\n")
    repo.write("profile/experience.md", "Six years or seven? [ask: Tenure]\n")
    assert questions.check(repo.root) == [
        "profile/experience.md:1: [ask: Tenure] reaches no line in board.md"]


def test_a_key_on_the_board_is_answered_whatever_its_case(repo):
    """The board says it in a sentence; the marker says it in one word."""
    repo.write("board.md", "- confirm the tenure figure with his manager\n")
    repo.write("profile/experience.md", "[ask: Tenure]\n")
    assert questions.check(repo.root) == []


def test_a_placeholder_is_not_a_question(repo):
    """`[ask: <Key>]` names the shape the marker takes."""
    repo.write("board.md", "## Todo\n")
    repo.write("AGENTS.md", "tag it `[ask: <Key>]` and put it on the board\n")
    assert questions.check(repo.root) == []


def test_the_board_does_not_ask_itself(repo):
    repo.write("board.md", "- [ask: Tenure] is his to answer\n")
    assert questions.check(repo.root) == []


def test_two_markers_on_one_line_are_two_questions(repo):
    repo.write("board.md", "## Todo\n")
    repo.write("profile/experience.md", "[ask: Tenure] and [ask: Band]\n")
    assert len(questions.check(repo.root)) == 2


def test_a_fresh_instance_with_no_board_is_quiet(repo):
    """The template ships the rules without the board, so a clone of it has
    every marker and no page to check them against."""
    repo.write("AGENTS.md", "tag it and put it on the board\n")
    assert questions.check(repo.root) == []


def test_an_unseen_question_exits_non_zero(repo, monkeypatch, capsys):
    repo.write("board.md", "## Todo\n")
    repo.write("profile/experience.md", "[ask: Tenure]\n")
    monkeypatch.setattr(questions, "ROOT", repo.root)
    with pytest.raises(SystemExit):
        questions.main()
    assert "[ask: Tenure]" in capsys.readouterr().out
