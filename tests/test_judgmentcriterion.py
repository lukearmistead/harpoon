"""A verdict in the newest run against the criteria bullet it says decided it."""

import pytest

from tools.learn import judgmentcriterion

HEADER = "decision,why,criterion,company,title,url\n"
OLD_HEADER = "decision,why,company,title,url\n"


def judgment(repo, run, body, header=HEADER):
    return repo.write(f"learn/runs/{run}/judgment.csv", header + body)


def test_a_verdict_with_no_criterion_is_named(repo):
    judgment(repo, "2026-09-27T071613",
             "reject,the office line,,Waymark,Staff ML Engineer,https://x/1\n")
    assert judgmentcriterion.check(repo.root) == [
        "learn/runs/2026-09-27T071613/judgment.csv: verdict 1 (Waymark) is "
        "`reject` with no criterion"]


def test_a_filled_criterion_passes(repo):
    judgment(repo, "2026-09-27T071613",
             "reject,the office line,\"$200K floor, Firm\","
             "Waymark,Staff ML Engineer,https://x/1\n")
    assert judgmentcriterion.check(repo.root) == []


def test_a_blank_company_still_names_the_row(repo):
    """Some rows carry no company at all, and a problem line naming nothing
    cannot be acted on."""
    judgment(repo, "2026-09-27T071613", "reject,,,,,\n")
    assert judgmentcriterion.check(repo.root) == [
        "learn/runs/2026-09-27T071613/judgment.csv: verdict 1 (no company) is "
        "`reject` with no criterion"]


def test_a_row_with_no_decision_is_left_alone(repo):
    """A row nobody ruled on has nothing to name a criterion for."""
    judgment(repo, "2026-09-27T071613", ",,,Waymark,Staff ML Engineer,https://x/1\n")
    assert judgmentcriterion.check(repo.root) == []


def test_a_run_whose_header_predates_the_column_is_left_alone(repo):
    """Every run before the column exists has none, and no grep will ever fill
    those in."""
    judgment(repo, "2026-09-27T071613",
             "reject,the office line,Waymark,Staff ML Engineer,https://x/1\n",
             header=OLD_HEADER)
    assert judgmentcriterion.check(repo.root) == []


def test_only_the_newest_run_is_read(repo):
    """The newest run is the one being written now; an older one is history."""
    judgment(repo, "2026-09-25T114356", "reject,the office line,,Honor,Staff DS,\n")
    judgment(repo, "2026-09-27T071613",
             "reject,the office line,\"$200K floor, Firm\",Waymark,Staff ML,\n")
    assert judgmentcriterion.check(repo.root) == []


def test_a_run_with_only_a_sweep_file_is_not_a_gap(repo):
    """The judgment pass is a person, and a sweep whose survivors nobody ruled
    on is what reconcile reports."""
    repo.write("learn/runs/2026-09-27T071613/sweep.csv", "decision,company\n")
    assert judgmentcriterion.check(repo.root) == []


def test_a_fresh_instance_with_no_runs_is_quiet(repo):
    """The run log is written per instance, so a clone of the template has
    none, and a check that fails there gets ignored everywhere."""
    repo.write("AGENTS.md", "one directory per run, never exported\n")
    assert judgmentcriterion.check(repo.root) == []


def test_a_fresh_instance_says_it_skipped(repo, monkeypatch, capsys):
    repo.write("AGENTS.md", "one directory per run, never exported\n")
    monkeypatch.setattr(judgmentcriterion, "ROOT", repo.root)
    judgmentcriterion.main()
    assert "skipped" in capsys.readouterr().out


def test_a_verdict_with_no_criterion_exits_non_zero(repo, monkeypatch, capsys):
    judgment(repo, "2026-09-27T071613",
             "reject,the office line,,Waymark,Staff ML Engineer,https://x/1\n")
    monkeypatch.setattr(judgmentcriterion, "ROOT", repo.root)
    with pytest.raises(SystemExit):
        judgmentcriterion.main()
    assert "Waymark" in capsys.readouterr().out
