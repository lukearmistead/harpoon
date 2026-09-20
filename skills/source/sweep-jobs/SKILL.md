---
name: sweep-jobs
description: Source and filter companies for the job search. Fans agents out across the channel catalog in source/channels.md and the candidate's network export, filters the results against profile/criteria.md, and puts survivors and rejections on the board. Stops before deep research, which is the research-company skill. Use when asked to find companies, sweep for open roles, check what is hiring, expand the pipeline, or evaluate names someone mentioned.
---

# Sweep jobs

Four steps: source, filter, board, stop. Source wide and reject in writing:
the answer carries the whole sourced list, each rejection naming the gate it
failed and each near miss what would change it. Talking the candidate out
of a bad application beats writing a good one.

**Load first.** `profile/criteria.md` is the filter, and it changes often, so
read it every time; if it is empty, stop and run write-criteria first.
`profile/resume.md` is what a job description gets compared against, and
`source/channels.md` is the channel catalog. `profile/experience.md` is not needed.

**First run.** If `source/channels.md` is empty, seed it before sourcing: a
short interview about the candidate's market. Which sector, which funds lead
rounds in it, which curated or sector boards exist, whether a LinkedIn
export sits in `profile/network/export/`. Write the catalog in the file's table
shape and keep going.

## Step 1: Source

**Machine lane first, and it is the default.** Run:

    python3 -m tools.sweep

It fetches every cataloged endpoint in `source/channels.md` concurrently,
drops what `board.md` and `apply/` already decided, what earlier
runs already surfaced (`.sweep-seen.json`, gitignored; safe to lose), what
fails the location hard line, and what fails the title class, then prints
only the new leads plus a count per drop reason.

Each run writes `learn/runs/<run-id>/`, named for the second it started so two
runs in a day cannot overwrite each other. `sweep.csv` is one row per lead
and its `decision` is the gate that fired or `kept`; `run.json` holds the
gate order, the per-channel counts, the fetch errors and the revision that
produced them: the commit, whether the tree was dirty, and how many commits
had not been pushed. A dirty tree means the commit does not describe the code
that ran, so a grade taken off that run is weaker than it looks.
`python3 -m tools.sweep audit` reruns every gate against all live
postings, ignoring the seen-cache.

Nothing in the code writes `judgment.csv`, because the judgment pass is you.
Write it in the same directory with the columns
`tools/evals.py` names in `JUDGMENT_COLUMNS`, one row per posting:

    decision,why,adjudication,judge,adjudicated,shape,fix,note,company,title,url

`decision` is `board`, `near-miss` or `reject`, and `why` is your reasoning,
written now. **`note` is not yours: it belongs to whoever grades the row
later**, along with the rest of the adjudication columns, and reasoning
written there makes a grader overwrite the evidence they came to grade.

**Name the criterion in `why`, in the words `profile/criteria.md` uses.** Not a gate
number, which that file has never heard of and `CLAUDE.md` bans outright, and
not a fresh phrase each run: two runs forty minutes apart once wrote "Gate 5"
and "The expertise test" for the same call, which makes the two uncountable.
Say which test decided it and whether that test is a stop, a real objection or
a tiebreaker, because the criteria file ranks them and the whole file is the
standard here, not your read of the posting.

**A lead that reached you only because a channel criterion was too loose is not
a rejected seat.** Say so once, fix `source/channels.md`, and do not write a verdict
per posting: nineteen identical rows in one run were a single call about
sourcing, and they drown the calls about seats.

Invent a header here and `reconcile` reads nothing and reports nothing wrong.
**Then run
`python3 -m tools.sweep reconcile`**, which names every `kept` lead with
no verdict and no board row: an unjudged survivor is not pending, it is
gone, because the seen-cache remembers it and the next run drops it at
`seen-before`.

Every row carries empty adjudication columns. Fill one in when a call
proves wrong, and when it proves right: a gate nobody labels has no
measured error rate. Read the drop counts too, because a silent filter bug
hides there, and an ERROR line is a dead channel to fix or note in
`source/channels.md`, never an empty one. A first run after a long gap is big;
the next is the delta.

**Agents run only the channels a script cannot** (rows in the catalog
with no Endpoint), split by source, never by topic, no overlap:

- **Network** is the highest-yield channel and the only one nobody else
  can run: former colleagues come from `find-former-colleagues.py` in this
  directory, not a fresh derivation.
- **Recent raises** and verifying a named service need web search. The
  contract shrinks to company names, one line on what each does, and which
  source produced it. **Never board contents**: resolve each name with
  `python3 -m tools.sweep probe <company>`, which finds the ATS board
  and prints its open seats. A name that survives judgment gets its
  endpoint recorded in `source/channels.md` so it is machine-lane forever.

**Agents source. They do not filter.** Criteria get applied once, in the
main thread, so five agents cannot apply them five ways. Each agent
verifies rather than recalls and marks the unverified as unverified.

## Step 2: Filter

Run the gates in order, cheapest first. Stop at the first failure and name it.

**Name it, never number it.** These gates had numbers once and the numbers were
wrong more often than they were right: twelve verdicts said "gate 5", the method
stack, when every one of them meant the expertise test, and nineteen more hedged
"gate 5 or 6" rather than pick. A number is also banned from the board by
`CLAUDE.md`, because it means nothing to the candidate. Use these names here, in
`why`, and on `board.md`, so the same call reads the same in all three.

