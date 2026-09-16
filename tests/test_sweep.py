"""The pipeline around the fetchers: catalog, dedupe, filters, digest."""

import json

from harpoon import sweep, watch
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
    assert sweep.load_catalog() == [("HN hiring", "hn", "whoishiring", ""),
                                    ("GV", "consider", "jobs.gv.com:gv", "")]


def test_catalog_reads_the_watching_column(tmp_path, monkeypatch):
    """A watchlist row has four cells and the third is its criterion; a
    catalog row has three and its third cell is prose."""
    (tmp_path / "me").mkdir()
    (tmp_path / "me/channels.md").write_text(
        "| Rad AI | `ashby:radai` | band > 260 | demoted on peer band |\n"
        "| HN hiring | `hn` | monthly thread |\n")
    monkeypatch.setattr(sweep, "ROOT", tmp_path)
    rows = sweep.load_catalog()
    assert rows[0].watching == "band > 260"
    assert rows[1].watching == ""


def test_alternation_survives_the_cell_split(tmp_path, monkeypatch):
    """A title regex needs |, which is also the cell separator, so the file
    escapes it and the parse has to put it back."""
    (tmp_path / "me").mkdir()
    (tmp_path / "me/channels.md").write_text(
        "| Zipline | `greenhouse:flyzipline` | title ~ staff\\|principal | 350 postings |\n")
    monkeypatch.setattr(sweep, "ROOT", tmp_path)
    assert sweep.load_catalog()[0].watching == "title ~ staff|principal"


def test_band_floor_reads_every_real_shape():
    cases = {
        "$158,400 – $237,600": 158400,
        "$300-350k": 300000,
        "$175K – $250K • Offers Equity": 175000,
        "$156k - 210k": 156000,
        "$175K – $230K • 0.1% – 0.3% • Relocation Bonus": 175000,
        "$120K – $140K": 120000,
        "no band": None,
        "": None,
    }
    for band, floor in cases.items():
        assert watch.band_floor(band) == floor, band
    assert watch.band_floor(None) is None


def run_sweep(tmp_path, monkeypatch, capsys, leads, pipeline="", seen=None,
              channels="| HN | `hn` | |\n"):
    (tmp_path / "me").mkdir(exist_ok=True)
    (tmp_path / "me/channels.md").write_text(channels)
    (tmp_path / "pipeline.md").write_text(pipeline)
    (tmp_path / "applications").mkdir(exist_ok=True)
    monkeypatch.setattr(sweep, "ROOT", tmp_path)
    monkeypatch.setattr(sweep, "SEEN", tmp_path / ".sweep-seen.json")
    monkeypatch.setattr(sweep, "EVALS", tmp_path / "evals")
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
    assert "1 already-decided: Acme Health" in out


def test_wrong_metro_and_title_are_counted(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(location="New York, NY"),
                     lead(company="B Co", title="Account Executive", url="https://x.com/2")])
    assert "1 wrong-metro" in out
    assert "1 title-class" in out


def test_second_run_is_quiet(tmp_path, monkeypatch, capsys):
    run_sweep(tmp_path, monkeypatch, capsys, [lead()])
    out = run_sweep(tmp_path, monkeypatch, capsys, [lead()],
                    seen=json.loads((tmp_path / ".sweep-seen.json").read_text()))
    assert "## New leads (0)" in out
    assert "1 seen-before" in out


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


def test_watched_company_survives_already_decided(tmp_path, monkeypatch, capsys):
    """A company cataloged as its own channel is on the board with no seat and
    is being watched for one; already-decided must not swallow its postings."""
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="acmehealth")],
                    pipeline="| Acme Health | lead | watch | ...",
                    channels="| Acme Health | `greenhouse:acmehealth` | watchlist |\n")
    assert "## New leads (1)" in out


def test_watching_one_company_does_not_unwatch_the_rest(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Other Co", url="https://x.com/9")],
                    pipeline="| Other Co | lead | now | ...",
                    channels="| Acme Health | `greenhouse:acmehealth` | watchlist |\n")
    assert "1 already-decided: Other Co" in out


def test_decided_matches_whole_names_not_prose(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Ada", title="Staff ML Engineer", url="https://x.com/3")],
                    pipeline="**Messages to send.** Ask Adam about the Acme Health seat.")
    assert "## New leads (1)" in out


