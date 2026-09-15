# Evals

The misclassification log, in the machine learning sense. Every call this
repo makes is a prediction that eventually gets graded: a company advanced
that should have failed a gate, one rejected that proved good, an
application that went out and was declined. One dated line per grade,
append-only, naming the skill that made the call.

A single grade is a noisy label: a rejection can follow a correct apply
call. Log it anyway and let the pattern decide. Three misses of the same
shape are a skill amendment waiting to be written, and the amendment gets
noted on the line that triggered it, so the log shows which fixes paid off.

<!-- One line per grade:
YYYY-MM-DD <skill>: predicted X, actual Y. Error: false positive | false
negative | none, world changed. Fix: <amendment made> | watch.

A made-up example:
2026-03-01 sweep-jobs: boarded Acme Health on an aggregator listing,
seat did not exist on Acme's own board. Error: false positive at gate 4.
Fix: gate 4 now requires the canonical URL. -->
