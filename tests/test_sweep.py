"""The pipeline around the fetchers: catalog, dedupe, filters, digest."""

import csv
import json
import re

from harpoon import evals, sweep, watch
from harpoon.contract import Lead


def latest_run(tmp_path):
    return sorted((tmp_path / "evals").glob("*"))[-1]


def sweep_rows(tmp_path):
    with open(latest_run(tmp_path) / "sweep.csv", newline="") as f:
        return list(csv.DictReader(f))


def seed_run(tmp_path, name, rows):
    """An earlier run directory, so carry-forward has something to read."""
    run = tmp_path / "evals" / name
    run.mkdir(parents=True)
    with open(run / "sweep.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(evals.SWEEP_COLUMNS)
        for row in rows:
            w.writerow([row.get(c, "") for c in evals.SWEEP_COLUMNS])
    return run


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
        "| Beacon AI | `ashby:beaconai` | band > 260 | demoted on peer band |\n"
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
        "| Kestrel | `greenhouse:flykestrel` | title ~ staff\\|principal | 350 postings |\n")
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
              channels="| HN | `hn` | |\n", error=None):
    (tmp_path / "me").mkdir(exist_ok=True)
    (tmp_path / "me/channels.md").write_text(channels)
    (tmp_path / "pipeline.md").write_text(pipeline)
    (tmp_path / "applications").mkdir(exist_ok=True)
    monkeypatch.setattr(sweep, "ROOT", tmp_path)
    monkeypatch.setattr(sweep, "SEEN", tmp_path / ".sweep-seen.json")
    monkeypatch.setattr(sweep, "EVALS", tmp_path / "evals")
    if seen is not None:
        (tmp_path / ".sweep-seen.json").write_text(json.dumps(seen))
    monkeypatch.setattr(sweep, "fetch_all", lambda catalog: [("HN", leads, error)])
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


def test_peninsula_dies_at_the_metro_gate_and_remote_does_not(
        tmp_path, monkeypatch, capsys):
    """me/criteria.md Geography is San Francisco or the East Bay, and remote
    passes because it requires no move. The gate once took the whole Bay Area,
    which left judgment rejecting peninsula addresses by hand every run."""
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(location="Palo Alto, CA"),
                     lead(company="B Co", location="Redwood City, CA",
                          url="https://x.com/2"),
                     lead(company="C Co", location="Oakland, CA",
                          url="https://x.com/3"),
                     lead(company="D Co", location="Remote (US)",
                          url="https://x.com/4")])
    assert "2 wrong-metro" in out
    assert "## New leads (2)" in out


def test_one_call_graded_across_many_postings_counts_once(tmp_path, capsys):
    """Three of one shape amends a skill, so a shape has to count calls, not
    rows. Three postings graded in one sitting are one call, and the same label
    carried into a later run is not a second."""
    graded = [dict(decision="kept", adjudication="wrong-metro", judge="human",
                   adjudicated="2026-01-01", shape="gate too wide",
                   company=name, title="Staff ML Engineer")
              for name in ("A Co", "B Co", "C Co")]
    seed_run(tmp_path, "2026-01-01T000000", graded)
    seed_run(tmp_path, "2026-01-02T000000", graded)
    evals.grades(tmp_path / "evals")
    out = capsys.readouterr().out
    assert "6 rows, 1 calls" in out
    assert "**1** gate too wide" in out
    assert "| kept | 6 | 0 | 6 |" in out


def test_second_run_is_quiet(tmp_path, monkeypatch, capsys):
    run_sweep(tmp_path, monkeypatch, capsys, [lead()])
    out = run_sweep(tmp_path, monkeypatch, capsys, [lead()],
                    seen=json.loads((tmp_path / ".sweep-seen.json").read_text()))
    assert "## New leads (0)" in out
    assert "1 seen-before" in out


def test_channel_error_prints_loud(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys, [], error="hn: no thread")
    assert "ERROR HN: hn: no thread" in out
    assert json.loads((latest_run(tmp_path) / "run.json").read_text())["errors"] \
        == ["HN: hn: no thread"]


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


def test_foreign_remote_reads_the_title_too(tmp_path, monkeypatch, capsys):
    """A posting that means it says so in the title, and the location cell
    alone once let an Austrian seat through the whole funnel."""
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(title="Senior ML Engineer - based in Austria",
                          location="Austria; Remote (Remote)"),
                     lead(company="B Co", title="Staff AI Engineer (Spain)",
                          location="Remote", url="https://x.com/8"),
                     lead(company="C Co", title="Staff ML Engineer, US and Canada",
                          location="Remote", url="https://x.com/9")])
    assert "2 foreign-remote" in out
    assert "## New leads (1)" in out