def test_manager_and_intern_seats_drop(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(title="Engineering Manager, Machine Learning"),
                     lead(company="B Co", title="Machine Learning Intern", url="https://x.com/4")])
    assert "2 ic-seat" in out


def test_tooling_gtm_and_foreign_remote_drop(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(title="Staff AI Platform Engineer"),
                     lead(company="B Co", title="Senior ML Engineer",
                          location="Europe; London (Remote)", url="https://x.com/5"),
                     lead(company="C Co", title="Staff ML Engineer",
                          location="Canada; United States (Remote)", url="https://x.com/6")])
    assert "1 tooling-or-gtm" in out
    assert "1 foreign-remote" in out
    assert "## New leads (1)" in out


def test_pipes_in_titles_stay_in_one_cell(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(title="ML Engineer | LLM Evals")])
    assert "ML Engineer / LLM Evals" in out


def test_each_step_logs_both_calls_and_stops_at_the_drop(tmp_path, monkeypatch, capsys):
    import datetime
    run_sweep(tmp_path, monkeypatch, capsys,
              [lead(), lead(company="B Co", title="Machine Learning Manager", url="https://x.com/7")])
    day = datetime.date.today().isoformat()
    ic = (tmp_path / "evals" / f"{day}-sweep-ic-seat.csv").read_text()
    assert "pass,Acme Health" in ic and "drop,B Co" in ic
    gtm = (tmp_path / "evals" / f"{day}-sweep-tooling-or-gtm.csv").read_text()
    assert "Acme Health" in gtm and "B Co" not in gtm


WATCH_RAD = "| Rad AI | `ashby:radai` | band > 260 | watchlist |\n"


def test_watched_posting_below_the_floor_drops(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Rad AI", band="$200K – $260K")],
                    channels=WATCH_RAD)
    assert "## New leads (0)" in out
    assert "1 watch-criterion" in out


def test_watched_posting_above_the_floor_is_a_hit(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Rad AI", band="$280K – $340K")],
                    channels=WATCH_RAD)
    assert "## Watchlist hits (1)" in out
    assert "band > 260" in out
    assert "## New leads (0)" in out


def test_a_band_topping_higher_but_starting_lower_still_misses(tmp_path, monkeypatch, capsys):
    """Why band > reads the floor: $240-265K tops out above $260K but starts
    below it, so it is worse than the seat that caused the pass."""
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Rad AI", band="$240K – $265K")],
                    channels=WATCH_RAD)
    assert "1 watch-criterion" in out
    assert "Watchlist hits" not in out


def test_unbanded_posting_passes_a_band_criterion(tmp_path, monkeypatch, capsys):
    """An unposted band is an unknown, not a known miss."""
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Rad AI", band=None)], channels=WATCH_RAD)
    assert "## Watchlist hits (1)" in out


def test_title_criterion_matches_and_misses(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Zipline", title="Staff Data Scientist"),
                     lead(company="Zipline", title="Senior Data Scientist",
                          url="https://x.com/8")],
                    channels="| Zipline | `greenhouse:flyzipline` | "
                             "title ~ staff\\|principal | watchlist |\n")
    assert "## Watchlist hits (1)" in out
    assert "1 watch-criterion" in out


def test_criterion_is_found_by_display_name_when_the_slug_differs(tmp_path, monkeypatch, capsys):
    """Zipline's slug is flyzipline but its board answers "Zipline"; keying on
    one of the two would leave the criterion silently unchecked."""
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Zipline", title="Senior Data Scientist")],
                    channels="| Zipline | `greenhouse:flyzipline` | "
                             "title ~ staff\\|principal | watchlist |\n")
    assert "1 watch-criterion" in out


def test_empty_criterion_watches_everything(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Honor", band="$90K – $100K")],
                    channels="| Honor | `greenhouse:honor` | | 17 postings |\n")
    assert "## New leads (1)" in out
    assert "Watchlist hits" not in out


def test_unwatched_company_ignores_the_new_step(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(band="$90K – $100K")], channels=WATCH_RAD)
    assert "## New leads (1)" in out
    assert "watch-criterion" not in out
