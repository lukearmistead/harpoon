"""Verdicts worth a second look, against the three reasons one can be."""

import json

from tools.source import rejudge

CRITERIA = """# Criteria

## Labels

- **Firm** fails a role on its own.

## Role

- **Strong:** Modeling with a human in the loop, and the operator is a clinician.
- **Strong:** My range is the full data product, across disciplines.

## Title & Salary

- **Firm:** $200K floor. The band's top clears it comfortably.
- **Strong:** At or above my level of staff, IC.
"""

BOARD = "## Board\n\n| Company | Status |\n|---|---|\n"
SWEEP = ("decision,company,title,location,band,url,source\n"
         "kept,Acme,Staff ML Engineer,San Francisco,$250-400K,http://a,hn\n")


def run(repo, name, mode, rows, criteria_commit="old", judgment=None):
    repo.write(f"learn/runs/{name}/sweep.csv", rows)
    repo.write(f"learn/runs/{name}/run.json", json.dumps(
        {"mode": mode, "revision": {"criteria_commit": criteria_commit}}))
    if judgment is not None:
        repo.write(f"learn/runs/{name}/judgment.csv", judgment)


def judged(decision="reject", criterion="", why="", company="Acme"):
    return ("decision,why,criterion,company,title,url\n"
            f"{decision},\"{why}\",\"{criterion}\",{company},Staff ML Engineer,http://a\n")


def test_the_floor_comes_from_the_candidate_s_own_file():
    assert rejudge.criteria_floor(CRITERIA) == 200_000


def test_a_file_stating_no_floor_bounds_nothing():
    """Every other instance of the template has a different number or none, so
    a default here would be wrong for all of them."""
    assert rejudge.criteria_floor("# Criteria\n\n- **Firm:** no contract work\n") is None


def test_a_verdict_can_rest_on_more_than_one_rule():
    assert rejudge.pairs("the seat, Strong; the model, Strong") == [
        ("the seat", "Strong"), ("the model", "Strong")]


def test_one_strong_alone_is_a_verdict_criteria_does_not_allow():
    assert rejudge.rests_on_one_strong("at or above my level of staff, Strong")


def test_two_strongs_together_are_allowed_and_not_flagged():
    """Criteria says two or three sink a role when the verdict says so."""
    assert not rejudge.rests_on_one_strong("the seat, Strong; the moat, Strong")


def test_a_firm_miss_is_never_flagged():
    assert not rejudge.rests_on_one_strong("$200K floor, Firm")


def test_a_role_bullet_is_the_thesis_and_does_not_come_back():
    bullets = rejudge.thesis_bullets(CRITERIA)
    assert rejudge.is_thesis("Modeling with a human in the loop, Strong", bullets)


def test_a_salary_bullet_is_a_fact_about_today():
    bullets = rejudge.thesis_bullets(CRITERIA)
    assert not rejudge.is_thesis("$200K floor, Firm", bullets)


def test_one_bullet_outside_the_thesis_is_enough_to_re_read():
    """A verdict resting on the thesis and on a band is still worth a look,
    because the band is the half that can have moved."""
    bullets = rejudge.thesis_bullets(CRITERIA)
    assert not rejudge.is_thesis(
        "Modeling with a human in the loop, Strong; $200K floor, Firm", bullets)


def test_the_posting_read_first_is_the_one_topping_highest():
    postings = [{"band": "$150-220K"}, {"band": "$180-400K"}]
    assert rejudge.worth_reading(postings, 200_000)["band"] == "$180-400K"


def test_a_band_below_the_floor_is_not_worth_reading():
    assert rejudge.worth_reading([{"band": "$90-150K"}], 200_000) is None


def test_an_unposted_band_is_not_a_known_miss():
    assert rejudge.worth_reading([{"band": ""}], 200_000) is not None


def test_a_company_somebody_is_working_is_left_alone():
    assert not rejudge.open_company("acme", {"Acme": "applied"})


def test_a_company_with_no_row_at_all_is_open():
    assert rejudge.open_company("acme", {"Nuna": "passed"})


def test_a_reject_on_one_strong_with_a_live_posting_is_listed(repo):
    repo.write("profile/criteria.md", CRITERIA)
    repo.write("board.md", BOARD)
    run(repo, "2026-09-01T000000", "audit", SWEEP)
    run(repo, "2026-09-02T000000", "sweep", SWEEP,
        judgment=judged(criterion="at or above my level of staff, Strong"))
    (stale, strong, reasonless), audit, floor, _ = rejudge.candidates(repo.root)
    assert [r[1]["company"] for r in strong] == ["Acme"]
    assert (stale, reasonless, audit, floor) == ([], [], "2026-09-01T000000", 200_000)


