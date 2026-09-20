"""The note indexes: what the generator owns, and what only a person can write."""

import pytest
from types import SimpleNamespace

from tools import notes


def note(directory, name, heading):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(f"# {heading}\n\n## Notes\n\n- something\n")
    return directory / name


def test_index_lists_notes_newest_first(tmp_path):
    note(tmp_path, "2026-08-23-ryan-quan.md", "2026-08-23 Ryan Quan")
    note(tmp_path, "2026-09-15-sam-wertheimer.md", "2026-09-15 Sam Wertheimer")
    body = notes.render(tmp_path)
    assert body.index("Sam Wertheimer") < body.index("Ryan Quan")
    assert "**2026-09-15** [Sam Wertheimer](2026-09-15-sam-wertheimer.md)" in body


def test_title_drops_the_date_the_heading_repeats(tmp_path):
    path = note(tmp_path, "2026-09-16-data-aggregators.md",
                "2026-09-16, the data aggregators")
    assert notes.title(path) == "the data aggregators"


def test_a_written_summary_survives_regeneration(tmp_path):
    """The one thing no generator can write is the one thing it must not lose."""
    note(tmp_path, "2026-09-15-sam-wertheimer.md", "2026-09-15 Sam Wertheimer")
    (tmp_path / "index.md").write_text(notes.render(tmp_path))
    written = notes.render(tmp_path).replace(
        notes.NEEDS_A_LINE, "Sprinter's strategy lead on forecasting demand")
    (tmp_path / "index.md").write_text(written)

    note(tmp_path, "2026-09-16-later.md", "2026-09-16 Later")
    again = " ".join(notes.render(tmp_path).split())  # rewrapped, so normalize
    assert "Sprinter's strategy lead on forecasting demand" in again
    assert again.count(notes.NEEDS_A_LINE) == 1


def test_a_long_filename_is_never_wrapped_across_lines(tmp_path):
    """A wrapped path is a path that will not open, and it breaks carry-forward."""
    name = "2026-09-16-out-of-pocket-talent-network-and-then-some-more.md"
    note(tmp_path, name, "2026-09-16, a heading long enough to force a wrap here")
    (tmp_path / "index.md").write_text(notes.render(tmp_path))
    assert f"]({name})" in (tmp_path / "index.md").read_text()
    assert name in notes.existing(tmp_path / "index.md")


def test_the_header_prose_is_never_touched(tmp_path):
    """Everything above the markers belongs to whoever wrote it."""
    note(tmp_path, "2026-09-15-sam-wertheimer.md", "2026-09-15 Sam Wertheimer")
    (tmp_path / "index.md").write_text(
        f"# Mine\n\nProse a person wrote.\n\n{notes.START}\n- stale\n{notes.END}\n")
    rendered = notes.render(tmp_path)
    assert rendered.startswith("# Mine\n\nProse a person wrote.")
    assert "- stale" not in rendered


def test_check_fails_on_a_stale_index_and_on_a_missing_summary(tmp_path):
    note(tmp_path, "2026-09-15-sam-wertheimer.md", "2026-09-15 Sam Wertheimer")
    assert any("stale" in p for p in notes.check(tmp_path))

    (tmp_path / "index.md").write_text(notes.render(tmp_path))
    problems = notes.check(tmp_path)
    assert problems and all("no summary yet" in p for p in problems)

    (tmp_path / "index.md").write_text(
        notes.render(tmp_path).replace(notes.NEEDS_A_LINE, "what it says"))
    # a hand-written summary changes the wrapping, so the file is not canonical
    # until the generator runs again, and the check says so
    assert any("stale" in p for p in notes.check(tmp_path))
    (tmp_path / "index.md").write_text(notes.render(tmp_path))
    assert notes.check(tmp_path) == []


def test_check_exits_non_zero_when_something_is_wrong(tmp_path, monkeypatch):
    note(tmp_path / "profile" / "meetings", "2026-09-15-x.md", "2026-09-15 X")
    monkeypatch.setattr(notes, "ROOT", tmp_path)
    monkeypatch.setattr(notes, "DATED_DIRS", ("profile/meetings",))
    monkeypatch.setattr(notes, "MATERIAL_DIRS", ())
    with pytest.raises(SystemExit):
        notes.main(["--check"])


def test_an_empty_directory_needs_no_index(tmp_path):
    """The template ships both directories empty; a check on them must be quiet."""
    (tmp_path / "meetings").mkdir()
    assert notes.check(tmp_path / "meetings") == []


def test_an_index_that_exists_stays_checked_after_the_notes_go(tmp_path):
    note(tmp_path, "2026-09-15-sam-wertheimer.md", "2026-09-15 Sam Wertheimer")
    (tmp_path / "index.md").write_text(
        notes.render(tmp_path).replace(notes.NEEDS_A_LINE, "what it says"))
    (tmp_path / "2026-09-15-sam-wertheimer.md").unlink()
    assert any("stale" in p for p in notes.check(tmp_path))


def test_the_index_never_lists_itself(tmp_path, monkeypatch):
    """Only bites once: the index is untracked until the commit that adds it."""
    inside = tmp_path / "profile" / "network"
    inside.mkdir(parents=True)
    listed = ("roster.csv", "index.md", "README.md", ".gitkeep")
    for name in listed:
        (inside / name).write_text("x")

    monkeypatch.setattr(notes, "ROOT", tmp_path)
    monkeypatch.setattr(notes.subprocess, "run", lambda *a, **k: SimpleNamespace(
        stdout="\0".join(f"profile/network/{n}" for n in listed)))

    assert [str(p) for p in notes.tracked(inside)] == ["roster.csv"]
