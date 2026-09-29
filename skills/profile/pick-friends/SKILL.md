---
name: pick-friends
description: Record which connections in the network are friends, without ever asking the candidate to recall a name. Reads the LinkedIn export through `python3 -m tools.profile.friends`, which ranks the network best candidates first and guesses how the candidate knows each one, shows it fifteen rows at a time, and takes strikes, corrections and additions. Writes profile/network/friends.md and its line in profile/network/index.md, then offers to run gather-histories on the first fifteen. Touches no LinkedIn page. Use when the candidate says "here are my friends", "who are my friends", wants to name someone as a friend, or before the first gather-histories run.
---

# Pick friends

Profile work, done once and edited over time. `profile/network/friends.md`
is the candidate's file the way `profile/criteria.md` is theirs: this skill
lays the network out and looks everything up, and the candidate settles who
is on it. Both source skills downstream read it. gather-histories reads a
friend's past employers off LinkedIn, and research-company's Paths step
treats a second-degree person as a path only when the mutual connection is
a friend. Neither can run until the network has been picked through, so
this runs first, and it touches no LinkedIn page.

A friend is a connection who would go to bat for the candidate at a company
they left, or would introduce them to someone they know. That is the whole
test, and only the candidate can apply it.

Recall is the hard part and recognition is easy, so the candidate is never
asked who their friends are. They see a batch, and their whole job is four
kinds of sentence: strike a name, correct a how, add a name the ranking
missed, and say stop.

## Load first

- `profile/network/friends.md` as it stands, if it exists. On a rerun the
  script leaves out everyone already on it, so a batch shows only what is
  still undecided.
- `profile/network/index.md`, for which rosters sit beside the export. The
  script reads them itself; you read the index to know what "per
  roster-<company>.md" in a how column is pointing at.
- `profile/criteria.md`, Working with me, for anything the candidate has said
  about batch size or how they want to be asked.

If `profile/network/export/Connections.csv` is missing, stop and say so: the
index's header prose says how to request the export. Nothing here can run
without it.

## The procedure

**1. Show one batch.** Run `python3 -m tools.profile.friends --batch 0` and show
the rows it prints, numbered from one, as "the first batch": the flag
counts from zero and the candidate does not. Show them under the header
`| friend | how | connected on | profile |`. Fifteen rows, best candidates
first, each with the script's guess at how the candidate knows them, taken
from the strongest signal the export carries: a roster, one of the
candidate's own employers, a recommendation, an endorsement, or messages,
newest connection first on ties. `--size N` changes the fifteen when
`profile/criteria.md` says so, and a candidate who wants name and link
only gets that: the how is the script's guess and they may not want it in
front of them. Do not trim the batch, reorder it, or ask anything about it
beyond what the next step says.

**2. Stop here, for strikes.** Say it in one line: everyone in this batch
is a friend unless struck; strike by number or name, correct any how, and
say stop at any point. Then wait. A name that is not struck stands. A how the
candidate rewrites is theirs and replaces the guess word for word. "Keep
only three and four" is a strike of the other thirteen. Never ask who else
comes to mind, never ask them to list anyone: the batch is the question.

**3. Take a name the candidate adds.** When the candidate names someone the
ranking has not shown, look the name up rather than typing anything. Grep
the surname stem, not the surname, in `profile/network/export/Connections.csv`,
the way research-company does: `Brandvol` and `Brandvoll` are one letter apart
and the longer spelling misses the row. One match: take the URL and the
connection date from the row, guess the how from the company on it, and
add the row. Several matches: show them with company and date. **Stop
here**, and let the candidate say which. No match: say the export does not
carry the name and ask whether the spelling is right. **Stop here.** If the
candidate confirms it, add the
row with the how they gave and the connected-on and profile cells blank,
and say that gather-histories will have no page to load for them. A URL or
a date is looked up or left empty, never guessed.

**4. Next batch, or stop.** Unless the candidate said stop, run
`--batch 1`, then `--batch 2`, and repeat steps 1 to 3. Hold the picks in
the conversation and write the file once, at stop, because the script
counts batches over everyone not yet in the file: writing after each batch
would shift the next one. A batch that comes back struck entire is a sign
the ranking has run out of signal; say so and offer to stop, and stop if
the candidate says so. A struck name goes under a `## Struck` heading at
the bottom of the file as a bullet, `- Name`, one per line: the script
skips those too, so nobody is struck twice, and a bullet is not a table
row, so gather-histories never reads a struck name as a friend.

**5. Write `profile/network/friends.md`.** The plan's shape, and nothing
else in the file:

```
# Friends

Connections the candidate names as friends: would go to bat for them at a
company they left, would introduce them to someone they know. Picked by
striking names off ranked batches of the network; the how column is the
copilot's guess until the candidate corrects it, and the URL and date come
from the export.

| friend | how | connected on | profile |
|---|---|---|---|
| A. Friend | Acme, the analytics rebuild, 2020 | 2019-03-14 | https://www.linkedin.com/in/... |

## Struck

- B. Stranger
```

The header prose may say "how the candidate knows them", but the column is
named `how`, the header `tools/profile/friends.py` pastes its rows under.
The same script reads the first column to know who is already picked. On a
rerun, append the new rows under the existing ones and leave every existing
row as it is: a row the candidate edited by hand is a pick already made.
Read the file back to them in one line, the count and the batches read.

**6. Write the index line.** `python3 -m tools.profile.notes` lists what git
tracks, so stage the file with `git add profile/network/friends.md` first,
then run the generator. It plants `**[needs-a-summary]**` on the new line
in `profile/network/index.md`; replace the placeholder with one line that
says what the file is and how many friends it holds, run the generator
again so the wrapping matches, and prove it with
`python3 -m tools.profile.notes --check`. Ask before committing.

**7. Offer the first fifteen histories. Stop here.** End by offering to run
gather-histories now on the first fifteen friends, so the two skills run in
one sitting when the candidate wants them to. That skill is the first one
to touch LinkedIn: it checks that Claude in Chrome is connected, proposes
its batch, and waits for a go, all under
`skills/source/gather-histories/linkedin.md`, which holds the limits. Do not
run it on a yes here; say yes runs it, and let the candidate say it.

## The standing rule

**A connection the candidate calls a friend in any conversation is added
to `profile/network/friends.md` that turn, with no skill invoked.** "She is
a friend," "he would vouch for me," "I know him well" in a research run, a
meeting note, or a board update: look the name up as step 3 says and add
the row the same turn, then say so in one line. The file belongs to the
candidate the way `profile/criteria.md` does, and a friend named out loud
and not written down is the gap this skill exists to close. This rule binds
here; the candidate gates whether it also goes in `AGENTS.md`.

## Lessons

At the end of a run that taught something about how this skill should
work, append a dated entry to `learn/lessons.md` naming the skill and what
happened: a signal the ranking weighs wrong, a how that is guessed badly
across a whole batch, a batch size the candidate wanted changed. One file,
so a shape reaches three in one place.
