import pytest

from harpoon.contract import Posting


def make(**overrides):
    row = dict(
        company="Acme Health",
        what_it_does="Schedules home visits for health plans",
        org_location="San Francisco",
        org_location_verified=False,
        title="Staff ML Engineer",
        url="https://jobs.ashbyhq.com/acme/123",
        band="$200K-$250K",
        onsite_policy="3 days in office",
        warm_connection=None,
        source="investor",
    )
    row.update(overrides)
    return Posting(**row)


def test_round_trips():
    posting = make()
    assert posting.company == "Acme Health"
    assert posting.org_location_verified is False


def test_no_company_is_rejected():
    with pytest.raises(ValueError):
        make(company="")


def test_no_open_seat_is_representable():
    posting = make(title=None, url=None, band=None, onsite_policy=None)
    assert posting.title is None
