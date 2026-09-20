"""Every path the repo cites, and the two absences that are not failures."""

import pytest

from tools import citations


def test_a_path_that_resolves_is_quiet_and_one_that_does_not_is_named(repo):
    repo.write("board.md", "read `profile/criteria.md` first\nand `profile/gone.md`\n")
    repo.write("profile/criteria.md", "# Criteria\n")
    dead, local = citations.check(repo.root)
    assert dead == ["board.md:2: missing profile/gone.md"]
    assert local == 0


def test_a_link_resolves_against_the_file_that_carries_it(repo):
    """An index links a sibling note by bare filename, which is right for
    whoever opens it and invisible from the repo root."""
    repo.write("profile/meetings/index.md", "- [Sam](2026-09-15-sam.md)\n")
    repo.write("profile/meetings/2026-09-15-sam.md", "# Sam\n")
    assert citations.check(repo.root)[0] == []


def test_a_naming_convention_is_not_a_citation(repo):
    """No file named `YYYY-MM-DD-topic.md` should ever exist."""
    repo.write("board.md", "name it `YYYY-MM-DD-topic.md`, or `apply/<company>/log.md`\n")
    assert citations.check(repo.root)[0] == []


def test_urls_and_anchors_are_not_paths(repo):
    repo.write("board.md", "[posting](https://example.com/jobs/1) and [why](#reasons)\n")
    assert citations.check(repo.root)[0] == []


def test_imported_material_is_counted_not_failed(repo):
    """Gitignored source is absent from a fresh clone by design."""
    repo.write(".gitignore", "profile/documents/\n")
    repo.write("board.md", "from `profile/documents/offer.pdf`\n")
    assert citations.check(repo.root) == ([], 1)


def test_a_per_instance_file_is_counted_not_failed(repo):
    """The template ships the rules that name these without the files."""
    repo.write("AGENTS.md", "the words live in `source/gates.md`\n")
    assert citations.check(repo.root) == ([], 1)


def test_only_the_bare_index_name_is_excused(repo):
    """The four index files are per-instance and the rules name the file
    generically, which is why the bare name is excused. A real path that ends
    in the same word is a dead citation like any other, and the shell version
    of this check waved those through for months."""
    repo.write("AGENTS.md", "each carries an `index.md`, see `apply/gone/index.md`\n")
    dead, local = citations.check(repo.root)
    assert dead == ["AGENTS.md:1: missing apply/gone/index.md"]
    assert local == 1


def test_the_bullet_map_must_name_sections_the_fact_base_has(repo):
    """A stale entry in the map is a resume bullet with nothing behind it."""
    repo.write("profile/experience.md", "## Sprinter\n\nNumbers.\n")
    repo.write("profile/resume.md",
               "# Resume\n\n## What backs each bullet\n\n"
               "- forecasting: `## Sprinter`\n- pilots: `## KPL pilot`\n")
    dead, _ = citations.check(repo.root)
    assert dead == ["profile/resume.md: the bullet map names ## KPL pilot, "
                    "which profile/experience.md does not have"]


def test_the_map_is_read_only_below_its_own_heading(repo):
    """A section named in the prose above the map is not part of the map."""
    repo.write("profile/experience.md", "## Sprinter\n")
    repo.write("profile/resume.md",
               "`## Elsewhere` is discussed here.\n\n## What backs each bullet\n\n"
               "- forecasting: `## Sprinter`\n")
    assert citations.check(repo.root)[0] == []


def test_a_dead_citation_exits_non_zero(repo, monkeypatch, capsys):
    repo.write("board.md", "read `profile/gone.md`\n")
    monkeypatch.setattr(citations, "ROOT", repo.root)
    with pytest.raises(SystemExit):
        citations.main()
    assert "missing profile/gone.md" in capsys.readouterr().out
