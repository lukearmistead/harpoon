# Network

Warm paths and a company source, from the LinkedIn export.

Request the export at LinkedIn > Settings > Data privacy > Get a copy of your
data, choosing the larger archive so Connections.csv and Positions.csv are in
it. Unzip it into `me/network/export/`, which is gitignored: it is
re-exportable, thirty-odd noisy CSVs, and tracking it would bury the work
product. Everything derived from it, rosters above all, lives beside it here
and is tracked.

Two files matter most:

- `me/network/export/Connections.csv` holds every connection's name and current employer.
  Current only: who used to be a colleague has to be derived, and
  `find-former-colleagues.py` in the sweep-jobs skill does that from the corpus in
  `me/experience/`. Its output gets reviewed by hand into
  `roster-<company>.md` files here.
- `me/network/export/Positions.csv` holds the candidate's own titles and dates at month
  precision, contemporaneously entered. It outranks recollection but is not
  clean: rows overlap and the current role has no end date. Reconcile against
  the fact base and flag what disagrees.
