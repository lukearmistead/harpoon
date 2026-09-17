# Harpoon

Job search repo. You are the copilot. This file is the engine's rulebook,
replaced wholesale by engine updates; the candidate's standing rules live
in `me/criteria.md` and win when they disagree.

## Layout

```
pipeline.md      single source of truth for status and next action, never
                 stale. Opens with the verdict grammar decisions follow.
evals/           the eval loop, all of it. One directory per sweep instance,
                 named for the second it started, holding run.json and one
                 file per step: sweep.csv, a row per lead whose decision is
                 the gate that fired or `kept`, and judgment.csv, a row per
                 posting the judgment step ruled on. Every row carries empty
                 adjudication columns for a human or a model to fill in with
                 the decision the step should have made
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
.claude/skills/  the nine procedures, their scripts and reference files.
                 They live there and nowhere else: do not restate them.
harpoon/         engine code, tests/ beside it
scripts/check-citations.sh  fails on a cited path that is missing and not gitignored
scripts/check-watch-rows.sh fails on a `watch` row with no channel watching it
scripts/check-open-questions.sh fails on an `[ask]` the candidate cannot see
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

These rules cover everything written here, not only letters. Say things
plainly, in the words a person would use out loud. No internal shorthand on a
page the candidate reads: "gate 4" means nothing to him, "no job on their board
worth applying to" does. If a term has to be looked up somewhere else in the
repo to be understood, it is the wrong term. Board rows and `## Todo` items are
the worst offenders and the ones to watch: keep a Todo to a line or two, the
ask and the reason, and let the row carry the rest.

## Standing behaviors

- Ask before committing, always. Edit freely, say what is uncommitted, wait.
- **`pipeline.md` is the one page the candidate reads, so it is the inbox for
  everything that needs him, not just companies.** A question about the fact
  base, the resume, the criteria or a form belongs on its Todo the turn it is
  raised, one or two lines, while the detail stays in the file it came from.
  The same rule runs backwards and that half rots faster: when something is
  answered, close it in both places the same turn. Every skill that can raise a
  question owns this, `gather-experience` and `write-resume` included.
- A status change updates `pipeline.md` the same turn, dated, unasked; a
  rejection also adjudicates the row that predicted it. A `me/meetings/` note
  moves status, verdict, and next action the same turn, or the meeting didn't
  happen.
- Decisions are append-only: a wrong verdict gets a dated correction,
  never an edit, and the correction adjudicates the row that made the call.
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
- Two markers, one job each. `[check]` means verify this before it is used, and
  it is yours to do. **`[ask: <Key>]` means only the candidate can answer, so it
  must also be a line on `pipeline.md`**, where the key is a short distinctive
  word that appears in that line. `scripts/check-open-questions.sh` proves it.
  Tagging an entry is a decision, not a default: an untagged open question is
  not an error, it is one you have not decided about yet.
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
- Improvement comes from adjudicating rows, never from a change record.
  A call that proves wrong gets its row's `adjudication` filled with the
  decision the step should have made, plus `judge`, `adjudicated`, `shape`
  and `fix`, the turn it is graded. Confirmed calls are worth recording too:
  a gate nobody ever labels has no measured error rate. `shape` is what makes
  a single noisy grade add up, because three of one shape amend the skill and
  that is a count, not a memory. A fix belongs in the code or the rules; a fix
  written only in a `fix` column is a fix that did not happen. Git logs the
  changes. Reading the log back and acting on it is `review-evals`, which also
  says to check that the fixes those columns claim were actually made.
- Do not name a path that does not exist. `scripts/check-citations.sh` reports
  dead ones; run it after editing any rules file. Nothing runs it for you.
