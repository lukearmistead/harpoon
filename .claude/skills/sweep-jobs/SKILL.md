---
name: sweep-jobs
description: Source and filter companies for the job search. Fans agents out across the channel catalog in me/channels.md and the candidate's network export, filters the results against me/criteria.md, and puts survivors and rejections on the board. Stops before deep research, which is the research-company skill. Use when asked to find companies, sweep for open roles, check what is hiring, expand the pipeline, or evaluate names someone mentioned.
---

# Sweep jobs

Four steps: source, filter, board, stop. Source wide and reject in writing:
the answer carries the whole sourced list, each rejection naming the gate it
failed and each near miss what would change it. Talking the candidate out
of a bad application beats writing a good one.

**Load first.** `me/criteria.md` is the filter, and it changes often, so
read it every time; if it is empty, stop and run write-criteria first.
`me/resume.md` is what a job description gets compared against, and
`me/channels.md` is the channel catalog. `me/experience.md` is not needed.

**First run.** If `me/channels.md` is empty, seed it before sourcing: a
short interview about the candidate's market. Which sector, which funds lead
rounds in it, which curated or sector boards exist, whether a LinkedIn
export sits in `me/network/export/`. Write the catalog in the file's table
shape and keep going.

## Step 1: Source, in parallel

**Split agents by source, never by topic.** One agent per channel cluster
in `me/channels.md`, no overlap. The network cluster is the highest-yield
channel and the only one nobody else can run: former colleagues come from
`find-former-colleagues.py` in this directory, not a fresh derivation.
Verify any named service with a search; note what died in `me/channels.md`.

**Every agent returns the same contract, and nothing more:** company and
one line on what it does; where the data or AI org sits, marked verified or
unverified; seat title and canonical URL on the company's own board, or
"none open" (never omit it: a blank reads as a live seat); warm connection
with name and role, or none; which source produced it.

**Agents source. They do not filter.** Criteria get applied once, in the
main thread, so five agents cannot apply them five ways. Each agent verifies
rather than recalls and marks the unverified as unverified.

## Step 2: Filter

Run the gates in order, cheapest first. Stop at the first failure, name it.

1. **Already decided.** Grep `pipeline.md` and `applications/`. Never
   re-surface anything Closed or rejected without saying what changed.
2. **The hard lines.** Whatever `me/criteria.md` marks as a stop, checked
   from the posting and the company's own pages, not an aggregator.
3. **Alive and growing.** Last raise and its date, layoff history, revenue
   direction. Debt as the most recent round is a signal, not a footnote.
4. **The seat, on the company's own board.** An aggregator hit is a lead, not
   a fact. Carry the exact title, location string, onsite policy, published
   band, and the canonical URL. `.claude/skills/sweep-jobs/ats-boards.md`
   holds the machine-readable endpoints; read it before fetching.
5. **The method stack.** A posting whose method list is mostly things the
   candidate has never shipped is a mismatch regardless of domain fit.
   Cheap, so it goes before the expensive read.
6. **`me/criteria.md`, as written.** The tests and their override rule live
   there. Compare the posting's problem against `me/resume.md`, not titles.

**Read the whole board, never a title search.** The best-fitting posting
often carries a title nobody would search for, and never state a
headquarters, a funding number or a seat from memory: every error here came
from trusting a summary over a source. Lessons that cost a day each:

- **Compare a seat's band to the company's own ladder, not the market.**
  A Staff band topping out where Senior starts is a Senior seat in disguise.
- **Read the requirements section for hard gates.** A required PhD or twelve
  years is a wall, not a stretch.
- **Resolve onsite policy from sibling postings** when the target is
  silent, and trust the posting over the aggregator on onsite policy.
- **Re-validate immediately before applying.** Posting IDs churn inside a
  day, and a seat only on an aggregator is not live: ask a person.
- **A short result is a false negative.** Small for the headcount? Fetch
  the board again.
- **Name the seat category that keeps failing the same gate.** When one
  kills its third posting, write the pattern in `me/channels.md` so it gets
  rejected in one line instead of researched again.

## Step 3: Put it on the board

- Survivors go on `pipeline.md`: stage, next action naming a person or a
  posting, the board URL, any warm connection by name and role.
- **Rejections go under Swept and rejected** as one dated line in the
  verdict grammar `pipeline.md` opens with. A gate 2, 3 or 4 failure is a
  fact about today, so add what would bring it back; a gate 5 or 6 failure
  is about the thesis and does not come back. Verdicts are append-only: a
  wrong one gets a dated correction under it, never an edit.
- No open seat is not a rejection when the problem and the office are
  right: the next action there is a person.
- Run `./check-citations.sh`. Nothing runs it for you.

## Step 4: Stop

Do not roll into deep research: a swept candidate is a row, not a directory
under `applications/`. When the candidate says one advances, run
research-company on that company alone.
