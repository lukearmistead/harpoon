---
name: write-application
description: Draft one application. Re-validates the seat, cuts a resume variant and a cover letter from the fact base and the settled answers, checks the draft against the barred claims, and moves the row on pipeline.md. Use when the candidate says they want to apply somewhere, asks for a cover letter or a tailored resume, or names a specific posting to go after.
---

# Write application

One seat at a time, ending in a directory at `applications/<slug>/`. Runs
last, after research-company has produced a verdict. The output could only
have been written for this seat and this person: a letter that could have
gone to three companies is a failure of this skill, not a product.

## Load first

- `me/criteria.md`, for the thesis and how the candidate wants to be
  worked with.
- `applications/<slug>/company.md`: the verdict, the open questions, who is
  on the other side of the model. Missing? Stop and run research-company.
- `me/positioning.md`, the picks in force. Empty? Stop and run
  gather-experience.
- `me/voice.md` before any prose. It holds both halves: how the candidate
  sounds, and the tells that give an LLM away.
- `me/resume.md`, the master. The variant is cut from it, never rewritten.
  **Its `## What backs each bullet` map is how you reach the fact base.** Read
  the bullet first; open the `me/experience.md` section it names only when this
  seat needs more than the bullet says, which a letter usually does for one or
  two projects and a resume variant usually does for none. `me/experience.md`
  is 1,850 lines and loading it whole to write two paragraphs is the habit this
  map exists to break.

## Step 1: Re-validate the seat. Hard gate.

Fetch the canonical URL on the company's own board (endpoints in
`.claude/skills/sweep-jobs/ats-boards.md`) and capture the exact title, location,
onsite policy, and band as posted today. Postings die in days: if the seat
is gone, say so, re-read what is on the board now, and stop.

## Step 2: Check the file is ready

Three stops: no verdict in `applications/<slug>/company.md` (research
first); an unresolved hard-line question (ask before writing; which office
the team sits in is the recurring one); volume climbing while depth per
target falls (say so: this skill is where volume creep starts).

## Step 3: Read the settled answers before drafting, not after

Open `me/positioning.md` and each project's inline picks
in `me/experience.md` and read what they say today: a cached list goes
stale. Tailoring pressure pushes toward the stronger phrasing, so the
picks stay in mind while writing, not applied as a filter at the end. They
recur in four shapes: a claim barred outright in any phrasing; a specified
lead framing; a shared credit written as sole; an inference written as a
measurement.

## Step 4: The resume variant

Cut, reorder, and delete. Never add. Every claim traces to
`me/experience.md`: a number not in there does not go in. Bullets matching
this seat's problem move first inside each role; never reorder roles or
change a title or a date. Delete what maps to no problem in the
`me/positioning.md`: a variant is shorter, not longer. The summary line
comes from `me/resume.md` as it stands; a different emphasis is a
positioning decision, so ask, and record it in `me/experience.md` first.

## Step 5: The cover letter

`me/voice.md` holds the prose rules and sets the register. Three
paragraphs beat four: the specific match, naming what the posting asks for
and the thing in the corpus that answers it, close enough that the reader
can check; why the domain is not new ground; and one real question from
the company file's open questions, which shows the posting was read rather
than matched. Quote the posting rather than paraphrasing. Do not open by
explaining the company back to itself or close by restating paragraph one.

## Step 6: The form questions

Draft the short-answer questions in the same file; they get less thought
than the letter and are read more carefully, so if one repeats the letter,
answer it differently. Record every field in
`applications/<slug>/form-fill.md`, plus anything the form said that the
posting did not: onsite days, band, location. The form outranks the posting
on all three, and what it reveals moves the row if it changes the answer.
Flag what only the candidate can answer: salary, authorization, referral.

## Step 7: The pass before submitting

A separate read of the finished draft against the source, not memory: every
number, title, date and scope claim checked back to `me/experience.md` and
its `[check]` flags; every claim against the settled answers, the pass that
catches real drift; the voice rules; then once more asking whether it could
have gone to another company. If yes, the first paragraph is wrong.

## Finish

- Write `applications/<slug>/resume.md` and
  `applications/<slug>/cover-letter.md`. Each ends with a `<!-- cut -->`
  marker, then the seat metadata and a line naming what was read to write
  it; the renderer drops everything after the marker.
- Append a dated entry to the company file's log: what was drafted, the
  open questions, the URL.
- Render with `render-application.sh <slug>` in this directory. Layout is
  `resume.typ` beside it, so the markdown stays diffable. Check the
  rendered PDF rather than trusting the marker.
- **Drafting is not applying.** Submitting is the candidate's action. The
  row's next action says the drafts are ready; the status moves to `applied`
  on the day they submit.
- Run `./scripts/check-citations.sh`. Ask before committing.

## Lessons, counting toward a third

At three of one shape this file changes. Until then the count is the point.

- **An application with no company file behind it.** One: a seat the
  candidate picked and applied to with no research done, declined before a
  recruiter screen one day later. A single grade is noise, so this is a count
  and not yet a rule.
