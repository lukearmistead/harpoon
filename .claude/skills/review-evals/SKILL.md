---
name: review-evals
description: Review the eval log and act on what it shows. Grades the decisions recorded in evals/<run-id>/, counts shapes toward the third that amends a skill, and puts the fix in the code or the rules where it belongs. Use when asked to review the evals, improve how a step judges, check whether a gate is working, or when a call has proven wrong and needs recording.
---

# Review the evals

The loop only improves by adjudicating rows. This file is how to read what the
runs recorded, decide what it means, and change something because of it.

Two failure modes shape every step below. A finding written before the counting
is usually ranked wrong. And a fix recorded in a `fix` column is not a fix.

## Load first

`me/criteria.md`, before the first CSV. It is the standard every judgment call
gets graded against, not your own read of a posting, and it is the candidate's
file rather than a description of the code. Read it early and read the whole
thing: the review this file came from found its largest problem in the criteria
file, not in any eval row, and would have missed it by starting with the data.

`CLAUDE.md` holds the adjudication rules. This file does not restate them.

## Step 1: Check that the recorded fixes happened

The highest-yield move, and it goes first because everything downstream trusts
these files. Every `fix` cell that names a file is a claim. Open the file.

**Read the rules file's history, not only its current text.** The question is
"has this file ever said that," which a `git log -p` answers and a read does
not. One review found a location gate widened well past the candidate's stated
rule on the strength of a `fix` cell saying the criteria had been rewritten to
match. It never had, in any revision. The phantom rule had reached three places
by then: the gate, that cell, and a board row citing the criteria file for words
it does not contain, and the judgment step was quietly paying the cost every run
by rejecting those postings one at a time by hand.

Check the claims that look fine too. In the same review two other `fix` cells
claimed reference files had been amended, and both had been, exactly as written.
Knowing which claims hold is what makes the failures legible.

## Step 2: Count before concluding

`python3 -m harpoon.sweep grades` is the standing report: rows and calls per
decision, confirmed against overturned, and every shape with its count. Beyond
it, per run and by hand: how many decisions carry a recorded reason at all, how
many are graded, and how many rows are one call wearing many hats.

**Identical text across rows is one call, not many.** Nineteen rows in one run
carried a byte-identical note, and it was a single finding about a sourcing
filter being too loose, filed as nineteen rejections. Counting rows there says
the step is busy; counting calls says what it actually decided.

A ranked list written before this counting was wrong twice in the review that
produced this file. Write the ranking after.

## Step 3: Name where the loop has no instrument

Grades get written about things a person looked at, and nobody looks at what was
dropped. So every drop gate's measured error rate reads zero, and the zero means
nothing was measured rather than nothing was wrong. Thousands of postings died
at a title filter that has never been sampled.

Say this plainly rather than reporting the zero. Then name what sampling would
cost, because a recall check is work every run and that makes it the candidate's
call, not a default.

## Step 4: Replay a change against the runs already logged

The eval directories are a corpus, so a proposed gate change can be run against
them before anyone trusts it. Report the before and after counts.

**Check what newly dies, not only what survives.** Confirming that the bad rows
are gone is half a verification. An allowlist gate makes every unnamed town a
silent false negative, so grep the new drop rows for what should have passed.
This step exists because a review did the survivor half, called it verified, and
had the other half pointed out.

## Step 5: Grade, including the calls that were right

Fill the adjudication columns on the row whose decision it is about, the turn it
is graded. A gate nobody labels has no measured error rate, so a confirmed call
is data and belongs in the log next to the misses.

- **Put the grade on the row that made the call.** A location decision belongs
  on the sweep row that kept the lead, not on the judgment row that rejected it
  by hand afterwards. The second is the symptom.
- **Choose a `shape` an earlier row would have chosen.** Free text that never
  collides counts to one forever, and three of one shape is what amends a skill.
  Read the shapes already in the log before inventing one.
- **A decision is append-only.** A cell that is wrong gets a dated correction
  appended, never an edit, and that holds for the grading cells too.

## Step 6: Put the fix where it lives, then check what cites it

Code or rules, and the `fix` column only describes it. Then:

- **Grep before renaming anything.** Skills and reference files name each other's
  sections, and a rename that breaks those references defeats the change it is
  part of. A proposed heading rename was caught this way, cited in two places.
- **A test pins a rule that drifted once.** The drift is the evidence that
  nothing was holding it.
- Run the check scripts. Nothing runs them for you.

## Scope, and what is not yours

- Engine files ship in the public template, so no company names, no candidate
  name, and no run identifiers in a comment. Commits split on that boundary.
- `me/criteria.md` is the candidate's. Findings about it are a proposed diff and
  a line on `pipeline.md`, never an edit.
- Recorded verdicts on the board are picks. Rewording them, even to fix
  shorthand the rules ban, is the candidate's yes.
- Ask before committing.

## Precision, because a durable doc outlives the session

Recount every number before it goes into anything written down. One review put
"42% of the run's judgment work" into a document and the honest version was
"seven of nine leads drew a verdict citing geography, two of them on geography
alone." The sharper number was the stronger finding. Overstating a real result
is how a real result gets discounted.

## Lessons, counting toward a third

At three of one shape this file changes. Until then the count is the point.

- **A rule cited by a file that never contained it.** One: a gate, a `fix` cell
  and a board row all cited the criteria file for a rule absent from every
  revision of it. At a second, step 1 stops being a step and becomes a check
  script that greps cited rules against their source.
