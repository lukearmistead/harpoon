---
name: write-resume
description: Cut and maintain the master resume at me/resume.md from the fact base. Every claim traces to me/experience.md verbatim; holes go back to gather-experience rather than getting invented. Use when asked to write, improve, or rework the resume, or when the fact base or the positioning changes.
---

# Write resume

One job: the master at `me/resume.md`, cut from the fact base. Filling holes
in the fact base is gather-experience; cutting a variant for a seat is
write-application.

## Load first

- `me/experience.md` in full, positioning first, `## Voice` before any prose.
  If it is empty, stop and run gather-experience: nothing reaches the resume
  that is not in the fact base.
- `me/criteria.md`, for the problems every bullet gets judged against. If it
  is empty, run write-criteria first: a bullet cannot be judged against
  problems nobody has named.
- `me/resume.md` as it stands. Audit before improving: the honest finding may
  be that the numbers are fine and only the emphasis is wrong.

## The cut

Every claim traces to the fact base verbatim and carries a category below.
Every bullet maps to a problem in `me/criteria.md` or it comes out, and the
summary covers all of them. The master runs long on purpose: contact line,
summary paragraph, one section per employer with a block per title held,
education, then the sourcing line.

## What may appear where

- **Public.** Published outside the company. Leads anywhere, and beats a
  self-attested number saying the same thing.
- **Confirmed.** Sourced to a named document or person, safe in writing. Keep
  the hedge it arrived with.
- **Conversation only.** True but unchainable, usually because counts restart
  or authors differ across cycles. Say it, never write it down as one arc.
- **Confidential.** Known, sourced, competitively sensitive. Ships
  qualitative, saying it out loud is the candidate's call, and the file says
  why it moved.
- **Barred.** Never appears in any phrasing: contested, unsupported, a
  target.
- **Missing.** Ships qualitative. Never estimate a magnitude. Send it back to
  gather-experience and track it under `## Open questions` until it resolves.

## How a bullet is written

- **Lead with the problem and the result.** Method comes last or not at all.
- **Strip internal project names.** Describe the system instead, and keep
  only a name an outsider can verify from a public source.
- **Prefer the verb that says what was measured.** Name the audience it
  reached.
- **Keep honest limitations off the page.** A regression reported beside a
  gain is a strength in the fact base and the interview. On paper it reads
  as fault.
- **Plain words over insider ones.** If an outsider cannot picture it,
  rewrite.
- **Easy on the commas.** Short declaratives, per the fact base's `## Voice`.
- **Cut the trailing clause.** Most bullets end with one doing little work.

## Picks

- A change that drops or rewords a claim is a pick, the candidate's to make.
  Ask with a recommendation, record it in the positioning section of
  `me/experience.md` the same turn, then let the resume follow. A layout or
  length pass is not exempt: a claim cut during a restructure is a content
  decision wearing a layout hat.
- An edit the candidate makes themselves is the pick already made. Sync the
  fact base to their wording per gather-experience, and do not propose
  restoring the old version.
- A draft stays `[draft, confirm before using]` until read back.

## Finish

- The resume ends with a line naming what was read to write it.
- Reread it against the barred list, since drafts drift toward the stronger
  claim, then run `./scripts/check-citations.sh` and ask before committing.
