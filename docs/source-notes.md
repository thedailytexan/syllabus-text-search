# Notes on the sources

Things about UT's syllabus site and Simple Syllabus that aren't obvious and cost
real time to work out. If something breaks, start here.

## UT's course documents search

The search lives at:

```
https://utdirect.utexas.edu/apps/student/coursedocs/courses/nlogon/
```

No login is needed. It takes ordinary query parameters:

| Parameter | Notes |
|---|---|
| `year` | Four digits, e.g. `2026` |
| `semester` | `2` spring, `6` summer, `9` fall |
| `department` | Three characters from the site's dropdown |
| `course_type` | `In Residence` for regular UT courses |
| `search` | Must be present, even empty |

**The `search` parameter is the trap.** Leave it out and the site returns the
search form again with a `200 OK` and no error of any kind. It looks like a
department with no courses. Every request needs `search=` on the end.

**Department codes are padded to three characters.** Journalism is `"J  "` with
two trailing spaces, chemistry is `"CH "`. Don't trim them. `build_manifest.py`
scrapes the dropdown each run rather than keeping a list, so codes stay current.

**Results are capped at 1,000 per query.** Past that the page says *"Limiting
results to 1,000"* and silently drops the rest. This is why we query one
department at a time instead of asking for a whole semester at once. No
department is currently close to the cap — the largest is around 210 — but
`build_manifest.py` warns if one ever hits it. The fix would be splitting that
department by course number.

**Read the syllabus link out of the seventh column, not the page.** Instructor
CVs use the exact same `/download/<id>/` URL shape as syllabi. A page-wide search
for that pattern quietly collects CVs instead, and you won't notice until you
read what you downloaded. The columns are:

```
semester | course | unique | title | instructors | CV | syllabus | survey
```

**Two kinds of syllabus link**, distinguished by the button text:

- *Download* → `/download/<id>/` → returns the PDF directly
- *View* → `utexas.simplesyllabus.com/doc/<id>` → a web page, see below

## Simple Syllabus

These are Angular pages that assemble themselves in the browser. Fetching the URL
returns about 18 KB of HTML containing roughly 15 characters of visible text. The
`/pdf` and `/print` routes look promising but just redirect back into the same
app. There's a REST API behind it, but every endpoint we tried returned a 500
without credentials.

So we render them in a real browser. Two things matter:

**Send a real browser User-Agent.** With Playwright's default headless
User-Agent, the page renders completely empty and reports an error to the site's
own error tracker. The same URL with a normal Chrome User-Agent string returns
around 14,000 characters. This single line is the difference between "this site
can't be scraped" and it working fine.

**Don't wait for `networkidle`.** The app keeps a connection open, so network
activity never goes quiet and the wait times out after a full minute. Wait for
`domcontentloaded` instead, then poll the body text until it's longer than a few
hundred characters. That lands in about 3 seconds per page.

Blocking images, fonts and media with `page.route` makes it meaningfully faster
and costs nothing, since we only want text.

## Being a good neighbour

These are public records and collecting them is fine, but both sites are run by
people who didn't ask for our traffic:

- Both scripts identify themselves with a contact email in the User-Agent.
- Requests run 4–6 at a time, not unbounded.
- Everything is cached to disk and the scripts resume, so re-running doesn't
  re-fetch what we already have.

Neither site serves a usable `robots.txt` — UT's redirects to a login page and
Simple Syllabus returns a redirect — so there are no crawl directives to follow.
That's a reason to be careful rather than a licence to hammer them.