def test_pipes_in_titles_stay_in_one_cell(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(title="ML Engineer | LLM Evals")])
    assert "ML Engineer / LLM Evals" in out


def test_the_log_is_one_row_per_lead_naming_the_gate_that_fired(tmp_path, monkeypatch, capsys):
    run_sweep(tmp_path, monkeypatch, capsys,
              [lead(), lead(company="B Co", title="Machine Learning Manager", url="https://x.com/7")])
    rows = sweep_rows(tmp_path)
    assert [(r["company"], r["decision"]) for r in rows] == [
        ("Acme Health", "kept"), ("B Co", "ic-seat")]
    assert all(r["adjudication"] == "" for r in rows)


def test_the_run_directory_carries_the_time_not_just_the_day(tmp_path, monkeypatch, capsys):
    """Two runs on one day used to share a filename and the later one won,
    which is how the 2026-09-15 13:40 run lost its predictions."""
    run_sweep(tmp_path, monkeypatch, capsys, [lead()])
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{6}", latest_run(tmp_path).name)


def test_a_new_run_leaves_an_older_run_alone(tmp_path, monkeypatch, capsys):
    old = seed_run(tmp_path, "2000-01-01T000000", [{"decision": "kept",
                                                    "company": "Older Co"}])
    run_sweep(tmp_path, monkeypatch, capsys, [lead()])
    assert "Older Co" in (old / "sweep.csv").read_text()
    assert len(list((tmp_path / "evals").glob("*"))) == 2


def test_a_lead_from_two_channels_is_judged_once_then_marked_duplicate(
        tmp_path, monkeypatch, capsys):
    """Within-run repeats used to land on seen-before, which conflated
    "surfaced by an earlier run" with "arrived twice in this one"."""
    out = run_sweep(tmp_path, monkeypatch, capsys, [lead(), lead(source="other")])
    assert [r["decision"] for r in sweep_rows(tmp_path)] == ["kept", "duplicate"]
    assert "## New leads (1)" in out
    assert "1 duplicate" in out


def test_an_adjudication_survives_the_next_run(tmp_path, monkeypatch, capsys):
    seed_run(tmp_path, "2000-01-01T000000", [dict(
        decision="ic-seat", adjudication="kept", judge="human", shape="title-read",
        company="B Co", title="Machine Learning Manager", location="San Francisco",
        url="https://x.com/7", source="test")])
    run_sweep(tmp_path, monkeypatch, capsys,
              [lead(company="B Co", title="Machine Learning Manager", url="https://x.com/7")])
    row, = sweep_rows(tmp_path)
    assert (row["decision"], row["adjudication"], row["judge"]) == (
        "ic-seat", "kept", "human")


def test_a_label_outlives_a_run_that_never_saw_its_lead(tmp_path, monkeypatch, capsys):
    """Labels are read from every earlier run, not just the last one: a
    posting is absent from most runs, and its label must not die with them."""
    seed_run(tmp_path, "2000-01-01T000000", [dict(
        decision="kept", adjudication="kept", judge="human", shape="confirmed",
        company="Acme Health", title="Staff ML Engineer", location="San Francisco",
        url="https://x.com/1", source="test")])
    seed_run(tmp_path, "2000-01-02T000000", [dict(decision="kept",
                                                  company="Someone Else")])
    run_sweep(tmp_path, monkeypatch, capsys, [lead()])
    row, = sweep_rows(tmp_path)
    assert (row["adjudication"], row["shape"]) == ("kept", "confirmed")


def test_a_label_does_not_survive_the_gate_moving(tmp_path, monkeypatch, capsys):
    """Carry-forward keys on the decision too: a lead that now dies at a
    different gate is a different call, and the old label would be a lie."""
    seed_run(tmp_path, "2000-01-01T000000", [dict(
        decision="wrong-metro", adjudication="kept", judge="human",
        company="B Co", title="Machine Learning Manager", location="San Francisco",
        url="https://x.com/7", source="test")])
    run_sweep(tmp_path, monkeypatch, capsys,
              [lead(company="B Co", title="Machine Learning Manager", url="https://x.com/7")])
    row, = sweep_rows(tmp_path)
    assert (row["decision"], row["adjudication"]) == ("ic-seat", "")


