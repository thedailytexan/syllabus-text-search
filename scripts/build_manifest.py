"""Build the list of every syllabus UT publishes for a given semester.

Reads UT's public course documents search, one department at a time, and
records a row per course section: the course, its unique number, the
instructors, and where its syllabus lives.

Run this first. Both fetch scripts read the manifest it writes.

Usage:
    python scripts/build_manifest.py              # current default semester
    python scripts/build_manifest.py 2026 spring
"""
import asyncio, json, re, sys, time
from pathlib import Path

import httpx
from selectolax.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "manifest.jsonl"

BASE = "https://utdirect.utexas.edu/apps/student/coursedocs/courses/nlogon/"
INDEX = "https://utdirect.utexas.edu/apps/student/coursedocs/nlogon/"
UA = {"User-Agent": "DailyTexanDataDesk/0.1 (matthew.gray.marshall@utexas.edu)"}

SEMESTERS = {"spring": 2, "summer": 6, "fall": 9}
DEFAULT_YEAR, DEFAULT_SEMESTER = 2026, "fall"

# Result table columns, in order.
COLS = ["semester", "course", "unique", "title",
        "instructors", "cv", "syllabus", "survey"]
SYLLABUS_COL = COLS.index("syllabus")
CONCURRENCY = 5
RETRIES = 3


async def department_codes(client):
    """Scrape the department dropdown so we never hard-code a stale list."""
    r = await client.get(INDEX)
    select = re.search(r'(?s)name="department".*?</select>', r.text).group(0)
    return [c for c in re.findall(r'<option value="([^"]*)"', select) if c.strip()]


async def scrape(client, sema, dept, year, sem_code, rows, warnings):
    async with sema:
        params = {"year": year, "semester": sem_code, "department": dept,
                  "course_type": "In Residence", "search": ""}
        for attempt in range(RETRIES):
            try:
                r = await client.get(BASE, params=params)
                break
            except Exception as e:
                if attempt == RETRIES - 1:
                    warnings.append(f"{dept}: request failed ({e})")
                    return
                await asyncio.sleep(2 * (attempt + 1))

        # UT truncates large result sets; a department this big would need
        # splitting by course number. No department currently comes close.
        if "Limiting results" in r.text:
            warnings.append(f"{dept}: hit the 1,000 result cap - results truncated")

        for tr in HTMLParser(r.text).css("table#results_table tbody tr"):
            tds = tr.css("td")
            if len(tds) < len(COLS):
                continue
            rec = {name: tds[i].text(strip=True) for i, name in enumerate(COLS)}
            rec["dept"] = dept

            link = tds[SYLLABUS_COL].css_first("a")
            href = link.attributes.get("href", "") if link else ""
            if "simplesyllabus.com" in href:
                rec["kind"] = "view_simplesyllabus"
                rec["doc_id"] = href.rstrip("/").split("/")[-1]
            elif (m := re.search(r"/download/(\d+)/", href)):
                rec["kind"] = "download_pdf"
                rec["doc_id"] = m.group(1)
            else:
                rec["kind"] = "none"
                rec["doc_id"] = None
            rec["href"] = href
            rows.append(rec)


async def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_YEAR
    name = (sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SEMESTER).lower()
    if name not in SEMESTERS:
        sys.exit(f"semester must be one of {', '.join(SEMESTERS)}")
    sem_code = SEMESTERS[name]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows, warnings = [], []
    sema = asyncio.Semaphore(CONCURRENCY)
    t0 = time.perf_counter()

    async with httpx.AsyncClient(headers=UA, timeout=120,
                                 follow_redirects=True) as client:
        depts = await department_codes(client)
        print(f"{name.title()} {year} - scanning {len(depts)} departments\n")
        await asyncio.gather(*(scrape(client, sema, d, year, sem_code, rows, warnings)
                               for d in depts))

    with OUT.open("w") as f:
        for rec in rows:
            f.write(json.dumps(rec) + "\n")

    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    pdfs = {r["doc_id"] for r in rows if r["kind"] == "download_pdf"}
    views = {r["doc_id"] for r in rows if r["kind"] == "view_simplesyllabus"}

    print(f"sections found : {len(rows):,}")
    print(f"  PDF files    : {kinds.get('download_pdf', 0):,} -> {len(pdfs):,} unique")
    print(f"  Simple Syll. : {kinds.get('view_simplesyllabus', 0):,} -> {len(views):,} unique")
    print(f"  no syllabus  : {kinds.get('none', 0):,}")
    print(f"\nwrote {OUT.relative_to(ROOT)} in {time.perf_counter() - t0:.0f}s")
    for w in warnings:
        print(f"WARNING {w}")


asyncio.run(main())
