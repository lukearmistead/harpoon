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

**Where an org sits is a question for a person, never an inference.** Three
misses on this shape, each expensive: a company boarded on "SF among sites"
whose whole board turned out to be two other metros; one boarded on an SF/NY
listing that held a single engineering seat in the target metro out of 147
postings; and one read as a room in its HQ city when the CTO and the CEO live
in two others.
An HQ address plus a roster of regional directors makes a distributed company
read as in-a-room, and a posting's location field makes a single office read
as a metro. Confirm the metro against the company's own board before a lead is
boarded, count the postings that are actually in range, and where the count is
small or the answer still turns on who sits where, the next action is a
person, not another page.

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

**Moat, on two axes. Both, always.** Against better models: what does a
stronger foundation model not give a competitor: proprietary corpus,
physical operations, regulatory position, contracts, workflow lock-in.
"Proprietary AI" in marketing copy is a claim, not a moat: say which one
you found. Then against commoditization: name the thing the company
actually charges for, ask who controls access to it and whether a standard,
a regulator or a platform is working to make it routine or free. The first
axis is the right test for a product company and the wrong one for an
infrastructure company, where the moat and the threat are usually the same
fact read twice. A company whose moat is that something is hard is short
its own moat if somebody is funded to make that thing easy.

**The seat.** Title, level, band, location, onsite policy, and what the
posting actually asks for. Validate it on the company's own board first,
using `.claude/skills/sweep-jobs/ats-boards.md`, and record that URL. Quote the problem
statement rather than paraphrasing. A seat only on an aggregator is not a
seat.

**Who is on the other side of the model**, tested the way `me/criteria.md`
frames it. Whose work does the model change, does it get better for them or
only cheaper, who buys, and what number justifies the purchase. This is the
section worth writing at length.

**Fit against the corpus.** Name the specific projects that map to the seat's
problem. Start from `me/resume.md`, whose `## What backs each bullet` map names
the `me/experience.md` section behind each claim, and open only the sections
this seat actually turns on. Do not invent a number, title, date or scope claim
not in `me/experience.md`; respect its `[check]` flags.

**Against it.** The honest case. A file with no section arguing against is
not research.

**Warm paths.** From the export in `me/network/export/` and rosters beside
it, with names and roles, and who can actually reach the data org. **Grep the
surname stem, not the surname.** `Mandel` and `Mandell` are one letter apart,
and searching the longer spelling turned a first-degree connection working at
the company into a board claim that no connection existed, which then got
counted as an instance of a shape it was not.

**The grep's result is never "none," and this step ends in a question rather
than a verdict.** Three files declared no warm path and were wrong within a
day, by three different mechanisms: the person was in the candidate's own
request; the person was in the export at another company and knew the CEO;
the person worked at the company, was a former colleague, and had never been
a first-degree connection. The export carries first-degree connections and
their *current* employer, and the rosters carry whoever the candidate's own
documents happened to name, so between them they cannot see a former
colleague who never connected, anyone at one remove, or anyone the candidate
knows outside work. Write what was actually searched, "nobody in the export
works here," then **ask the candidate who might know someone there before the
file is finished.** It is one question, it is cheap, and it was never asked in
any of the three. Record the answer as theirs, dated.

**When the export returns more than one name at a company, do not pick one.**
List them with their connection dates and ask which one the candidate actually
knows. Picking on title match is the failure: one file named the Principal AI
Scientist connected three years ago because the title fit the question it wanted
answered, while the candidate's real contact was the Senior Director connected
nine years ago, sitting in the same export two rows away. The export carries no
relationship strength except the connection date, so a title match is a guess
about the wrong thing. Name them all, lead with the oldest connection, and let
the candidate choose.

Ask early whether public writing exists about the work, the candidate's or
theirs: a public source is citable with no confidentiality question and
beats anything in a private folder.

**Next.** One action, naming a person or a posting.

**A dated log at the bottom**, appended to rather than rewritten.

**A closing line naming what was read to write the file.** If the fact base is
not in that line, the claims in the file are not sourced.

## What to flag rather than resolve

- **How the company expects people to work, and whose interests it serves.**
  Ask both explicitly and put the answer in the file, quoted. Three companies in
  eight days were decided on one of these and `me/criteria.md` carries neither:
  a lobbying firm passed on whose access it sells, a company whose posting asks
  for six days a week, and a founder who says on the record that their company
  works seven and keeps mattresses in the office. A posting states hours,
  onsite expectations and intensity in the same breath as the band, and a
  founder's own interviews state the rest. This is flagged, never resolved: it
  is the candidate's call every time, and the file's job is to put it in front
  of them before a draft gets written rather than after.
- Anything contradicting the thesis in `me/criteria.md`. Say it plainly.
- Contradictions between sources. Record both and say who wrote each.
- Marketing claims that cannot be verified from outside. A file that flags
  a vendor's claim as an open question gets it resolved in one conversation
  with an insider; one that settles the claim charitably never finds out.
- Anything needing a number from the candidate. Ask, never reconstruct.

## Finish

- Update the company's row on `pipeline.md`: status, date, next action.
- If the verdict is a pass, set the status to `passed` with the reason, dated.
- **`watch` costs a channel row in `me/channels.md` in the same turn**, because
  that row is the thing doing the watching. No slug you can verify against the
  live board means no `watch`: the row is a `lead`, whatever else is true about
  it, and a board with no fetcher yet is the same answer rather than an
  exception.
- Run `./scripts/check-citations.sh` and `./scripts/check-watch-rows.sh`.
- No em dashes anywhere in the file.

## Lessons, counting toward a third

At three of one shape this file changes. Until then the count is the point.

- **A seat verdict written from the titles you searched for.** One: a
  208-posting board judged on the rows the research went looking for, while a
  named vertical holding five in-metro seats went unread. Read every title and
  record how many were read.
- **A third-party board's band is a placeholder, not the number.** One: a band
  recorded off an investor portfolio board and $45K high at the top against
  the company's own posting, which publishes bands later than
  it publishes postings. Re-read the posting before the application goes.