- **Already decided.** The machine lane precomputes this; grep
  `board.md` and `apply/` for agent-sourced names. Never
  re-surface a `rejected` or `passed` row without saying what changed.
- **The stops.** Whatever `profile/criteria.md` marks as a stop, checked
  from the posting and the company's own pages, not an aggregator. The
  machine lane pre-applies the location line textually; a posting that
  says "Remote" and means "Remote, EST only" still dies here.
- **Alive and growing.** Last raise and its date, layoff history, revenue
  direction. Debt as the most recent round is a signal, not a footnote.
- **The seat**, on the company's own board. An aggregator hit is a lead, not
  a fact. Carry the exact title, location string, onsite policy, published
  band, and the canonical URL. `.claude/skills/source/sweep-jobs/ats-boards.md`
  holds the machine-readable endpoints; read it before fetching.
- **The method stack.** A posting whose method list is mostly things the
  candidate has never shipped is a mismatch regardless of domain fit.
  Cheap, so it goes before the expensive read.
- **Who is on the other side of the model.** The expertise test and the
  operator test, which is where most rejections actually land. Compare the
  posting's problem against `profile/resume.md`, not titles.
- **The preferences**, weighed and not counted, last because they are the
  ones that get misused.

**Only what `profile/criteria.md` marks as a stop can reject a posting on its own.**
Everything else is weighed against the rest, and a rejection resting on a
preference has to say so in those words. Both of the worst calls this search has
made were this: a tiebreaker used to rank a company down as though it were a
gate, and a preference that quietly outranked the stated requirement for a seat
at or above level. The criteria file ranks its own rules. Read the rank, not just
the rule.

**Read the whole board, never a title search.** The best-fitting posting
often carries a title nobody would search for, and never state a
headquarters, a funding number or a seat from memory: every error here came
from trusting a summary over a source. Lessons that cost a day each:

- **Compare a seat's band to the company's own ladder, not the market.**
  A Staff band topping out where Senior starts is a Senior seat in disguise.
- **Read the requirements section for hard gates, then ask `profile/criteria.md`
  which of them is actually a wall.** That file is the only thing that says so,
  and it has moved: a required degree was read as a wall here for a week after
  the candidate said it was a suggestion, which cost a verdict.
- **Resolve onsite policy from sibling postings** when the target is
  silent, and trust the posting over the aggregator on onsite policy.
- **Re-validate immediately before applying.** Posting IDs churn inside a
  day, and a seat only on an aggregator is not live: ask a person.
- **A short result is a false negative.** Small for the headcount? Fetch
  the board again.
- **Name the seat category that keeps failing the same gate.** When one
  kills its third posting, write the pattern in `source/channels.md` so it gets
  rejected in one line instead of researched again.

## Step 3: Put it on the board

- Survivors go on `board.md`: status, next action naming a person or a
  posting, the board URL, any warm connection by name and role. A survivor
  with a next action is a `lead`; one worth keeping with nothing to do is a
  `watch`, which means adding its board to the `source/channels.md` watchlist in
  the same turn, because that row is what does the watching.
- **Rejections go under Swept and rejected** as one dated line in the
  verdict grammar `board.md` opens with. Failing a stop, the company's
  health or the seat is a fact about today, so add what would bring it back;
  failing the expertise or operator test is about the thesis and does not
  come back. Verdicts are append-only: a
  wrong one gets a dated correction under it, never an edit.
- **Confirm the metro against the company's own board before boarding**,
  never off the digest's location field. Three misses on this shape, each one
  a company boarded on a location string that its own board contradicted.
  Count the postings actually in range and say the count.
- No open seat is not a rejection when the problem and the office are
  right: the next action there is a person.
- **Nothing is on the board until it is on `board.md`.** A verdict that
  lives only in `judgment.csv` does not stop the row resurfacing, because
  `decided_names` reads the board.
- Run `python3 -m tools.sweep reconcile`, then
  `./scripts/check-citations.sh`. Nothing runs either for you.

## Step 4: Stop

Do not roll into deep research: a swept candidate is a row, not a directory
under `apply/`. When the candidate says one advances, run
research-company on that company alone.

## Lessons, counting toward a third

At three of one shape this file changes. Until then the count is the point.

- **A preference outranking a stop.** Two: a healthcare tiebreaker used as a
  gate to rank a company down, and an operator-test preference that quietly
  outranked the stated requirement for a seat at or above level. Read
  `profile/criteria.md`'s stops as constraints first and its preferences as the
  ranking among what survives, and say which is which out loud. At a third,
  this file gets an explicit step that sorts the criteria by force before any
  seat is compared.

- **A gate widened past the criteria file.** One: the location gate was widened
  to a whole metro on the strength of an adjudication whose `fix` cell said the
  criteria had been rewritten to match, and it never was, so the gate stood on a
  rule no file contained. It reached three places before anyone checked, the
  code, that cell, and a board row citing the file for words it does not
  contain. Judgment then spent its verdicts rejecting by hand what the gate had
  stopped dropping. When a `fix` cell says a rules file changed, open the file.

- **A fetcher that samples reads as a fetcher that enumerates.** Two: the
  Consider and Getro pagination stopping silently at the first empty page,
  and a16z returning the first page of seven ranked queries, where two runs
  three hours apart shared 155 of 162 postings and each held 7 the other
  did not. The seen-cache makes it worse, not better: a posting sampled once
  is cached forever. At a third, the fetchers get real pagination rather
  than another stderr warning.
