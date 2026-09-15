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

Fall 2026, start to finish in about 25 minutes:

| | |
|---|---|
| Course sections | 6,968 |
| Sections with a syllabus | 6,968 (all of them) |
| Unique documents | 4,094 |
| Documents we can read | 4,090 (99.9%) |
| Searchable text | 98.3 million characters |
| Total size | 2.2 GB on disk, 134 MB in the database |
| Failed downloads | 0 |

## Setup

You need Python 3.10+ and [uv](https://docs.astral.sh/uv/). The commands below
pull their own dependencies, so there's no virtualenv to manage.

Two extra things, each only needed by one step:

```sh
# step 3 drives a real browser
uv run --with playwright playwright install chromium

# step 4 reads PDFs and falls back to character recognition
brew install poppler ocrmypdf tesseract
```

Step 5 needs somewhere to put the data - a Postgres database. We use
[Neon](https://neon.tech). Copy `.env.example` to `.env` and put the connection
string in it.

## Running it

Five steps, in order. The first four write into `data/`; the last one loads what
they collected into Postgres.

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

**4. Pull the text out of the PDFs.** About a minute.

```sh
uv run python scripts/extract_text.py
```

**5. Load it into the database.** About 30 seconds.

```sh
uv run --with "psycopg[binary]" python scripts/load_database.py
```

Takes the connection string from `DATABASE_URL`, or from `.env`.

All of these remember what they finished. Re-running only picks up what's new
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
  extractions.jsonl         one row per PDF, recording how we read it
  pdfs/<sha256>.pdf         3,282 PDFs, named by content hash
  text/<sha256>.txt         the text from that PDF
  simple_syllabus/<id>.html rendered page, kept so we can re-parse it later
  simple_syllabus/<id>.txt  the text from that page
```

PDFs are named by a hash of their contents rather than by course. Instructors
reuse one syllabus across many sections, so this stores each document once and
lets any number of sections point at it. That collapsed 5,963 links into 3,282
actual files.

## Searching it

Two tables. `documents` holds one row per distinct syllabus and its text.
`sections` holds one row per course offering and points at its document. They
are separate because instructors reuse a syllabus across sections - one document
here covers 69 of them - so the text is stored once and shared.

The `syllabi` view joins them, which is what you normally want:

```sql
-- which departments' syllabi mention ChatGPT
select department, count(*) as sections
from syllabi
where tsv @@ websearch_to_tsquery('english', 'chatgpt')
group by department
order by sections desc;
```

**Count sections, not documents.** They are different numbers and the gap is
large: 1,382 documents mention ChatGPT, but those cover 2,256 course sections.
If you are writing "X courses do Y", you want the section count.

Searches run in well under a second across the whole corpus.

## Things we learned along the way

- **Almost nothing needs OCR.** We assumed these would be scans. In the end
  99.5% of the PDFs already had readable text inside them and only 13 needed
  character recognition. Running OCR over everything would have taken hours to
  do a worse job on the 99% that didn't need it.
- **Four syllabi are locked.** Their authors uploaded password-protected PDFs,
  so nobody can read them without the password. They're recorded as `encrypted`
  rather than quietly dropped.
- **The Simple Syllabus pages are the richer half** — around 19,000 characters
  each on average, already broken into labeled sections like the catalog
  description, instructor information and learning objectives.
- **Every section has a syllabus.** There are no gaps to chase.

The fiddly details of how UT's site behaves are in [docs/source-notes.md](docs/source-notes.md).

## What's next

- Decide whether to keep the PDF originals somewhere shared, so stories can link
  the actual document
- Backfill earlier semesters - the site goes back to Fall 2010 and the scripts
  take a semester argument
