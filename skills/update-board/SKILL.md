---
name: update-board
description: Maintain the board in board.md. Holds the rules for status, ordering, dates and the Todo list, and runs the freshness pass that re-checks whether posted jobs are still open and whether anything has changed at a watched company. Use when a row changes status, when the board has not been swept in a while, when a posting needs re-verifying, or when asked to tidy or clean up the pipeline.
---

# Update the board

`board.md` is the only place status lives. This file holds the rules for
keeping it true. The board section of `board.md` should carry what the candidate
reads and nothing more; the procedure lives here.

Write plainly. Board cells and Todo lines are read by a person, so no internal
shorthand: say "nothing on their board is worth applying to", never "gate 4".

## The statuses

Six, one per row.

- `applied`: sent, waiting to hear back. A row waiting on a person is still
  `applied`.
- `interview`: talking to them.
- `lead`: worth doing something about, and there is something to do.
- `watch`: nobody is working it and nothing is waiting on the candidate. **This costs a
  row in `source/channels.md` in the same turn**, because that row is the thing
  doing the watching. Two kinds count, and both are real:
  - a board the sweep can fetch, which is the normal case; or
  - a careers page on the **Watched by hand** list, checked by the freshness
    pass below. Slower, and only as good as the last run of the pass, but it is
    a watcher. The worked example is a Webflow careers page with no job
    board behind it, at a company the candidate named himself.

  What does not count is a board that is machine-readable where nobody has
  written the fetcher, like the Rippling and Workday rows. The fix there is the
  fetcher, not a standing manual chore, so those rows are `lead` until it is
  written. Hand-watching one instead is the candidate's call, never a default.
- `rejected`: they declined the candidate.
- `passed`: the candidate declined them.

`scripts/check-watch-rows.sh` enforces the `watch` rule. Run it after any
status change. Eight rows failed it on 2026-09-16, which is why it exists.

## The table

- One table, ordered `applied`, `interview`, `lead`, `watch`, `rejected`,
  `passed`. Order inside a status carries no ranking, so never read the top of
  the lead block as the best fit.
- **No priority column, ever.** A hand-kept priority field is a second copy of
  Todo that nothing recomputes, so it rots: sixteen rows once sat in a
  `backlog` band on the same day the sweep found live jobs at eight of them.
  What to do next is `## Todo`, rebuilt from the rows.
- What blocks a row goes in its `next` cell in prose, whatever the status: a
  question owed, a person to reach, a decision that is the candidate's.
- **Two or three sentences per `next` cell, and that is a ceiling.** The cell
  names the block; `apply/<company>/company.md` carries the research,
  the corrections and the reasoning, and it wins any disagreement. Write the
  finding into the file first, then say in the row what it means for the next
  move. One cell reached 4,500 characters because every turn appended to the
  row instead of the file, which puts the page they actually read out of reach.
- The date is the row's last touch, not its last move. It is not a staleness
  signal, because a sweep that re-finds a posting dates a row exactly like a
  meeting does.

## Todo

**This is the inbox for everything that needs the candidate, not just
companies.**
`board.md` is the one page they read, so a question about the fact base, the
resume, the criteria or a form belongs here the turn it is raised. Anywhere
else and it is a private backlog: the fact base once held twenty open questions
against three lines here.

Two lines at most per item, the ask and the reason. The detail stays in the
file it came from, which wins any disagreement, exactly as a board row does.

Four blocks, in this order:

- **Messages**: a person to contact, and what to ask them.
- **Applications, nothing blocking**: a seat to read or apply to.
- **Fact base**: what only the candidate can answer about their own record. Every
  `[ask: <Key>]` in `profile/` has a line here, and `scripts/check-open-questions.sh`
  proves it. `[check]` items are yours to verify and do not belong here.
- **Decisions, the candidate's**: a call only they can make, each with a
  recommendation. This is also where a rule change reaches them: `review-evals`
  puts a repeated shape here as one line, the shape, its count and a
  recommendation, and nothing in `learn/lessons.md` becomes a rule until they
  answer it.

**Urgent only, and that is a hard filter.** A line earns its
place by being blocked on them, ready to send, or a live seat worth acting on
now. Everything else lives in its row's `next` cell, which is where it came
from and where it is not lost. A Todo rebuilt to name every lead row is a
second copy of the board: thirty-two leads became forty-one Todo items once,
and they asked for the non-urgent ones taken back off the same day. Completeness
is the board's job. Being short enough to read is this one's.

**There is no standing-constraints block.** One existed and was removed on
on the candidate's instruction: "the audience for that is the large language
model." What is true across every row belongs in a skill, in `profile/criteria.md`,
or in the row, never on the page they read. Two things that block carried, kept
here because they are still true:

- **No cap on applications in flight.** A two-in-flight ceiling was removed on
  2026-09-16. It stopped nothing seven times running and nothing enforced it.
  `profile/criteria.md` is what keeps the volume honest: a seat at their level, a band
  topping $200K, and the operator test. Flag volume over depth; do not invent
  a limit.
- **A criteria change reopens rows, and reopened rows are unverified.** The
  2026-09-11 rewrite reopened twelve remote rows that have never been
  re-checked. Re-verifying them is the freshness pass's first job, not a line
  on their Todo.

Rebuild from the sources rather than maintaining alongside them. An item with
nothing behind it, no row and no file, does not belong here at all.

**Closing is half the job and the half that rots.** When something is answered,
take its Todo line off and close it in its home file the same turn. One
`profile/experience.md` entry read "two open items, both theirs" for a day after both
were settled, because the answer never travelled back.

## Changing a status

- Update the row the same turn, dated, unasked.
- Verdicts are append-only. A wrong one gets a dated correction underneath,
  never an edit, and the correction fills in the `adjudication` column of the
  eval row that made the call.
- A rejection also adjudicates the row that predicted it.
- Moving a company off **Swept and rejected** needs a line saying what changed.
  Usually it is `profile/criteria.md`, not the company.
- Run `./scripts/check-citations.sh`, `./scripts/check-watch-rows.sh` and
  `./scripts/check-open-questions.sh`.

## The freshness pass

Run it when the board has not been re-verified in a week, when the candidate asks
for a
tidy-up, or before any sweep. Nothing runs it automatically.

**Are the posted jobs still open?** Every `lead` row naming a specific posting
is a claim that the job exists. Re-fetch each one through `tools.boards`, or
the URL directly when there is no fetcher. A posting that has disappeared is
news: say so on the row, dated, and either find its replacement on the same
board or move the row to `watch` and catalog the board. Do not silently delete
a link that stopped resolving.

**What has changed at the watched companies?** A `watch` row is a delegation,
not a parking space, and the delegation is only as good as the last look. For
each one, check the board row's own criterion in `source/channels.md` and then ask
what else moved: a funding round, layoffs, a merger, an acquisition, a
repositioning, a person the candidate knows arriving or leaving. A company that has
repositioned is a different company, and its row is stale in a way no title
filter catches. One row sat wrong for weeks until somebody looked and found a
Series B, a new market and a named customer behind a one-line description
nobody had re-read.

**Is the metro still right?** Confirm against the company's own board, never a
digest's location field or an HQ address. Count the postings actually in range
and say the count. Three rows have been wrong this way.

**Does every row still have a next action?** A `lead` with nothing to do is
either a `watch`, if a channel can carry it, or it is finished and should be
`passed` with the reason written down.

Report what changed, what did not, and what you could not verify. "Checked and
nothing moved" is a real result worth writing, because a row nobody has looked
at and a row that has not changed look identical on the page.
