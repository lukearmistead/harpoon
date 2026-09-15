---
name: research-company
description: Research one company that has advanced off the board and write its company.md in applications/. Covers business model, funding and health, the data org, the seat, moat, who is on the other side of the model, and warm paths, ending in a verdict and a next action. Use when the candidate adds a company to the board, says a company advances, or asks for a deeper look at a single name.
---

# Research a company

One company at a time. Create `applications/<slug>/` and write the research
to `applications/<slug>/company.md`, then update the row on `pipeline.md`.
The directory is the company's, not the application's: the drafts and PDFs
join it later if the candidate applies, and most directories hold research
alone. This runs after sweep-jobs, on names the candidate has said should
advance. Do not run it on a list.

Read `me/criteria.md` first. If it is empty, stop and run write-criteria.
Read the existing company file if there is one, and treat its dated log as
history to append to rather than overwrite.

## The hard lines, before anything else

Whatever `me/criteria.md` marks as a stop gets checked first. If the stop
is geographic, confirm there is an office in range and that **the data or
AI org actually sits in it**, not just the company. A company fully
researched and then blocked on a question that costs five minutes to check
is the waste this rule exists to prevent.

If a hard line fails, say so, write the short version of the file, and stop.

## What the file has to answer

Follow the shape the existing `applications/<slug>/company.md` files use,
once there are any.

**Verdict, in the first line, in the verdict grammar `pipeline.md` opens
with.** A dated sentence someone can act on, plus the location. "Apply."
"Right company, wrong seat." Verdicts are append-only: one that turns out
wrong gets a dated correction under it, never an edit.

**Business model, in one sentence.** Who pays, for what, and what has to be
true for them to keep paying. If it cannot be said in a sentence, that is a
finding and it goes in the file.

**Numbers, in a table.** Funding with dates and lead investors, revenue and
growth if public, headcount, offices, reach. Mark anything unverified.

**Is it alive and growing.** Last raise and its date, layoffs, revenue
direction. Debt as the most recent round is a signal, not a footnote.

**Moat, specifically against better models.** What does a stronger
foundation model not give a competitor: proprietary corpus, physical
operations, regulatory position, contracts, workflow lock-in. "Proprietary
AI" in marketing copy is a claim, not a moat: say which one you found.

**The seat.** Title, level, band, location, onsite policy, and what the
posting actually asks for. Validate it on the company's own board first,
using `.claude/skills/sweep-jobs/ats-boards.md`, and record that URL. Quote the problem
statement rather than paraphrasing. A seat only on an aggregator is not a
seat.

**Who is on the other side of the model**, tested the way `me/criteria.md`
frames it. Whose work does the model change, does it get better for them or
only cheaper, who buys, and what number justifies the purchase. This is the
section worth writing at length.

**Fit against the corpus.** Name the specific projects in
`me/experience.md` that map to the seat's problem. Do not invent a number,
title, date or scope claim not in that file; respect its `[check]` flags.

**Against it.** The honest case. A file with no section arguing against is
not research.

**Warm paths.** From the export in `me/network/export/` and rosters beside
it, with names and roles, and who can actually reach the data org. Ask
early whether public writing exists about the work, the candidate's or
theirs: a public source is citable with no confidentiality question and
beats anything in a private folder.

**Next.** One action, naming a person or a posting.

**A dated log at the bottom**, appended to rather than rewritten.

**A closing line naming what was read to write the file.** If the fact base is
not in that line, the claims in the file are not sourced.

## What to flag rather than resolve

- Anything contradicting the thesis in `me/criteria.md`. Say it plainly.
- Contradictions between sources. Record both and say who wrote each.
- Marketing claims that cannot be verified from outside. A file that flags
  a vendor's claim as an open question gets it resolved in one conversation
  with an insider; one that settles the claim charitably never finds out.
- Anything needing a number from the candidate. Ask, never reconstruct.

## Finish

- Update the company's row on `pipeline.md`: stage, date, next action.
- If the verdict is a pass, move the row to Closed with the reason, dated.
- Run `./scripts/check-citations.sh`.
- No em dashes anywhere in the file.
