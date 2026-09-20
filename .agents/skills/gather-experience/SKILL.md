---
name: gather-experience
description: Build the experience corpus and the fact base. Reads the raw documents in me/experience/, interviews the candidate to fill the holes, records each session in me/interviews/, and writes the fact base at me/experience.md. Runs first, because the criteria and the resume are both built from what it gathers. Use when new source material arrives, when a hole in the fact base surfaces, or when the candidate corrects something already written.
---

# Gather experience

Three artifacts, each sourced from the one before it: documents the candidate
drops in `me/experience/`, the interview record in `me/interviews/`, the fact
base `me/experience.md`. This runs before write-criteria and write-resume,
because both are built from the fact base: one interview here saves the
candidate telling the same stories twice.

## Load first

- `me/positioning.md`, the picks in force, then `me/experience.md` as it
  stands.
- `me/interviews/`, for anything said since the fact base was written.
- `me/meetings/`, for market signal the fact base cannot supply on its own.

If `me/experience/` is empty and the fact base is too, say so and ask for
source material: performance reviews, self-assessments, old resumes, project
documents, published writing. The interview fills holes in a corpus; it does
not replace one.

## The pipeline

**1. Intake.** Read every document in `me/experience/`. Quote numbers verbatim
and tag who wrote each: **(mgr)**, **(self)**, **(peer)**, or public. A
manager's number or a published one beats one the candidate wrote about
themselves. Split parallel agents by source, not by topic. Summarize each
source back to the candidate before interviewing, so a misread gets caught
early.

**1b. Read the public artifacts before interviewing about them.** A repository,
a personal site, a published talk: fetch it and read it. Asking the candidate to
describe something a reader can open is a worse version of reading it, and the
answers it produces are vaguer than the artifact. A candidate said "just go to
the GitHub page" after three interview questions were queued about their own
project, and the code answered two of them better than they would have, naming the
exact model, the constrained output schema and the absence of any evaluation,
which is the thing the interview would never have surfaced because nobody
volunteers a missing eval. Then interview for only what the artifact cannot
hold: when it was built, who used it, what it changed, and why the vendor or the
approach was chosen. Record the artifact's claims as the artifact's, not the
candidate's, and flag any discrepancy with what they said as a question.

**2. Interview to fill the holes, found in two passes.** The corpus pass:
intake surfaces claims that are abstract, unquantified, or resting on a
number nobody wrote down. The coverage pass: walk the career timeline from
`me/network/export/Positions.csv` role by role and ask what happened that
no document mentions. Documents underrepresent side work, failures, and
skills the org did not value, so the corpus alone only deepens what is
already written; the walk is what finds the project nothing names. Rank
all holes by what they are worth and take the top few. Two or three open
questions per project that invite a story, not a data point. Loose in the
middle, precise at the edges: read every number back verbatim before it
lands.

**3. Write the interview down.** One dated file per session,
`me/interviews/YYYY-MM-DD-topic.md`: verbatim answers, who said what, what is
still open. The fact base cites it as authority. Then run
`python3 -m harpoon.notes` and write the session's one-line summary into
`me/interviews/index.md`, which is how anyone finds it later without opening
every file in the directory. The generator adds the line; only the summary is
yours, and `scripts/check-notes-index.sh` fails until it is written.

**4. Route what the session produced, three ways.** This is one decision per
thing learned, and collapsing it is how the fact base grew to 2,785 lines.

- **The fact goes in `me/experience.md`**, which holds every number, title,
  date and scope claim, and nothing reaches a resume that is not in it. It is
  `## Timeline` and one section per project, and nothing else. Each project's section keeps the short story too: the
  problem, what went sideways, what the candidate did. Cover letters and
  interview prep pull from it, and a fact base of bare numbers answers no
  behavioral question. `[check]` marks a claim to confirm, and contradictions
  between sources stay.
- **The pick goes in `me/positioning.md`**, stated as the rule in force and
  nothing more. No chain of drafts, no dates on who changed what, no argument
  that lost: a reader wants what to write, not how it was decided.
- **How it was settled goes in `me/interviews/`**, not into the fact base. The
  chain of drafts, the version that lost, the objection that was overruled:
  all of it dated, and named from the pick it produced so the pick is one line
  with a pointer rather than a page of history. A pick in `me/positioning.md`
  that names no file is a pick nobody can check.
- **What is still open goes in `evals/LEARNINGS.md`** under `# Open questions
  about the record`, with an `[ask: <Key>]` and a matching Todo line if only
  the candidate can answer it.

Voice is none of the three: how the candidate sounds lives in `me/voice.md`.

## When the candidate pushes back

Every document here gets read and argued with, and that is the pipeline
working. Memory surfaces more on the third pass, so a late recollection is
not weaker.

- **Check once, from curiosity, not doubt.** The candidate is the source
  of truth either way. Name what the new version contradicts and where the
  old one came from, then ask what the old source missed: a mismatch
  usually hides a story (a restarted count, a scope that grew, a number
  that changed between cycles) and the story is fact-base material. A
  second assertion wins without re-litigating.
- **Then it is the source of truth.** Record it as a dated entry in
  `me/interviews/`, leave the superseded version with a pointer to what
  replaced it, and update the fact base and everything downstream that turn.
- Elsewhere the repo flags a contradiction and leaves both standing. Not
  here.
- **An edit the candidate makes in a file is a pick, not a draft.** Sync the
  fact base to it rather than auditing it back.
- A pick is theirs: which identity leads, whether an open question is
  settled. Ask with a recommendation, record it in `me/positioning.md`,
  then let everything downstream follow.

## Finish

Read the open questions list back: what got filled, what is still open. Then
name what runs next. An empty `me/criteria.md` means write-criteria; a stale
`me/resume.md` means write-resume.

**File the questions where the candidate will see them.** This skill writes the
open questions list, and that list is not a page they read. Any entry only they
can answer gets `[ask: <Key>]` and a matching line on `pipeline.md`'s Todo under
Fact base, one or two lines, while the detail stays here. The rest keep
`[check]`, which is yours to verify. `./scripts/check-open-questions.sh` proves
the tagged ones landed.

**Close in both directions.** When an entry is answered, strike it through with
the date here and take its Todo line off the same turn. This is the half that
rots: one entry read "two open items, both theirs" for a day after both were
settled on the board and in `me/criteria.md`, because nothing carried the
answer back. Ask before committing.
