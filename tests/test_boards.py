"""Parsing tests: each fetcher turns its endpoint's JSON into Lead rows.

Fixtures are minimal recorded shapes; no test touches the network.
"""

import pytest

from tools import boards
from tools.boards import ChannelError


def fake_json(payload):
    return lambda url, data=None, headers=None: payload


def test_ashby_carries_band_and_url(monkeypatch):
    monkeypatch.setattr(boards, "_json", fake_json({"jobs": [{
        "title": "Staff ML Engineer", "location": "San Francisco",
        "jobUrl": "https://jobs.ashbyhq.com/x/1",
        "compensation": {"compensationTierSummary": "$250K – $350K"}}]}))
    (lead,) = boards.ashby("x")
    assert lead.band == "$250K – $350K"
    assert lead.url == "https://jobs.ashbyhq.com/x/1"


def test_greenhouse_extracts_band_from_content(monkeypatch):
    monkeypatch.setattr(boards, "_json", fake_json({"jobs": [{
        "title": "Data Scientist", "location": {"name": "Remote, US"},
        "absolute_url": "https://boards.greenhouse.io/x/jobs/2",
        "content": "pay range is &#36;180,000 - &#36;220,000 a year"}]}))
    (lead,) = boards.greenhouse("x")
    assert lead.band == "$180,000 - $220,000"
    assert lead.location == "Remote, US"


def test_lever_formats_salary_range(monkeypatch):
    monkeypatch.setattr(boards, "_json", fake_json([{
        "text": "ML Engineer", "categories": {"location": "SF Bay Area"},
        "hostedUrl": "https://jobs.lever.co/x/3",
        "salaryRange": {"min": 200000, "max": 260000}}]))
    (lead,) = boards.lever("x")
    assert lead.band == "$200,000-$260,000"


def test_getro_reads_org_band_and_stops_paging(monkeypatch):
    monkeypatch.setattr(boards, "_json", fake_json({"results": {"count": 1, "jobs": [{
        "title": "Applied Scientist", "url": "https://jobs.fund.com/j/4",
        "location_details": [{"name": "San Francisco, CA, USA"}],
        "compensation_public": True, "compensation_amount_min_cents": 20000000,
        "compensation_amount_max_cents": 26000000,
        "organization": {"name": "Acme Health"}}]}}))
    (lead,) = boards.getro("222")
    assert lead.company == "Acme Health"
    assert lead.band == "$200,000-$260,000"
    assert lead.location == "San Francisco, CA, USA"
    assert lead.source == "getro:222"


def test_consider_lead_reads_salary_and_normalized_locations():
    lead = boards._consider_lead({
        "companyName": "Plaid", "title": "Senior ML Engineer",
        "normalizedLocations": [{"label": "San Francisco, California"}, "Remote"],
        "salary": {"minValue": 228960, "maxValue": 315360},
        "url": "https://jobs.gv.com/j/5"}, "jobs.gv.com")
    assert lead.band == "$228,960-$315,360"
    assert lead.location == "San Francisco, California; Remote"


def test_a16z_lead_formats_salary():
    lead = boards._a16z_lead({
        "company_name": "Dyno", "title": "ML Scientist",
        "location": "Remote", "salary_min": 100000, "salary_max": 200000,
        "apply_url": "https://x.com/j/6"})
    assert lead.band == "$100,000-$200,000"


def test_hn_parses_header_line(monkeypatch):
    def routed(url, data=None, headers=None):
        if "search_by_date" in url:
            return {"hits": [{"objectID": "9", "title": "Ask HN: Who is hiring? (September 2026)"}]}
        return {"children": [
            {"id": 10, "text": "Acme Health | Staff ML Engineer | San Francisco<p>LLM evals."},
            {"id": 11, "text": "no pipes here, not a header line"}]}
    monkeypatch.setattr(boards, "_json", routed)
    (lead,) = boards.hn_hiring()
    assert lead.company == "Acme Health"
    assert lead.location == "San Francisco"
    assert lead.url == "https://news.ycombinator.com/item?id=10"


def test_dead_channel_raises_not_empty(monkeypatch):
    def boom(url, data=None, headers=None):
        raise ChannelError("gone")
    monkeypatch.setattr(boards, "_json", boom)
    with pytest.raises(ChannelError):
        boards.greenhouse("dead-slug")
