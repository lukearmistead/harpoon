"""Fetchers for the machine-readable discovery channels.

One function per endpoint type, each returning list[Lead]. Endpoints and
their quirks are documented in .agents/skills/sweep-jobs/ats-boards.md;
this module is that file, executable. A dead or unparseable channel raises
ChannelError so it surfaces as an error row, never as "nothing new".
"""

import html as htmllib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from harpoon.contract import Lead

UA = {"User-Agent": "Mozilla/5.0 (compatible; harpoon-sweep)"}
BAND_RE = re.compile(r"\$[\d,]+(?:\.\d+)?[Kk]?\s*(?:-|–|—|to)\s*\$?[\d,]+(?:\.\d+)?[Kk]?")


class ChannelError(Exception):
    pass


def _fetch(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf8", "ignore"), resp.headers
    except (urllib.error.URLError, TimeoutError) as e:
        raise ChannelError(f"{url}: {e}") from e


def _json(url, data=None, headers=None):
    body, _ = _fetch(url, data, {"Accept": "application/json", **(headers or {})})
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise ChannelError(f"{url}: not JSON ({e})") from e


def _band(text):
    m = BAND_RE.search(text or "")
    return m.group(0) if m else None


def ashby(slug):
    data = _json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
                 "?includeCompensation=true")
    leads = []
    for j in data.get("jobs", []):
        c = j.get("compensation") or {}
        comp = c.get("compensationTierSummary") or c.get("scrapeableCompensationSalarySummary")
        loc = j.get("location") or ("Remote" if j.get("isRemote") else "")
        leads.append(Lead(slug, j.get("title", ""), loc, comp,
                          j.get("jobUrl") or j.get("applyUrl"), f"ashby:{slug}"))
    return leads


def greenhouse(slug):
    data = _json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
    return [Lead(slug, j.get("title", ""),
                 (j.get("location") or {}).get("name", ""),
                 _band(htmllib.unescape(j.get("content", ""))),
                 j.get("absolute_url"), f"greenhouse:{slug}")
            for j in data.get("jobs", [])]


def lever(slug):
    data = _json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    leads = []
    for j in data:
        rng = j.get("salaryRange") or {}
        band = (f"${rng['min']:,}-${rng['max']:,}"
                if rng.get("min") and rng.get("max") else None)
        leads.append(Lead(slug, j.get("text", ""),
                          (j.get("categories") or {}).get("location", ""),
                          band, j.get("hostedUrl"), f"lever:{slug}"))
    return leads


