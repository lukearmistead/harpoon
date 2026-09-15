"""The pipeline around the fetchers: catalog, dedupe, filters, digest."""

import json

from harpoon import sweep
from harpoon.contract import Lead


def lead(**kw):
    base = dict(company="Acme Health", title="Staff ML Engineer",
                location="San Francisco", band=None,
                url="https://x.com/1", source="test")
    return Lead(**{**base, **kw})


def test_catalog_reads_endpoint_cells(tmp_path, monkeypatch):
    (tmp_path / "me").mkdir()
    (tmp_path / "me/channels.md").write_text(
        "| Channel | Endpoint | Works from |\n|---|---|---|\n"
        "| HN hiring | `hn:whoishiring` | monthly thread |\n"
        "| GV | `consider:jobs.gv.com:gv` | fund board |\n"
        "| Network | | not a machine channel |\n")
    monkeypatch.setattr(sweep, "ROOT", tmp_path)
    assert sweep.load_catalog() == [("HN hiring", "hn", "whoishiring"),
                                    ("GV", "consider", "jobs.gv.com:gv")]


def run_sweep(tmp_path, monkeypatch, capsys, leads, pipeline="", seen=None):
    (tmp_path / "me").mkdir(exist_ok=True)
    (tmp_path / "me/channels.md").write_text("| HN | `hn` | |\n")
    (tmp_path / "pipeline.md").write_text(pipeline)
    (tmp_path / "applications").mkdir(exist_ok=True)
    monkeypatch.setattr(sweep, "ROOT", tmp_path)
    monkeypatch.setattr(sweep, "SEEN", tmp_path / ".sweep-seen.json")
    if seen is not None:
        (tmp_path / ".sweep-seen.json").write_text(json.dumps(seen))
    monkeypatch.setattr(sweep, "fetch_all", lambda catalog: [("HN", leads, None)])
    sweep.sweep()
    return capsys.readouterr().out


def test_fresh_lead_lands_in_digest(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys, [lead()])
    assert "## New leads (1)" in out
    assert "Acme Health" in out


def test_already_decided_is_dropped_and_named(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys, [lead()],
                    pipeline="| Acme Health | applied | ...")
    assert "## New leads (0)" in out
    assert "1 already decided: Acme Health" in out


def test_wrong_metro_and_title_are_counted(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(location="New York, NY"),
                     lead(company="B Co", title="Account Executive", url="https://x.com/2")])
    assert "1 wrong metro" in out
    assert "1 wrong title class" in out


def test_second_run_is_quiet(tmp_path, monkeypatch, capsys):
    run_sweep(tmp_path, monkeypatch, capsys, [lead()])
    out = run_sweep(tmp_path, monkeypatch, capsys, [lead()],
                    seen=json.loads((tmp_path / ".sweep-seen.json").read_text()))
    assert "## New leads (0)" in out
    assert "1 seen before" in out


def test_channel_error_prints_loud(tmp_path, monkeypatch, capsys):
    (tmp_path / "me").mkdir()
    (tmp_path / "me/channels.md").write_text("| HN | `hn` | |\n")
    (tmp_path / "pipeline.md").write_text("")
    (tmp_path / "applications").mkdir()
    monkeypatch.setattr(sweep, "ROOT", tmp_path)
    monkeypatch.setattr(sweep, "SEEN", tmp_path / ".sweep-seen.json")
    monkeypatch.setattr(sweep, "fetch_all", lambda c: [("HN", [], "hn: no thread")])
    sweep.sweep()
    assert "ERROR HN: hn: no thread" in capsys.readouterr().out


def test_decided_matches_whole_names_not_prose(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Ada", title="Staff ML Engineer", url="https://x.com/3")],
                    pipeline="**Messages to send.** Ask Adam about the Acme Health seat.")
    assert "## New leads (1)" in out


def test_manager_and_intern_seats_drop(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(title="Engineering Manager, Machine Learning"),
                     lead(company="B Co", title="Machine Learning Intern", url="https://x.com/4")])
    assert "2 not an IC seat" in out
