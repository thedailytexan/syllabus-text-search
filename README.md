# syllabus

Collects every course syllabus UT Austin publishes for a semester and turns them
into searchable plain text.

Texas law requires public universities to post syllabi publicly, and UT does so
at its [Syllabi & CVs site](https://utdirect.utexas.edu/apps/student/coursedocs/nlogon/).
The site only lets you look up one course at a time, which makes it useless for
reporting questions like *which courses changed their attendance policy* or
*how many syllabi mention generative AI*. These scripts pull the whole semester
down so we can search across all of it at once.

## What's here so far

Fall 2026, collected in about 23 minutes:

| | |
|---|---|
| Course sections | 6,968 |
| Sections with a syllabus | 6,968 (all of them) |
| Unique documents | 4,094 |
| Total size | 2.2 GB |
| Failed downloads | 0 |

## Setup

You need Python 3.10+ and [uv](https://docs.astral.sh/uv/). The commands below
pull their own dependencies, so there's no virtualenv to manage.

One extra step for the Simple Syllabus script, which drives a real browser:

```sh
uv run --with playwright playwright install chromium
```

## Running it

Three steps, in order. Each one writes into `data/`.

**1. Build the list of syllabi.** Scans all 282 departments and records every
course section and where its syllabus lives. Takes about a minute.

```sh
uv run --with httpx --with selectolax python scripts/build_manifest.py
```

Defaults to Fall 2026. Pass a different semester as `python scripts/build_manifest.py 2026 spring`.

**2. Download the PDFs.** About 12 minutes.

```sh
uv run --with httpx python scripts/fetch_pdfs.py
```

**3. Render the Simple Syllabus pages.** About 11 minutes.

```sh
uv run --with playwright python scripts/fetch_simple_syllabus.py
```

Steps 2 and 3 remember what they finished. Re-running only picks up what's new
or previously failed, so it's safe to run them again later in the semester to
catch syllabi uploaded late.

## Why there are two fetch scripts

UT publishes syllabi two different ways, and they need completely different
handling:

- **Most are PDF files** linked with a *Download* button. We fetch them directly.
  This is 5,963 of the 6,968 sections.
- **The rest are hosted on Simple Syllabus**, linked with a *View* button. These
  aren't files at all — they're web pages that build themselves in the browser.
  Fetching the URL returns almost no text, so we open each one in a real browser
  and wait for it to finish. This is the other 1,005 sections.

Dropping the second group isn't an option: they're concentrated in a handful of
departments, so Social Work, Pharmacy and UGS would be nearly empty without them.

## What lands in `data/`

Nothing in `data/` is committed — it's 2.2 GB and the scripts rebuild it.

```
data/
  manifest.jsonl            one row per course section, with its syllabus link
  documents.jsonl           one row per PDF fetched
  simple_syllabus.jsonl     one row per page rendered
  pdfs/<sha256>.pdf         3,282 PDFs, named by content hash
  simple_syllabus/<id>.html rendered page, kept so we can re-parse it later
  simple_syllabus/<id>.txt  the text from that page
```

PDFs are named by a hash of their contents rather than by course. Instructors
reuse one syllabus across many sections, so this stores each document once and
lets any number of sections point at it. That collapsed 5,963 links into 3,282
actual files.

## Things we learned along the way

- **Almost nothing needs OCR.** We assumed these would be scans. In a sample of
  250 PDFs, 98.4% already had readable text embedded. Only around 50 documents
  in the whole corpus look like real scans. Running character recognition over
  everything would be slower *and* less accurate than just reading the text.
- **The Simple Syllabus pages are the richer half** — around 19,000 characters
  each on average, already broken into labeled sections like the catalog
  description, instructor information and learning objectives.
- **Every section has a syllabus.** There are no gaps to chase.

The fiddly details of how UT's site behaves are in [docs/source-notes.md](docs/source-notes.md).

## What's next

- Pull plain text out of the PDFs, with character recognition for the ~50 scans
- Load everything into Postgres with full-text search
