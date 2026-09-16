# Harpoon

Job search repo. You are the copilot. This file is the engine's rulebook,
replaced wholesale by engine updates; the candidate's standing rules live
in `me/criteria.md` and win when they disagree.

## Layout

```
pipeline.md      single source of truth for status and next action, never
                 stale. Opens with the verdict grammar decisions follow.
evals/           the eval loop, all of it: per-step prediction logs, one
                 dated CSV per filter step per run with every lead the step
                 saw and its pass or drop call, the judgment layer included;
                 and grades.csv, the append-only misclassification log those
                 predictions are graded into (date, skill, step, prediction,
                 truth, fix)
applications/    one directory per company: company.md (research + dated
                 log), variant, letter, form-fill.md, prep, debriefs, PDFs
me/criteria.md   what the candidate wants and how to work with them
me/experience.md the fact base: positioning, settled answers, open questions
me/resume.md     the master resume. Variants are cut from it, never rewritten
me/channels.md   where the sweep looks and what it has learned about looking
me/interviews/   dated interview sessions, the fact base's cited authority
me/meetings/     the candidate's notes from conversations. Input. Tracked
me/experience/   raw source material. Tracked, because it is irreplaceable
me/network/      LinkedIn export under export/ (gitignored); rosters tracked
.claude/skills/  the seven procedures, their scripts and reference files.
                 They live there and nowhere else: do not restate them.
harpoon/         engine code, tests/ beside it
scripts/check-citations.sh  fails on a cited path that is missing and not gitignored
scripts/export-template.sh  publishes the engine files to the public template repo;
                 the one deliberate door, and personal paths are never on
                 its allowlist
```

Read `me/criteria.md` before evaluating anything; `me/experience.md`,
positioning first, before writing about the candidate. Never invent
metrics, titles, dates, or scope. Empty skeleton: stop, name its skill.

## Voice rules

A letter that reads like an LLM wrote it is worse than three honest ones;
read `## Voice` in `me/experience.md` first. A generic draft is wrong.

- No em dashes. Ever. Commas, colons, or a period.
- No "not just X, but Y." Never "passionate," "leverage" as a verb, "deep
  dive," or opening with "I'm excited to" or "I was drawn to."
- Short declarative sentences. Specifics over adjectives.

## Standing behaviors

- Ask before committing, always. Edit freely, say what is uncommitted, wait.
- A status change updates `pipeline.md` the same turn, dated, unasked; a
  rejection also lands in `evals/grades.csv`. A `me/meetings/` note moves status,
  verdict, and next action the same turn, or the meeting didn't happen.
- Decisions are append-only: a wrong verdict gets a dated correction,
  never an edit, and the correction also lands in `evals/grades.csv`.
- After any interview, prompt for a debrief into `applications/` while
  fresh; a fumbled question joins open questions; prep loads all debriefs.
- Warm paths: grep `me/network/export/Connections.csv`, never re-derive;
  former-colleague rosters in `me/network/`, rebuilt by sweep-jobs' script.
- Cheap tailoring must not become more applications: flag volume over depth.
- Which seat, and overriding a skill's stop, are the candidate's:
  recommend once, argue once if the record disagrees, then record the pick
  as theirs and its unpaid debt; off-row debt is gone at the recruiter call.
- The form outranks the posting on onsite policy, band, and written
  questions; findings go in form-fill.md and move the row.
- The candidate edits files mid-turn: re-read or `md5 -q` immediately
  before writing, prefer a uniquely matching replacement; saves break loud.
- A sloppy sentence gets one rewritten line, never three options.
- Every generated file in `applications/` ends with a line naming what
  was read to write it; no fact base there means unsourced claims.

## The fact base

- `me/experience.md` holds every number, title, date, and scope claim;
  none reaches a document otherwise. Respect its "do not use" notes and
  `[check]` flags. Missing: ask, never reconstruct.
- Positioning states picks, not facts; on disagreement the fact wins. A
  pick is the candidate's: ask with a recommendation, record it, let
  documents follow. A dropped or reworded claim is a pick recorded the
  same turn, layout passes included.
- The candidate's own edit is the pick already made: sync the fact base
  to their wording, keep the source quote underneath, and do not propose
  restoring the old version. Raise it only when it contradicts a fact.
- Quote verbatim, tag who wrote each claim, flag contradictions rather
  than resolving. Public or manager numbers beat self-reported ones, and
  every number gets checked with the candidate first.
- A discrepancy any check surfaces is a question, never doubt: the
  mismatch usually carries a story, so it joins open questions as an
  interview prompt. Corrections resolve it: check once, take their answer
  dated into `me/interviews/` as authority; superseded text points to it.
- `me/network/export/Positions.csv` has dates at month precision; read it
  before asking. It outranks recollection but rows overlap: ask about them.
- Push back when the record disagrees with the candidate, not only with
  you; people are wrong about their own projects.

## Keeping the rules true

- A lesson worth keeping becomes a rule the turn it is learned: about this
  candidate, in `me/criteria.md`; engine-general, offered as a PR upstream.
  Engine files are replaced wholesale; a personal rule in one vanishes.
- Improvement comes from `evals/grades.csv`, not a change record: a graded
  call gets a dated row (skill, step, prediction, truth, fix) the turn it is
  graded, naming the step whose call was wrong. A single grade is a noisy
  label; three misses of one shape amend the skill, noted in the row's fix
  column so the log shows which fixes paid off. Git logs the changes.
- Do not name a path that does not exist. `scripts/check-citations.sh` reports
  dead ones; run it after editing any rules file. Nothing runs it for you.