def smartrecruiters(slug):
    data = _json(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings")
    leads = []
    for j in data.get("content", []):
        loc = j.get("location") or {}
        where = ", ".join(p for p in (loc.get("city"), loc.get("region")) if p)
        if loc.get("remote"):
            where = f"{where} (Remote)" if where else "Remote"
        leads.append(Lead(slug, j.get("name", ""), where, None,
                          f"https://jobs.smartrecruiters.com/{slug}/{j.get('id')}",
                          f"smartrecruiters:{slug}"))
    return leads


def workable(slug):
    data = _json(f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true")
    leads = []
    for j in data.get("jobs", []):
        where = ", ".join(p for p in (j.get("city"), j.get("state")) if p)
        if j.get("telecommuting"):
            where = f"{where} (Remote)" if where else "Remote"
        leads.append(Lead(slug, j.get("title", ""), where,
                          _band(j.get("description", "")),
                          j.get("url") or j.get("shortlink"), f"workable:{slug}"))
    return leads


GETRO_QUERIES = ("machine learning", "data science", "AI")
GETRO_LOCATIONS = ("San Francisco, CA, USA", "Remote")


def getro(network_id):
    """network_id comes from props.pageProps.network.id in the board page's
    __NEXT_DATA__; the numbers in cdn.getro.com asset URLs are not it."""
    leads, seen = [], set()
    for query in GETRO_QUERIES:
        for loc in GETRO_LOCATIONS:
            leads += [l for l in _getro_pages(network_id, query, loc)
                      if l.url not in seen and not seen.add(l.url)]
    return leads


def _getro_pages(network_id, query, loc):
    page = 0
    while True:
        body = json.dumps({"hitsPerPage": 100, "page": page, "query": query,
                           "filters": {"searchable_locations": [loc]}}).encode()
        res = _json(f"https://api.getro.com/api/v2/collections/{network_id}"
                    "/search/jobs", body,
                    {"Content-Type": "application/json"}).get("results", {})
        jobs = res.get("jobs", [])
        yield from (_getro_lead(j, network_id) for j in jobs)
        page += 1
        if not jobs or page * 100 >= min(res.get("count", 0), 1200):
            if page * 100 < min(res.get("count", 0), 1200):
                print(f"getro:{network_id}: short result, {page * 100} of "
                      f"{res.get('count')} for {query!r}; rerun to catch the rest",
                      file=sys.stderr)
            return


def _getro_lead(j, network_id):
    where = "; ".join(d.get("name", "") for d in j.get("location_details", []))
    if j.get("work_mode") == "remote":
        where = f"{where} (Remote)" if where else "Remote"
    lo, hi = j.get("compensation_amount_min_cents"), j.get("compensation_amount_max_cents")
    band = (f"${lo // 100:,}-${hi // 100:,}"
            if j.get("compensation_public") and lo and hi else None)
    return Lead((j.get("organization") or {}).get("name") or "?", j.get("title", ""),
                where, band, j.get("url"), f"getro:{network_id}")


CONSIDER_SF = ["San Francisco, California", "Berkeley, California",
               "Oakland, California"]


def consider(arg):
    """arg is host[:board-id], e.g. jobs.gv.com:gv. Locations are spelled
    "City, FullStateName"; free-text keys are ignored by the endpoint."""
    host, _, board = arg.partition(":")
    page, headers = _fetch(f"https://{host}/jobs")
    cookie = "; ".join(c.split(";")[0] for c in (headers.get_all("Set-Cookie") or []))
    tok = re.search(r'csrfToken["\']?\s*[:=]\s*["\']([^"\']+)', page)
    if not tok:
        raise ChannelError(f"{host}: no csrfToken on /jobs")
    board = board or (re.search(r'"fixedBoard"\s*:\s*"([^"]+)"', page) or [None]).group(1)
    hdrs = {"Content-Type": "application/json", "X-CSRF-Token": tok.group(1),
            "Cookie": cookie, "Referer": f"https://{host}/jobs"}
    leads, seen = [], set()
    for query in ({"locations": CONSIDER_SF}, {"remoteOnly": True}):
        leads += [l for l in _consider_pages(host, board, hdrs, query)
                  if l.key() not in seen and not seen.add(l.key())]
    return leads


def _consider_pages(host, board, hdrs, query):
    cursor = 0
    while cursor < 1500:
        body = json.dumps({"meta": {"sequence": cursor},
                           "board": {"id": board, "isParent": True},
                           "query": query}).encode()
        data = _json(f"https://{host}/api-boards/search-jobs", body, hdrs)
        jobs = data.get("jobs", [])
        yield from (_consider_lead(j, host) for j in jobs)
        cursor = (data.get("meta") or {}).get("sequence", cursor + len(jobs))
        if not jobs or cursor >= min(data.get("total", 0), 1500):
            if cursor < min(data.get("total", 0), 1500):
                print(f"consider:{host}: short result, {cursor} of "
                      f"{data.get('total')}; rerun to catch the rest", file=sys.stderr)
            return


def _consider_lead(j, host):
    locs = [L.get("label", str(L)) if isinstance(L, dict) else str(L)
            for L in j.get("normalizedLocations") or j.get("locations") or []]
    where = "; ".join(locs)
    if j.get("remote"):
        where = f"{where} (Remote)" if where else "Remote"
    sal = j.get("salary") or {}
    band = (f"${sal['minValue']:,}-${sal['maxValue']:,}"
            if sal.get("minValue") and sal.get("maxValue") else None)
    return Lead(j.get("companyName") or "?", j.get("title", ""), where, band,
                j.get("url") or j.get("applyUrl"), f"consider:{host}")


def hn_hiring(_arg=""):
    hits = _json("https://hn.algolia.com/api/v1/search_by_date"
                 "?query=%22who%20is%20hiring%22&tags=story,author_whoishiring")
    stories = [h for h in hits.get("hits", []) if "hiring" in h.get("title", "").lower()]
    if not stories:
        raise ChannelError("hn: no who-is-hiring thread found")
    thread = _json(f"https://hn.algolia.com/api/v1/items/{stories[0]['objectID']}")
    leads = []
    for c in thread.get("children", []):
        text = re.sub(r"<[^>]+>", "\n", htmllib.unescape(c.get("text") or ""))
        head = next((l for l in text.splitlines() if l.strip()), "")
        parts = [p.strip() for p in head.split("|") if p.strip()]
        if len(parts) < 2:
            continue
        loc = next((p for p in parts[1:] if LOCATION_HINT.search(p)),
                   "Remote" if re.search(r"(?i)\bremote\b", text) else "")
        leads.append(Lead(parts[0], " | ".join(parts[1:3]), loc, _band(text),
                          f"https://news.ycombinator.com/item?id={c['id']}", "hn"))
    return leads


LOCATION_HINT = re.compile(
    r"(?i)remote|\bSF\b|san francisco|bay area|berkeley|oakland|new york|\bNYC\b|"
    r"london|seattle|austin|boston|denver|chicago|\bLA\b|los angeles|toronto|hybrid|onsite")


A16Z_QUERIES = ("machine learning", "data scientist", "data science",
                "applied scientist", "AI engineer", "research scientist", "LLM")


def a16z(_arg=""):
    """jobs.a16z.com server-renders jobs into its flight payload; pagination
    is a server action, so narrow queries cover the space instead."""
    leads, seen, failures = [], set(), []
    for q in A16Z_QUERIES:
        page, _ = _fetch("https://jobs.a16z.com/jobs?q=" + urllib.parse.quote(q))
        text = page.replace('\\"', '"')
        i = text.find('"jobs":[')
        try:
            jobs, _ = json.JSONDecoder().raw_decode(text[i + len('"jobs":'):])
        except (json.JSONDecodeError, ValueError):
            failures.append(q)
            continue
        leads += [_a16z_lead(j) for j in jobs
                  if j.get("id") not in seen and not seen.add(j.get("id"))]
    if failures and not leads:
        raise ChannelError(f"a16z: flight payload unparseable for {failures}")
    return leads


def _a16z_lead(j):
    lo, hi = j.get("salary_min"), j.get("salary_max")
    return Lead(j.get("company_name") or "?", j.get("title", ""),
                j.get("location", ""), f"${lo:,}-${hi:,}" if lo and hi else None,
                j.get("apply_url"), "a16z")


FETCHERS = {"ashby": ashby, "greenhouse": greenhouse, "lever": lever,
            "smartrecruiters": smartrecruiters, "workable": workable,
            "getro": getro, "consider": consider, "hn": hn_hiring, "a16z": a16z}