def test_reconcile_names_a_kept_lead_with_no_verdict(tmp_path, monkeypatch, capsys):
    """A kept lead nobody ruled on is not pending, it is gone: the seen-cache
    remembers it and the next run drops it at seen-before."""
    run_sweep(tmp_path, monkeypatch, capsys, [lead()])
    capsys.readouterr()
    sweep.reconcile_board()
    assert "Acme Health" in capsys.readouterr().out


def test_reconcile_knows_a_slug_from_a_display_name(tmp_path, monkeypatch, capsys):
    """A watched company reaches the digest by design, and its leads arrive
    under the ATS slug while the board row carries the display name. Matching
    on one of the two reports a boarded company as unjudged, every run."""
    run_sweep(tmp_path, monkeypatch, capsys, [lead(company="northwind66")],
              pipeline="| Northwind | lead | x |\n",
              channels="| Northwind | `greenhouse:northwind66` | |\n")
    assert [r["decision"] for r in sweep_rows(tmp_path)] == ["kept"]
    capsys.readouterr()
    sweep.reconcile_board()
    assert "(0)" in capsys.readouterr().out


def test_a_url_less_lead_is_not_judged_by_a_url_less_verdict(tmp_path, monkeypatch, capsys):
    """Aggregators hand back postings with no link. Matching empty against
    empty marked every one of them judged the moment any verdict lacked a url."""
    run_sweep(tmp_path, monkeypatch, capsys, [lead(url=None)])
    run = latest_run(tmp_path)
    with open(run / "judgment.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["decision", "company", "title", "url"])
        w.writerow(["reject", "Some Other Co", "", ""])
    capsys.readouterr()
    sweep.reconcile_board()
    assert "Acme Health" in capsys.readouterr().out


WATCH_BEACON = "| Beacon AI | `ashby:beaconai` | band > 260 | watchlist |\n"


def test_watched_posting_below_the_floor_drops(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Beacon AI", band="$200K – $260K")],
                    channels=WATCH_BEACON)
    assert "## New leads (0)" in out
    assert "1 watch-criterion" in out


def test_watched_posting_above_the_floor_is_a_hit(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Beacon AI", band="$280K – $340K")],
                    channels=WATCH_BEACON)
    assert "## Watchlist hits (1)" in out
    assert "band > 260" in out
    assert "## New leads (0)" in out


def test_a_band_topping_higher_but_starting_lower_still_misses(tmp_path, monkeypatch, capsys):
    """Why band > reads the floor: $240-265K tops out above $260K but starts
    below it, so it is worse than the seat that caused the pass."""
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Beacon AI", band="$240K – $265K")],
                    channels=WATCH_BEACON)
    assert "1 watch-criterion" in out
    assert "Watchlist hits" not in out


def test_unbanded_posting_passes_a_band_criterion(tmp_path, monkeypatch, capsys):
    """An unposted band is an unknown, not a known miss."""
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Beacon AI", band=None)], channels=WATCH_BEACON)
    assert "## Watchlist hits (1)" in out


def test_title_criterion_matches_and_misses(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Kestrel", title="Staff Data Scientist"),
                     lead(company="Kestrel", title="Senior Data Scientist",
                          url="https://x.com/8")],
                    channels="| Kestrel | `greenhouse:flykestrel` | "
                             "title ~ staff\\|principal | watchlist |\n")
    assert "## Watchlist hits (1)" in out
    assert "1 watch-criterion" in out


def test_criterion_is_found_by_display_name_when_the_slug_differs(tmp_path, monkeypatch, capsys):
    """Kestrel's slug is flykestrel but its board answers "Kestrel"; keying on
    one of the two would leave the criterion silently unchecked."""
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Kestrel", title="Senior Data Scientist")],
                    channels="| Kestrel | `greenhouse:flykestrel` | "
                             "title ~ staff\\|principal | watchlist |\n")
    assert "1 watch-criterion" in out


def test_empty_criterion_watches_everything(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(company="Dovetail", band="$90K – $100K")],
                    channels="| Dovetail | `greenhouse:dovetail` | | 17 postings |\n")
    assert "## New leads (1)" in out
    assert "Watchlist hits" not in out


def test_unwatched_company_ignores_the_new_step(tmp_path, monkeypatch, capsys):
    out = run_sweep(tmp_path, monkeypatch, capsys,
                    [lead(band="$90K – $100K")], channels=WATCH_BEACON)
    assert "## New leads (1)" in out
    assert "watch-criterion" not in out
