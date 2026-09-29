---
name: gather-histories
description: Read where the candidate's friends have worked and turn the employers into names for the sweep. Reads profile/network/friends.md for the next batch, each friend's experience page on LinkedIn through Claude in Chrome under the limits in skills/source/gather-histories/linkedin.md, and writes one section per friend to profile/network/histories.md, ending with the employers board.md has not decided and an offer to probe them. The candidate's part is one word at the gate. Use when the candidate says "where have my friends worked", "gather histories", "read my friends' histories", or after pick-friends offers it.
---

# Gather histories

Histories to companies. pick-friends writes `profile/network/friends.md`;
this skill reads the friends in it that have no history yet and appends
what it finds to `profile/network/histories.md`. Then the
employers go to the sweep as names, because judging a company is
sweep-jobs' job and nothing here judges one. The span is ten years by
default; the candidate can say a different span when they run it, and the
section header records the span used, so a later read knows what was
looked at.

This is the skill that loads the most pages, so the rulebook sits beside
it. `skills/source/gather-histories/linkedin.md` holds the URL forms, the
page that carries the history, the limits, and the stop conditions. This
file restates none of its numbers: an executor who has read it knows how
many pages may load and when to stop, and `python3 -m tools.profile.histories`
keeps the count, so the candidate never does.

## Load first

- `skills/source/gather-histories/linkedin.md`, whole, every run. The
  limits and the stop conditions are there and nowhere else.
- `profile/criteria.md`, the Working with me section, for any loosening of
  those limits the candidate has written.
- `profile/network/histories.md` as it stands, if it exists: the dated
  section headers are the record of every sitting so far.

If `profile/network/friends.md` does not exist, stop and say so: there are
no friends to read yet, and pick-friends is what writes them.

## The run

**1. Check the door.** Call `tabs_context_mcp` before proposing anything.
Anything but a connected browser means Claude in Chrome cannot be reached
from this session: say the three things the rulebook names to check, and
stop. A run that dies mid-batch has spent its loads and written nothing.

**2. Ask the tool for the batch.** Run:

    python3 -m tools.profile.histories next

It prints the friends with no section yet, in the file's order, capped at
the sitting's size, one name and profile slug per line. **If it exits 1,
refuse to go on,** and say why in the candidate's terms: a friend's history
was already read today, and the rulebook's Limits section does not allow
another sitting today, so the next batch is tomorrow's. Nothing loosens
that here. A larger batch is a line in `profile/criteria.md` and `--size N`
on the command; the one-a-day rule is the tool's and has no flag, so a
second sitting is a change to `tools/profile/histories.py`, not a line. If it
prints nothing and exits 0, every friend has a history already: say so and
end the run without a page.

**3. Show the batch.** The names the tool printed, numbered, with the span
about to be read stated once above them. The candidate says go, or strikes
a name that should wait; a struck name stays in the friends file and comes
up next time. A friend whose profile cell is blank has no page: the tool
leaves them off the batch, and if one is on it anyway, strike it yourself
and say so. Never open a profile page to fill in the list: the slug is
the profile column of `profile/network/friends.md`, looked up, never typed.
**Stop here** until the candidate says go: no page loads before that word.
The gate is one word from them with the list in front of it, and
everything else is the copilot's to carry.

**4. Read the pages.** For each friend left on the list, `navigate` to the
experience-details URL form in the rulebook, then `get_page_text`, and read
what came back before loading the next. The reading is the pacing. A
profile page is never the page for a history, and every stop condition in
the rulebook ends the run where it stands: say which condition, write the
sections for what was read, and report the page count. Nothing on
linkedin.com is clicked, sent, saved or dismissed.

**5. Write the sections.** One per friend, appended to
`profile/network/histories.md`, in this shape and no other, because
`tools/profile/histories.py` parses it:

    ## <friend>, read <YYYY-MM-DD>, <span>

    <profile URL>, connected <YYYY-MM-DD>

    | company | title | from | to |
    |---|---|---|---|
    | <company> | <title> | <YYYY-MM> | now |
    | <company> | <latest title>, and <N> prior | <YYYY-MM> | <YYYY-MM> |

Every employer with a month inside the span, a role that began before the
span and ended inside it included; none that ended before the span began,
and the span in the header. Dates at month precision; `now` for a current
role. Several titles at one employer collapse into one row spanning the
whole stay, the latest title first and the count of earlier ones after it.
The URL and the connected date come from the friend's row in
`profile/network/friends.md`, not from the page. The page text is read once
and not kept: the rows are the work product, and a page dump in a tracked
path is what the rulebook's Never section forbids.

The first section ever creates the file, under a `# Histories` title and
one line saying what the file is; `tools/profile/histories.py` reads only the
`## ` sections, so the top matter is the candidate's to word. When it does,
stage it with `git add` and run `python3 -m tools.profile.notes`, which adds
a line for it to `profile/network/index.md` with a placeholder summary;
replace the placeholder with one line saying what the file is, because
`scripts/check-notes-index.sh` fails until a person writes it. Every later
run finds the line already there.

**6. Hand the employers to the sweep.** Run:

    python3 -m tools.profile.histories employers

It prints every company across every history that `board.md` has not
decided, most friends first, each with which friends were there and when.
Show that list whole. A company on it is a name for the sweep, not a
company for research-company, and its paths do not get mapped in this run:
a company that a history surfaces goes to the sweep as a name.

**7. Report the page count.** One line of loads by kind, in the rulebook's
form, whether the run finished or stopped, counting every `navigate`
including one that returned a wall or nothing. It is how the candidate sees
the limit was held without ever tracking it.

**8. Offer to probe.** Each new name is an argument for
`python3 -m tools.source.sweep probe <company>`, which finds its board and prints
its open seats; a name that survives judgment gets its endpoint recorded
in `source/channels.md` by sweep-jobs, not here. Offer, and wait: whether
to probe now, and which names, is the candidate's call.

## Finish

Two records, in two places. What the run taught about LinkedIn's behavior,
a page that rendered differently, a wall, a form that moved, goes into
`skills/source/gather-histories/linkedin.md`, dated, so the next run
starts from it. A run that taught something about how this skill should
work appends a dated entry to `learn/lessons.md` naming the skill and what
happened, per `AGENTS.md`. Ask before committing.
