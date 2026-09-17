---
name: setup
description: Verify a new Harpoon instance before any real work. Checks that this is the candidate's own private repo, that git identity and the render toolchain are in place, and walks through what goes where. Use on first run in a fresh instance, when something environmental fails, or when asked to check the setup.
---

# Setup

One job: verify the instance. This skill changes no context files and writes
nothing but its findings. Run it once when the repo is new, and again whenever
a render or a push fails for a reason that smells environmental.

## The checks, in order

1. **This is the candidate's own private repo.** `gh repo view --json
   visibility,isTemplate` if `gh` is installed, otherwise `git remote -v` and
   ask. The remote must be theirs, not the public template, and visibility
   must be private: everything in this repo is sensitive. A clone of the
   template with no remote of its own has no backup, which is the failure
   this check exists to catch. The fix is GitHub's "Use this template" button
   with the private option, or `gh repo create <name> --template
   <template-repo> --private`.
2. **Everything original gets pushed.** `.gitignore` here excludes only
   rebuildable renders and the re-exportable LinkedIn export. If `git status`
   shows original work as untracked and ignored, something moved a directory.
3. **Git identity.** `git config user.name` must be the candidate's real name:
   the render script derives the PDF filename an employer sees from it.
4. **The render toolchain.** `pandoc` and `typst` on the path, plus the Inter
   font (`brew install pandoc typst && brew install --cask font-inter` on
   macOS). Without Inter the render falls back silently and looks wrong.
5. **Python.** `uv run pytest` passes, which proves the engine package
   imports.

## What goes where

Say this out loud at the end of a clean run, briefly:

- `pipeline.md` is the board and the only todo list. **Create it if it is
  missing**, which it will be in a fresh instance: the template ships no
  `pipeline.md` because it would carry real companies. Write the skeleton, the
  status meanings at the top, then `## Todo` with its five blocks and `## Board`
  with the table header. `.claude/skills/update-board/` says what each block
  means; copy the shape from there rather than inventing one. It is the one page
  the candidate reads, so every skill files what it needs from him here.
- `me/` is theirs: criteria, fact base, resume, rules, interviews, meetings,
  raw documents, the LinkedIn export under `me/network/export/`.
- `applications/` grows one directory per company that advances.
- The order of first operations: gather-experience, then write-criteria and
  write-resume, then sweep-jobs. Experience comes first because the criteria
  and the resume are both built from it, so one interview feeds both.

## Finish

Report each check as passed or failed with the fix, and stop. Do not start an
interview from here; that is its own skill and its own conversation.
