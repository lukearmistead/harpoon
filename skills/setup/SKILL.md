---
name: setup
description: Walk a new Harpoon instance from a fresh clone to a working one. Checks that this is the candidate's own private repo, installs the toolchain, writes the files the template deliberately ships without, and ends with a sweep that returns something. Use on first run in a fresh instance, when something environmental fails, or when asked to check the setup.
---

# Setup

One job: get this instance working, and leave nothing for them to do in a
terminal afterwards. Run it once when the repo is new, and again whenever a
render or a push fails for a reason that smells environmental.

**Do the steps, do not hand over a checklist.** The person running this may
never have opened a terminal, and every command below is one you run and
report on, not one you paste for them to type. Where a step needs something
only they can do, a GitHub account, a LinkedIn export, say what it is in one
sentence and what it is for.

## The checks, in order

1. **This is the candidate's own private repo.** `gh repo view --json
   visibility,isTemplate` if `gh` is installed, otherwise `git remote -v` and
   ask. The remote must be theirs, not the public template, and visibility
   must be private: everything in this repo is sensitive. A clone of the
   template with no remote of its own has no backup, which is the failure
   this check exists to catch. The fix is GitHub's "Use this template" button
   with the private option, or `gh repo create <name> --template
   <template-repo> --private`. If they have no GitHub account, say plainly
   that nothing here is backed up until they do, and keep going.
2. **Everything original gets pushed.** `.gitignore` here excludes only
   rebuildable renders and the re-exportable LinkedIn export. If `git status`
   shows original work as untracked and ignored, something moved a directory.
3. **Git identity.** `git config user.name` must be the candidate's real name:
   the render script derives the PDF filename an employer sees from it.
4. **The render toolchain.** `pandoc` and `typst` on the path, plus the Inter
   font (`brew install pandoc typst && brew install --cask font-inter` on
   macOS). Run the install rather than quoting it. Without Inter the render
   falls back silently and looks wrong, which is the worst kind of wrong:
   there is no error and the PDF goes out anyway.
5. **Python.** `uv run pytest` passes, which proves the `tools` package
   imports.
6. **The checks run on commit.** `git config core.hooksPath` must read
   `.githooks`. Set it if it does not: the hook is a tracked file but the
   configuration that points git at it is per-clone, so a fresh clone has none.
   Then `./scripts/check-all.sh` once, which is what the hook runs.
7. **`learn/lessons.md` exists.** Create it if it is missing, which it will
   be in a fresh instance: a heading, one line saying what it is for, and the
   rule that an entry becomes a rule only when the candidate says so, through
   the Todo. `AGENTS.md` holds the long version.
8. **`profile/positioning.md` and `profile/voice.md` exist.** Positioning
   holds the picks in force, which every drafting skill loads first. Create it
   with a heading and the line saying that a pick states the rule and names
   the `profile/interviews/` file that settled it; `gather-experience` fills
   it. Then `profile/voice.md`, same treatment. It holds both halves of the
   voice, which `AGENTS.md` and every drafting skill point at: the register to
   match, quoted from something they wrote, the tells that give an LLM away,
   and any standing correction they have given on their own prose. Empty is
   fine to start; `gather-experience` fills it.
9. **`source/gates.md` exists and describes their search, not somebody
   else's.** See the section below. This is the one check whose failure is
   invisible: a gates file belonging to another search returns an empty digest
   rather than an error, so it gets done here or it gets found weeks later.
10. **`board.md` exists.** A fresh clone has none, because the board names
    real companies: the template ships the rules that cite it and not the
    file. Write it from `skills/update-board/`, which is where the stages and
    the Todo blocks are defined. An instance cloned before 2026-09-20 also
    arrived with a frozen pre-rename tree the export could not reach: me/,
    applications/, evals/, harpoon/ and a pipeline.md teaching a `contacted`
    stage that no longer exists. Those are written plain here because they no
    longer exist anywhere. They were deleted at the source, so only an old
    instance still has them to remove by hand.
11. **The indexes exist once there is anything to index.** `python3 -m
    tools.notes` writes an `index.md` in `profile/meetings/`,
    `profile/interviews/`, `profile/documents/` and `profile/network/`, and
    skips a directory with nothing in it yet. The template ships none of them,
    because they name real people and real documents; the rules that cite them
    ship anyway, and `tools/citations.py` carries the list of every path the
    template deliberately ships without.

## Writing source/gates.md

`profile/criteria.md` says what they want in sentences. `tools/sweep.py` can
only match words against a posting, so `source/gates.md` is the same stops
written as the words a posting actually uses. It is theirs, it is never
exported, and until it exists the sweep stops and says so.

Read `profile/criteria.md` first and write what it already answers. Ask only
for what it does not:

- **Where will they work?** Cities, metro names, and whether remote counts.
- **What kind of work?** The words that appear in the titles they want. Wide
  on purpose: this gate is here to throw out the nurse and the accountant,
  not to pick between two good seats.
- **What is never right?** Manager seats if they are an IC, or whatever the
  equivalent is for them. Whole categories they will not take.
- **Which countries are not an option**, and which words mean the posting is
  open where they live anyway.

The file's shape, which `tools/gates.py` is the only reader of: a `## <gate>`
heading per list, prose under it in their words, and the words themselves in a
fenced block separated by commas. The six headings are `wrong-metro`,
`title-class`, `ic-seat`, `tooling-or-gtm`, `foreign-remote` and `in-us`, and
every one of them has to be there even when its list is empty, which switches
that gate off. A word matches anywhere it appears, so `europe` catches
"European"; a word in quotes has to stand alone, which is for the short ones
like `"ai"` and `"sf"`.

Then run `python3 -m tools.sweep` and read the digest with them. A first
sweep that returns nothing is the expected failure here, and the digest names
the gate that ate everything. Fix the list and run it again before calling
setup done.

## What goes where

Say this out loud at the end of a clean run, briefly:

- `board.md` is the board and the only todo list. It is the one page the
  candidate reads, so every skill files what it needs from them here.
- `profile/` is who they are: criteria, fact base, resume, voice, positioning,
  interviews, meetings, raw documents, the LinkedIn export under
  `profile/network/export/`.
- `source/` is where jobs come from: the channel catalog and the gate words.
- `apply/` grows one directory per company that advances.
- The order of first operations: gather-experience, then write-criteria and
  write-resume, then sweep-jobs. Experience comes first because the criteria
  and the resume are both built from it, so one interview feeds both.

## Finish

Report each check as passed, fixed, or failed with what is left to do, and
stop. Do not start an interview from here; that is its own skill and its own
conversation.
