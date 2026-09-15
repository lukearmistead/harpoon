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

Ashby returns 403 without a `User-Agent` header.

**Ask the ATS for bands before going anywhere else.** Ashby returns them
with `includeCompensation=true` and Greenhouse embeds them in
`content=true`. Fund boards are still worth the trouble for the companies
whose ATS genuinely publishes nothing. Two board platforms that look
unreadable are not:

- **a16z-style boards** (`jobs.a16z.com`) server-render jobs into the
  Next.js flight payload. `?q=<text>` and `?locations=metro:<slug>` drive
  the server render, so a plain fetch is parseable. Pagination is a server
  action, so cover the space with narrow queries rather than paging.
- **Consider-backed boards** (GV's `jobs.gv.com` among them) expose
  `POST /api-boards/search-jobs`. Send `X-CSRF-Token` from
  `window.serverInitialData.csrfToken` on `/jobs` with that page's cookie,
  and a body of `{"meta":{"sequence":<cursor>},"board":{"id":"<board>",
  "isParent":true},"query":{"locations":["<city, state>"]}}`. Filters are
  string arrays, free-text keys are ignored, `meta.sequence` pages 60 at a
  time.
