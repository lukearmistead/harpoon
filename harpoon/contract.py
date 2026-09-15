"""The posting contract.

Every sourcing agent in the sweep returns rows of this shape, and nothing
more. The fields mirror the contract stated in the sweep-jobs skill; when ATS
fetchers move into this package, they will emit it directly, and the sweep's
judgment layer will consume it unchanged.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Posting:
    company: str
    what_it_does: str          # one line
    org_location: str          # where the data or AI org actually sits
    org_location_verified: bool
    title: str | None          # None means no seat open
    url: str | None            # canonical URL on the company's own board.
                               # None with a title set means "no link found",
                               # which must never read as a live seat
    band: str | None           # as posted, verbatim
    onsite_policy: str | None  # as posted, verbatim
    warm_connection: str | None  # name and role, or None
    source: str                # which channel produced it

    def __post_init__(self) -> None:
        if not self.company:
            raise ValueError("a posting with no company is not a posting")
