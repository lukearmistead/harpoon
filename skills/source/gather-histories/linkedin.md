# LinkedIn, through Claude in Chrome

The export carries a connection's current employer, first degree only.
LinkedIn's own free-tier pages carry the rest, a friend's past employers and
who sits one remove away at a company, and no other door is open: the
official API is a partner program for incorporated companies, the unofficial
library borrows the session cookie and gets accounts banned in days, and a
hosted agent logs in from a device and an IP that are not the candidate's,
behind evasion tooling. So the copilot drives Claude in Chrome, in the
candidate's own Chrome, their session, their IP, under the limits below
(decided 2026-09-21). LinkedIn detects on visit velocity, uniform timing and
volume per session, not on whose login it is, so the limits are the whole
safety of the account. `gather-histories` and research-company's Paths step
both read this file and neither restates a number from it: an executor of
either who has read only this file knows how many pages it may load and when
to stop.

## The door

Before proposing any list, call `tabs_context_mcp`. A connected browser
answers with its tabs; anything else means Claude in Chrome cannot be
reached from this session. Then say the three things to check, and stop
rather than fail mid-run: the extension is running, Chrome is signed in to
the same claude.ai account as this session, and linkedin.com is allowed in
the extension's site permissions. The check costs one call; a run that dies
on its fourth page has spent four loads and written nothing.

## Pages

Every load is `navigate` to one of the URL forms below, then
`get_page_text`. Nothing is reached by clicking: the URL carries every
filter the work needs. Read each page before loading the next; the reading
is the pacing, and a fixed interval between loads is the uniform timing
LinkedIn looks for.

**Profile, `linkedin.com/in/<slug>/`.** Headline, current role, the about
text. `get_page_text` on this page returns no Experience section, because
the section lazy-loads and the tool reads what has rendered (verified
2026-09-21). Never open a profile looking for a history.

**Experience details, `linkedin.com/in/<slug>/details/experience/`.** Every
role with title, company and dates, whole, in one read (verified
2026-09-21). A history comes from this page and only this page: one load
per friend. The slug is the profile column of the friends list under
`profile/network/`, which came from the export; it is looked up, never
typed.

**Company page, `linkedin.com/company/<slug>/`.** The numeric company id
sits in the *See all employees* link, per LinkedIn Help and lobstr.io's
search guide, not yet read in a run as of 2026-09-21. `find` locates the
link; the id is the number in its href. One load, and the id
goes into the company's Paths section in `apply/<company>/company.md`, so a
later search there costs no company page.

**People search, filtered by current company and degree.** Two forms:

    linkedin.com/search/results/people/?currentCompany=["<id>"]&network=["F"]
    linkedin.com/search/results/people/?currentCompany=["<id>"]&network=["S"]

`F` is first degree, `S` second. The first-degree form is documented and
not used by any skill (decided 2026-09-21, after the first live run): the
monthly people-search limit is the scarce resource, and a first-degree
search spends it re-checking what the export already says, when the fix for
a stale export is a fresh export, which is free. A second-degree result
names its single mutual connection inline on the results page, "<Name> is a
mutual connection" (verified 2026-09-21, Angle Health), so `through` costs
no profile open when there is one mutual; a row with several says how many
and names them only on the profile. The numeric company id is in the URL
the *51-200 employees* link on the company page lands on (verified
2026-09-21); `javascript_tool` cannot read it off the link, since the tool
blocks query strings, so click the link and read the tab URL.

## Limits

Transcribed from the design on 2026-09-21. Not to be loosened in this file:
a loosening is a line in `profile/criteria.md` under Working with me, and
the skills read it there. The one exception is the one-sitting-a-day rule,
which `tools/profile/histories.py` enforces with no flag, so changing it is a change
to the tool.

- `gather-histories`: one page per friend, fifteen friends per sitting,
  never two sittings in a day. A 25-profile batch read back to back with
  fixed two-second waits saw no visible action; fifteen with human pacing
  stays under it.
- Paths step: one company per sitting, one search, single-digit profile
  opens.

A sitting is one run of the skill. The copilot keeps the count: who has
been read, how many pages this sitting, whether a sitting already happened
today. The dated section headers in the histories file under
`profile/network/` and the dated "Searched" line of a Paths section are the
record of a sitting, so read them before proposing one. The candidate never tracks a limit; a skill at its limit
refuses to exceed it and says why.

## Stop conditions

Each of these ends the run where it stands. Say which one, write what was
read so far, and report the page count.

- **A search that returns three results is the throttle.** The free
  commercial-use limit is roughly 300 people searches a month, and three
  results per search is the symptom of hitting it: the page names three
  people, blanks the rest to "LinkedIn Member", and says "You've reached
  the monthly limit for profile searches" (seen 2026-09-21, on the fourth
  search of the month's first run, so the candidate's own browsing counts
  against the same limit). Stop the run, say so, and note it dated in
  `source/channels.md` under the Network row. No second search to confirm:
  the second search is another search.
- **A limit above is reached.** Say which one, and what would loosen it.
- **A page that is not the page asked for.** A sign-in wall, a checkpoint,
  a verification prompt, or a page whose text is empty. Loading the next
  page after one of these is the wrong move every time; the load still
  counts.
- **The door closes mid-run.** `tabs_context_mcp` stops answering, or
  `navigate` fails. Same as above: stop, say so, count what loaded.

## Never

Never send, connect, message, or click anything that is not a navigation or
a read. `tabs_context_mcp`, `navigate`, `get_page_text` and `find` are the
whole toolset on linkedin.com; a run that would need anything else is a run
that stops and asks. No follow, no endorse, no save, no dismissed dialog:
every one of those is an action on the candidate's account, in their name.
And no page dump in a tracked path. The rows a skill writes are the work
product; the page text is read once and not kept.

## Page count

Every run ends with one line of loads by kind, whatever else it reports,
and whether it finished or stopped:

    Pages loaded: 15 experience, 0 profile, 0 company, 0 search.
    Pages loaded: 1 company, 2 search, 4 profile, 0 experience.

Count every `navigate`, including one that returned a wall or nothing. The
line is how the candidate sees the limit was held without ever tracking it,
and how a lesson about LinkedIn's behavior gets a number beside it.

Record what a run teaches here, dated, the way `skills/source/sweep-jobs/ats-boards.md`
does when an endpoint moves, and a run that taught something about how a
skill should work appends a dated entry to `learn/lessons.md` as well.
