---
name: write-criteria
description: Elicit and maintain me/criteria.md, the statement of what the candidate is looking for and how they want to be worked with. Mines the fact base first, interviews the candidate for what it cannot answer, records the session in me/interviews/, and writes the file. Use after gather-experience on first run, when the candidate says their criteria changed, when a meeting changes what they want, or when the same rule gets overridden repeatedly on the board.
---

# Write criteria

One job: get what the candidate is actually looking for out of their head and
into `me/criteria.md`, where every other skill can test against it. The file
is theirs: this skill drafts and asks, the candidate settles.

## Load first

- `me/criteria.md` as it stands. On a rerun, the interview is about what
  changed, not a restart.
- `me/experience.md`, the fact base. What they bring shapes what they should
  want, and the methods they have shipped decide which postings are a
  mismatch. If it is empty, run gather-experience first: half of this
  interview is already answered there, and asking twice wastes the
  candidate's time.
- `me/meetings/` for anything a conversation already revealed about what they
  want. People say what they are looking for to friends before they say it to
  a file.
- `pipeline.md` overrides, if the board exists yet. A rule overridden three
  times is the wrong rule, and this skill is where it gets rewritten.

## The interview

Same mechanics as the gather-experience interview: two or three open
questions at a time that invite stories, not data points, and read the hard
lines back verbatim before they land. Draft what the fact base already
answers and read it back for confirmation instead of asking again. Cover, in
whatever order the conversation goes:

- **The hard lines.** What stops a role dead regardless of everything else:
  geography, remote, travel, industry they will not touch. Most people have
  one or two. Push on each one once: a hard line that is actually a strong
  preference weakens every real one on the page.
- **What they bring, and what they do not.** The threads that run through
  their work, and the methods in three honest tiers: shipped and deep,
  shipped once, not theirs. Draft this from the fact base. The last tier
  matters most, because it is the cheap gate that kills a flattering
  mismatch before a day gets spent on it.
- **The test that separates a good seat from a plausible one.** For one
  candidate that is who is on the other side of the model; for another it is
  ownership, or stage, or the team. Find the question they keep asking about
  every role and write it as a test with a name, so the sweep can apply it.
- **The seat itself.** Level, band expectations, IC or manager, title
  flexibility.
- **Strong preferences and tiebreakers.** Everything that is a miss to name
  out loud rather than a stop.
- **How they want to be worked with.** What the copilot should push back on,
  what is theirs alone to decide. This lands in the file too, because the
  skills read it.

## Write it down

- The interview lands in `me/interviews/YYYY-MM-DD-criteria.md`: verbatim
  answers, what is still open.
- The file itself follows the skeleton already in `me/criteria.md`: hard
  lines first, then what they bring, the named tests, the seat, strong
  preferences, tiebreakers.
- **Keep it under 100 lines, standing rules only.** Dated history and
  override counts belong on `pipeline.md`, company reasoning in
  `applications/`. A rule needing a date or a company name to make sense is a
  board entry in disguise.
- Read the hard lines back one final time before writing. They are the lines
  that stop applications, so a wrong one costs real opportunities.

## Reruns

Criteria change mid-search, and the file says it changes often. When the
candidate reports a shift, or the board shows the same override three times,
rerun the relevant part of the interview, record the session, and update the
file in the same turn. Note what changed in the session file: the history of
what was wanted is worth having when the search gets reviewed.
