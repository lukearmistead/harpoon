# Harpoon

Job search repo. You are the copilot, and this is the rulebook, written to the
AGENTS.md standard so any agent can read it.

**This file is the Harpoon template, so a template update replaces it
wholesale.** A rule of the candidate's own written here would vanish, so their
standing rules live in `me/criteria.md` and win when the two disagree. Nothing
enters this file without their explicit go-ahead, drafted in conversation first.

## Layout

```
pipeline.md       status and next action, never stale, and the one page the
                  candidate reads. Opens with the grammar verdicts follow
evals/            one directory per run, and never exported. Every row carries
                  empty adjudication columns for the decision the step should
                  have made. LEARNINGS.md holds what a run taught with no row
applications/     one per company: company.md and its dated log, the variant,
                  the letter, form-fill.md, prep, debriefs, PDFs
me/criteria.md    what they want. Read it before evaluating anything
me/experience.md  the fact base. Every number lives here or nowhere. Never
                  invent a metric, title, date, or scope. Too long to load
                  whole, so reach it through the resume's map below
me/positioning.md the picks in force. Read it before writing about them
me/voice.md       how they sound and the tells to avoid. Read before any prose
me/resume.md      the master. A variant is cut from it, never rewritten. Its
                  `## What backs each bullet` names the fact base section
                  behind each claim: read the bullet, open the section only
                  when a seat needs more. write-resume keeps that map true
me/channels.md    where the sweep looks and what it has learned about looking
me/interviews/    how each settled answer was settled, whatever the occasion.
                  The cited authority for the fact base and the positioning
me/meetings/      their notes from conversations
me/experience/    raw source material
me/network/       LinkedIn export under export/, rosters beside it
                  Those four carry an `index.md` from `harpoon.notes`. Read it
                  before opening anything in them, and write the line for what
                  you add. The index is the front door, not a README
.agents/skills/   the nine procedures. They live here and nowhere else: do not
                  restate them. An empty skeleton means stop and name its skill
harpoon/          the code, tests/ beside it
scripts/          every check opens with a header saying what it fails on.
                  check-all.sh runs all of them plus the tests, and
                  .githooks/pre-commit runs that, so a commit is what runs them.
                  export-template.sh is the one door out to the public
                  template, and personal paths are never on its allowlist
```

## Standing behaviors

- Ask before committing, always. Edit freely, say what is uncommitted, wait.
- `pipeline.md` is the inbox for everything that needs the candidate, not just
  companies. A question goes on its Todo the turn it is raised and comes off
  the turn it is answered. `update-board` holds the rest.
- A status change updates `pipeline.md` the same turn, dated, unasked, and so
  does a `me/meetings/` note, which moves status, verdict and next action.
- A wrong verdict gets a dated correction, never an edit, and the correction
  adjudicates the row that made the call.
- After any interview, prompt for a debrief into `applications/` while it is
  fresh. A fumbled question joins open questions, and prep loads all debriefs.
- Warm paths: grep `me/network/export/Connections.csv`, never re-derive.
  Former-colleague rosters in `me/network/`, rebuilt by sweep-jobs' script.
- Cheap tailoring must not become more applications: flag volume over depth.
- Which seat to go after, and whether to override a skill's stop, are the
  candidate's calls. Recommend once, argue once if the record disagrees, then
  record the pick as theirs.
- The form outranks the posting on onsite policy, band, and written questions.
  Findings go in form-fill.md and move the row.
- They edit files mid-turn: re-read or `md5 -q` immediately before writing, and
  prefer a uniquely matching replacement.
- Every generated file in `applications/` ends with a line naming what was read
  to write it.
- No internal shorthand on a page the candidate reads: a term that has to be
  looked up elsewhere in the repo is the wrong term. Say things plainly, in the
  words a person would use out loud, and give a sloppy sentence one rewritten
  line rather than three options.

## The fact base

- `me/experience.md` holds every number, title, date, and scope claim;
  none reaches a document otherwise. Respect its "do not use" notes and
  `[check]` flags. Missing: ask, never reconstruct.
- Two markers, one job each. `[check]` means verify this before it is used, and
  it is yours to do. **`[ask: <Key>]` means only the candidate can answer, so it
  must also be a line on `pipeline.md`** carrying that short distinctive key
  word; `scripts/check-open-questions.sh` proves it. Tagging is a decision, not
  a default: an untagged open question is one you have not decided about yet.
  Open questions live in `evals/LEARNINGS.md`, not in the fact base.
- `me/positioning.md` states picks, not facts, and the fact wins on
  disagreement. A pick is theirs: ask with a recommendation, record it, let
  documents follow. A dropped or reworded claim is a pick recorded the same
  turn, layout passes included.
- Their own edit is the pick already made: sync the fact base to their wording,
  keep the source quote underneath, and do not propose restoring the old
  version. Raise it only when it contradicts a fact.
- Quote verbatim, tag who wrote each claim, flag contradictions rather
  than resolving. Public or manager numbers beat self-reported ones, and
  every number gets checked with them first.
- A discrepancy any check surfaces is a question, never doubt: the mismatch
  usually carries a story, so it joins open questions as an interview prompt.
  Check once, take their answer dated into `me/interviews/` as authority, and
  point the superseded text at it.
- `me/network/export/Positions.csv` has dates at month precision; read it
  before asking. It outranks recollection but rows overlap: ask about them.
- Push back when the record disagrees with them, not only with you; people
  are wrong about their own projects.

## Keeping the rules true

- A lesson worth keeping becomes a rule the turn it is learned: theirs, in
  `me/criteria.md`; template-general, a PR upstream. Never here, which a
  template update overwrites.
- **At the end of a skill run that taught something about how the skill should
  work, append a dated entry to `evals/LEARNINGS.md`** naming the skill and
  what happened. One file, so a shape reaches three in one place.
- **A learning is not a rule until they say so.** When a shape reaches three,
  `review-evals` puts its name, its count and a recommendation on
  `pipeline.md`'s Todo under **Decisions, the candidate's**, aimed at the skill
  that owns it or at this file if it crosses skills. They answer, the rule gets
  written, and the entry closes the same turn pointing at what it became.
- A wrong gate or verdict is a row, so it goes in the adjudication columns the
  turn it is graded: `adjudication`, `judge`, `adjudicated`, `shape`, `fix`.
  Confirmed calls too, because a gate nobody labels has no measured error rate,
  and `shape` is what makes a single noisy grade add up. What has no row,
  research quality, voice, how a skill sequences its work, goes in
  `evals/LEARNINGS.md`.
- A fix written only in a `fix` column did not happen. It belongs in the code
  or the rules, and `review-evals` reads the log back to check the claims.
- Do not name a path that does not exist.

## Keeping this file short

Under 140 lines, rules only. The rationale for a rule lives in the check that
enforces it or the skill that runs it, not here. A paragraph explaining why a
rule exists is a commit message in disguise.

