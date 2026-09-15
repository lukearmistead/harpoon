# Pipeline

The board. Single source of truth for stage and next action. If this file is
stale, the repo is lying. There is no separate todo list.

Stages: lead, contacted, applied, interview, rejected, passed

`passed` means the candidate declined it. `rejected` means they declined the
candidate.

Decisions land as one dated line and never get edited:

    2026-09-11 sweep reject gate-5: platform seat, no operator
    2026-09-14 research verdict: apply, SF office confirmed
    2026-09-20 applied

A verdict that turns out wrong gets a dated correction under it, appended.
The record of what was decided and why, including the errors, is what a later
review of the search learns from. Stage transitions carry dates for the same
reason.

## Working now

<!-- The rows being actively worked, ordered. Each row: company, stage, the
board URL, any warm connection by name and role, and a next action naming a
person or a posting. -->

## Leads, not being worked

<!-- Surfaced and plausible, nobody is on them. -->

## Closed

<!-- Done, with the dated reason. Rejected, passed, or dissolved. -->

## Overrides taken

<!-- Every time a criteria rule was overridden, dated, with the reason. A rule
bending three times is the wrong rule, and write-criteria reads this
section to find out. -->

## Swept and rejected

<!-- One dated line per rejection in the verdict grammar above, grouped by
sweep date. Never re-surface anything here without saying what has changed.
A gate 2, 3 or 4 failure is a fact about today, so add what would bring it
back. A method or thesis failure does not come back. -->