def test_a_verdict_with_nothing_written_down_is_its_own_section(repo):
    repo.write("profile/criteria.md", CRITERIA)
    repo.write("board.md", BOARD)
    run(repo, "2026-09-01T000000", "audit", SWEEP)
    run(repo, "2026-09-02T000000", "sweep", SWEEP, judgment=judged())
    _, _, reasonless = rejudge.candidates(repo.root)[0]
    assert [r[1]["company"] for r in reasonless] == ["Acme"]


def test_a_thesis_verdict_under_older_rules_is_not_queued(repo):
    """Failing the operator test is about what he is for, so re-reading it
    would reach the same answer."""
    repo.write("profile/criteria.md", CRITERIA)
    repo.write("board.md", BOARD)
    run(repo, "2026-09-01T000000", "audit", SWEEP)
    run(repo, "2026-09-02T000000", "sweep", SWEEP, judgment=judged(
        criterion="Modeling with a human in the loop, Strong; "
                  "My range is the full data product, Strong"))
    stale, strong, reasonless = rejudge.candidates(repo.root)[0]
    assert (stale, strong, reasonless) == ([], [], [])


def test_a_company_with_no_live_posting_is_not_queued(repo):
    repo.write("profile/criteria.md", CRITERIA)
    repo.write("board.md", BOARD)
    run(repo, "2026-09-01T000000", "audit",
        "decision,company,title,location,band,url,source\n")
    run(repo, "2026-09-02T000000", "sweep", SWEEP, judgment=judged())
    assert rejudge.candidates(repo.root)[0] == ([], [], [])


def test_a_posting_the_audit_dropped_at_a_gate_is_not_a_comeback(repo):
    """A title the gate threw out is not a seat coming back, so it must not
    put its company on the worklist."""
    repo.write("profile/criteria.md", CRITERIA)
    repo.write("board.md", BOARD)
    run(repo, "2026-09-01T000000", "audit",
        "decision,company,title,location,band,url,source\n"
        "title-class,Acme,Nurse Practitioner,San Francisco,$250-400K,http://a,hn\n")
    run(repo, "2026-09-02T000000", "sweep", SWEEP, judgment=judged())
    assert rejudge.candidates(repo.root)[0] == ([], [], [])


def test_no_run_log_at_all_says_so_rather_than_failing(repo, capsys):
    rejudge.report(repo.root)
    assert "skipped" in capsys.readouterr().out


def test_a_company_judged_twice_reports_only_its_newest_verdict(repo):
    """A re-judgment is the fix, so the row it replaced must not stay on the
    worklist: 26 companies got a reason and the list would have grown by 26."""
    repo.write("profile/criteria.md", CRITERIA)
    repo.write("board.md", BOARD)
    run(repo, "2026-09-01T000000", "audit", SWEEP)
    run(repo, "2026-09-02T000000", "sweep", SWEEP, judgment=judged())
    run(repo, "2026-09-03T000000-rejudgment", "sweep", SWEEP, judgment=judged(
        why="the operator is a developer", criterion="the seat, Firm"))
    _, _, reasonless = rejudge.candidates(repo.root)[0]
    assert reasonless == []


def test_a_near_miss_on_one_strong_is_correct_and_not_flagged(repo):
    """A Strong that does not fail a role alone is exactly what a near miss
    records, so only a decision that closed the company belongs in that
    section."""
    repo.write("profile/criteria.md", CRITERIA)
    repo.write("board.md", BOARD)
    run(repo, "2026-09-01T000000", "audit", SWEEP)
    run(repo, "2026-09-02T000000", "sweep", SWEEP, judgment=judged(
        decision="near-miss", criterion="at or above my level of staff, Strong"))
    assert rejudge.candidates(repo.root)[0] == ([], [], [])


def test_the_best_paying_seat_is_listed_first(repo):
    repo.write("profile/criteria.md", CRITERIA)
    repo.write("board.md", BOARD)
    run(repo, "2026-09-01T000000", "audit",
        "decision,company,title,location,band,url,source\n"
        "kept,Acme,Staff ML Engineer,SF,$200-260K,http://a,hn\n"
        "kept,Nuna,Staff ML Engineer,SF,$300-450K,http://n,hn\n")
    run(repo, "2026-09-02T000000", "sweep", SWEEP,
        judgment=("decision,why,criterion,company,title,url\n"
                  "reject,,,Acme,Staff ML Engineer,http://a\n"
                  "reject,,,Nuna,Staff ML Engineer,http://n\n"))
    _, _, reasonless = rejudge.candidates(repo.root)[0]
    assert [r[1]["company"] for r in reasonless] == ["Nuna", "Acme"]
