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

Five, one per row.

- `applied`: sent, waiting to hear back. A row waiting on a person is still
  `applied`.
- `interview`: talking to them.
- `lead`: worth doing something about, and there is something to do.
- `rejected`: they declined the candidate.
- `passed`: the candidate declined them.

**There is no `watch`, and that is the newest rule here.** A row is one company
and one seat, so a company worth an eye on with no seat to go after has nothing
to put in the role cell: it is a row in `source/channels.md`'s `## Companies`
table instead,
which is the thing that actually does the watching, and it arrives on the board
the run a seat appears. Twenty-one rows moved that way on 2026-09-27, every one
already watched by its own channel row.

Two kinds of watching count there, and both are real: a board the sweep can
fetch, which is the normal case, and a careers page checked by hand in the
freshness pass below, which is slower and only as good as the last run of the
pass. What does not count is a machine-readable board nobody has written the
fetcher for, like the Rippling and Workday rows. The fix there is the fetcher,
not a standing manual chore.

`scripts/check-company-rows.sh` fails a `watch` row on the board, and fails a
closed company with no row in that table. Run it after any status change.

## The table

- One table, ordered `applied`, `interview`, `lead`, `rejected`, `passed`.
  Order inside a status carries no ranking, so never read the top of the lead
  block as the best fit.
- **No priority column, ever.** A hand-kept priority field is a second copy of
  Todo that nothing recomputes, so it rots: sixteen rows once sat in a
  `backlog` band on the same day the sweep found live jobs at eight of them.
  What to do next is `## Todo`, rebuilt from the rows.
- **A row is one company and one seat.** The `role` cell carries the seat's own
  title as the posting spells it, never a paraphrase and never a title nothing
  wrote down. A row whose role would be empty is not a row: it is an entry in
  `source/channels.md`'s `## Companies` table.
- **No prose in the table, and nothing below it.** What blocks a row goes in
  `apply/<company>/company.md` under `## Next`, and that file wins any
  disagreement. A company with no file yet gets the file written, not a bullet
  at the bottom of the board.
- **The table is the last thing on the page.** `scripts/check-board-shape.sh`
  fails a commit that puts a heading under it. Four sections grew there and were
  moved out on 2026-09-28: 29 companies whose only record was a bullet became 29
  files in `apply/`, the override ledger went to `learn/lessons.md`, the people
  went to `profile/network/assets.md`, and four unchecked names became rows in
  `source/channels.md`. Every one of them was written for an agent to read, on
  the one page the candidate reads. When there is no home for something, that is
  the finding: name the file it belongs in and write it there.
- That rule replaced a `next` column, and the measurement is why: it reached
  66,584 characters, 87% of the table, with 98% of what it said written nowhere
  else, so the column had become the record rather than a pointer to it. One cell
  reached 4,500 characters because every turn appended to the row instead of the
  file, which puts the page they actually read out of reach.
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
now. Everything else lives in that company's file, which is where it came
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
- Moving a company off `learn/rejections.md` needs a line saying what changed,
  and its `## Companies` row in `source/channels.md` comes out the same turn.
  Usually what changed is `profile/criteria.md`, not the company.
- Run `./scripts/check-citations.sh`, `./scripts/check-company-rows.sh` and
  `./scripts/check-open-questions.sh`.

## The freshness pass

Run it when the board has not been re-verified in a week, when the candidate asks
for a
tidy-up, or before any sweep. Nothing runs it automatically.

**Are the posted jobs still open?** Every `lead` row naming a specific posting
is a claim that the job exists. Re-fetch each one through `tools.source.boards`, or
the URL directly when there is no fetcher. A posting that has disappeared is
news: say so on the row, dated, and either find its replacement on the same
board or take the row off the board and give the company a row in
`source/channels.md`'s `## Companies` table. Do not silently delete a link that stopped resolving.

**What has changed at the watched companies?** A fetched row in
`source/channels.md` is a delegation,
not a parking space, and the delegation is only as good as the last look. For
each one, check its own criterion in `source/channels.md` and then ask
what else moved: a funding round, layoffs, a merger, an acquisition, a
repositioning, a person the candidate knows arriving or leaving. A company that has
repositioned is a different company, and its row is stale in a way no title
filter catches. One row sat wrong for weeks until somebody looked and found a
Series B, a new market and a named customer behind a one-line description
nobody had re-read.

**Is the metro still right?** Confirm against the company's own board, never a
digest's location field or an HQ address. Count the postings actually in range
and say the count. Three rows have been wrong this way.

**Does every row still have a next action?** A `lead` with nothing to do comes
off the board, either into `## Companies` if a channel can carry it, or as
`passed` with the reason written down.

Report what changed, what did not, and what you could not verify. "Checked and
nothing moved" is a real result worth writing, because a row nobody has looked
at and a row that has not changed look identical on the page.
