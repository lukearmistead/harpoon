"""The runs index is only worth having if its counts agree with the log."""

import json

from tools.learn import runs

SWEEP = ("decision,adjudication,judge,adjudicated,shape,fix,note,company,"
         "title,location,band,url,source\n")
JUDGMENT = ("decision,why,criterion,adjudication,judge,adjudicated,shape,fix,"
            "note,company,title,url\n")
KEPT = "kept,,,,,,,Lumen Ops,Staff Data Scientist,San Francisco,,,hn\n"
GRADED = ("kept,reject,a model,2026-09-17,band-floor,source/gates.md,,"
          "Marrow Bio,Staff Scientist,San Francisco,,,hn\n")


def write_run(root, name, meta=None, sweep=None, judgment=None):
    run = root / "learn/runs" / name
    run.mkdir(parents=True)
    (run / "run.json").write_text(json.dumps({"run": name} | (meta or {})))
    if sweep:
        (run / "sweep.csv").write_text(sweep)
    if judgment:
        (run / "judgment.csv").write_text(judgment)
    return run


def table(out):
    return [line for line in out.splitlines() if line.startswith("| [")]


def test_newest_run_comes_first(tmp_path):
    write_run(tmp_path, "2026-09-15T134000", {"mode": "sweep"})
    write_run(tmp_path, "2026-09-16T192255", {"mode": "audit"})
    assert table(runs.build(tmp_path))[0].startswith("| [2026-09-16T192255]")


def test_only_a_filled_adjudication_cell_counts(tmp_path):
    """The number here has to match `python3 -m tools.source.sweep grades`,
    which reads the adjudication cell and none of the other grading columns."""
    write_run(tmp_path, "2026-09-16T192255", {"mode": "sweep"},
              sweep=SWEEP + KEPT + GRADED)
    assert table(runs.build(tmp_path))[0].endswith("| 2 | 1 |")


def test_a_judgment_row_counts_beside_the_sweep_rows(tmp_path):
    """A run records decisions in two files and the row is about the run."""
    write_run(tmp_path, "2026-09-16T192255", {"mode": "sweep"},
              sweep=SWEEP + KEPT,
              judgment=JUDGMENT + "reject,too junior,seniority,reject,a model,"
                                  "2026-09-17,band-floor,,,Marrow Bio,Staff,\n")
    assert table(runs.build(tmp_path))[0].endswith("| 2 | 1 |")


def test_a_sweep_run_nobody_has_graded_yet_prints_a_zero(tmp_path):
    """The ordinary case: a run written today, no judgment.csv beside it and
    no grades in it. The last cell is a zero rather than a blank, because a
    blank reads as unknown and this is a known nothing."""
    write_run(tmp_path, "2026-09-29T073725",
              {"mode": "sweep", "started": "2026-09-29T07:37:25",
               "channels": {"Lumen Ops": 12, "Marrow Bio": 0}},
              sweep=SWEEP + KEPT)
    assert table(runs.build(tmp_path)) == [
        "| [2026-09-29T073725](2026-09-29T073725/run.json) | sweep "
        "| 2026-09-29 | 2 | 1 | 0 |"]


def test_a_channel_that_returned_nothing_is_still_a_channel(tmp_path):
    """`-` and `0` say different things: a run that read no channels at all,
    and a channel that was read and had no postings in it."""
    write_run(tmp_path, "2026-09-16T192255",
              {"mode": "sweep", "channels": {"Lumen Ops": 0}})
    write_run(tmp_path, "2026-09-15T134000", {"mode": "sweep"})
    rows = table(runs.build(tmp_path))
    assert "| sweep | 2026-09-16 | 1 |" in rows[0]
    assert "| sweep | 2026-09-15 | - |" in rows[1]


def test_a_directory_with_no_run_json_is_not_a_run(tmp_path):
    """run.json is written last, so a directory without one is a run that is
    still being written or one that died partway."""
    write_run(tmp_path, "2026-09-16T192255", {"mode": "sweep"})
    (tmp_path / "learn/runs/2026-09-17T090000").mkdir()
    assert len(table(runs.build(tmp_path))) == 1


def test_the_prose_above_the_markers_survives_a_rewrite(tmp_path):
    write_run(tmp_path, "2026-09-16T192255", {"mode": "sweep"})
    index = tmp_path / "learn/runs/index.md"
    index.write_text("# Runs\n\nA sentence somebody wrote.\n\n"
                     "<!-- index:start -->\nout of date\n<!-- index:end -->\n")
    out = runs.render(tmp_path)
    assert "A sentence somebody wrote." in out
    assert "out of date" not in out


def test_an_instance_with_no_runs_needs_no_index(tmp_path):
    """The template ships the directory empty, and a check demanding an index
    of nothing would block the first commit anyone makes in a fresh clone."""
    (tmp_path / "learn/runs").mkdir(parents=True)
    assert not runs.wanted_here(tmp_path)
    (tmp_path / "learn/runs/index.md").write_text("")
    assert runs.wanted_here(tmp_path), "an index that exists stays checked"
