# Machine-readable job boards

Careers pages render in JavaScript and come back empty, so read the ATS. The
slug is usually in the apply link on the careers page; failing that, search
the ATS domain plus the company name. Slug guessing fails often: probe
variants of the company name and record the working slug in the company
file. A company hosting its own hiring page is the source of truth, and the
row says so.

| ATS | Machine-readable board |
|---|---|
| Ashby | `https://api.ashbyhq.com/posting-api/job-board/<slug>?includeCompensation=true` |
| Greenhouse | `https://boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true` |
| Lever | `https://api.lever.co/v0/postings/<slug>?mode=json` |
| SmartRecruiters | `https://api.smartrecruiters.com/v1/companies/<slug>/postings` |
| Workable | `https://apply.workable.com/api/v1/widget/accounts/<slug>?details=true` |
| Rippling | `https://api.rippling.com/platform/api/ats/v1/board/<slug>/jobs` |

Ashby returns 403 without a `User-Agent` header. Rippling answers no bands and
carries its slug in the careers page's `data-job-board-id` attribute, beside the
embed script served from static-assets.ripplingcdn.com that names the ATS.

**Read the careers page HTML before concluding a company has no board.** The
embed script names the ATS and a data attribute usually carries the slug, and
neither needs the page to render. Failing that, search the web for one real
posting and read the slug out of its apply URL: a numeric suffix defeats name
variants, which is how an 80-posting Greenhouse board at `springhealth66` was
recorded as no board at all.

**Ask the ATS for bands before going anywhere else.** Ashby returns them
with `includeCompensation=true` and Greenhouse embeds them in
`content=true`. Fund boards are still worth the trouble for the companies
whose ATS genuinely publishes nothing. Two board platforms that look
unreadable are not:

- **a16z-style boards** (`jobs.a16z.com`) server-render jobs into the
  Next.js flight payload. `?q=<text>` drives the server render; unescape
  `\"` and `raw_decode` the `"jobs":[...]` array, which carries
  `company_name`, `salary_min`/`salary_max`, `location`, `apply_url`.
  Pagination is a server action, so cover the space with narrow queries
  rather than paging.
- **Consider-backed boards** (GV's `jobs.gv.com`, Bessemer's `jobs.bvp.com`)
  expose `POST /api-boards/search-jobs`. Send `X-CSRF-Token` from
  `window.serverInitialData.csrfToken` on `/jobs` with that page's cookie,
  and a body of `{"meta":{"sequence":<cursor>},"board":{"id":"<board>",
  "isParent":true},"query":{"locations":["<city, state>"]}}`. The board id
  is `serverInitialData.fixedBoard`. Location values spell the state out
  ("San Francisco, California"; "San Francisco, CA" silently matches
  nothing), `{"remoteOnly":true}` is its own query, free-text keys are
  ignored, and `meta.sequence` pages 60 at a time against `total`.
- **Getro fund boards** (General Catalyst, Oak HC/FT, Thrive) answer
  `POST api.getro.com/api/v2/collections/<network-id>/search/jobs` with
  `Accept: application/json` (406 without it) and a body of
  `{"hitsPerPage":100,"page":N,"query":"<text>","filters":
  {"searchable_locations":["San Francisco, CA, USA"]}}`. The network id is
  `props.pageProps.network.id` in the board page's `__NEXT_DATA__`, never
  the numbers in cdn.getro.com asset URLs. Jobs carry compensation in
  cents and the canonical company-board URL.

`tools/boards.py` implements all of these; reach for it before a raw
fetch, and record what you learn here when an endpoint moves.
