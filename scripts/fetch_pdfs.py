"""Fetch every downloadable syllabus PDF from UT's public course documents app.

Content-addressed: files land at data/pdfs/<sha256>.pdf, so byte-identical
syllabi shared across sections are stored once. Resumable - a re-run skips
anything already recorded in data/documents.jsonl.
"""
import asyncio, hashlib, json, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

import httpx

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "data" / "pdfs"
MANIFEST = ROOT / "data" / "manifest.jsonl"
RECORDS = ROOT / "data" / "documents.jsonl"

BASE = "https://utdirect.utexas.edu/apps/student/coursedocs/courses/nlogon/download/"
UA = {"User-Agent": "DailyTexanDataDesk/0.1 (matthew.gray.marshall@utexas.edu)"}
CONCURRENCY = 6
RETRIES = 3


def load_targets():
    ids = {}
    for line in MANIFEST.read_text().splitlines():
        r = json.loads(line)
        if r["kind"] == "download_pdf":
            ids.setdefault(r["doc_id"], r["course"])
    return ids


def already_done():
    if not RECORDS.exists():
        return set()
    done = set()
    for line in RECORDS.read_text().splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("ok"):
            done.add(rec["doc_id"])
    return done


async def fetch(client, sema, doc_id, course, out, counters):
    async with sema:
        for attempt in range(RETRIES):
            try:
                r = await client.get(f"{BASE}{doc_id}/")
                if r.status_code >= 500:
                    raise httpx.HTTPError(f"server {r.status_code}")
                break
            except Exception as e:
                if attempt == RETRIES - 1:
                    out.append({"doc_id": doc_id, "ok": False, "error": str(e)})
                    counters["failed"] += 1
                    return
                await asyncio.sleep(2 * (attempt + 1))

        body = r.content
        ctype = r.headers.get("content-type", "").split(";")[0]
        cd = r.headers.get("content-disposition", "")
        m = re.search(r"filename=(.+)", cd)
        orig = unquote(m.group(1).strip('"')) if m else None

        if r.status_code != 200 or not body:
            out.append({"doc_id": doc_id, "ok": False,
                        "error": f"http {r.status_code}, {len(body)}b"})
            counters["failed"] += 1
            return

        sha = hashlib.sha256(body).hexdigest()
        path = PDF_DIR / f"{sha}.pdf"
        if path.exists():
            counters["dupe"] += 1
        else:
            path.write_bytes(body)
            counters["new"] += 1
        counters["bytes"] += len(body)

        out.append({"doc_id": doc_id, "ok": True, "sha256": sha,
                    "path": f"data/pdfs/{sha}.pdf", "bytes": len(body),
                    "content_type": ctype, "original_filename": orig,
                    "is_pdf": body[:5] == b"%PDF-", "sample_course": course,
                    "fetched_at": datetime.now(timezone.utc).isoformat()})

        n = counters["new"] + counters["dupe"] + counters["failed"]
        if n % 100 == 0:
            el = time.perf_counter() - counters["t0"]
            print(f"  {n:>5}/{counters['total']}  {el:6.0f}s  "
                  f"{n/el:4.1f}/s  {counters['bytes']/1e9:5.2f}GB", flush=True)


async def main():
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    targets = load_targets()
    done = already_done()
    todo = {k: v for k, v in targets.items() if k not in done}

    print(f"unique PDFs in manifest : {len(targets):,}")
    print(f"already fetched         : {len(done):,}")
    print(f"to fetch now            : {len(todo):,}\n")
    if not todo:
        print("nothing to do."); return

    out, sema = [], asyncio.Semaphore(CONCURRENCY)
    counters = {"new": 0, "dupe": 0, "failed": 0, "bytes": 0,
                "total": len(todo), "t0": time.perf_counter()}
    limits = httpx.Limits(max_connections=CONCURRENCY, max_keepalive_connections=CONCURRENCY)
    async with httpx.AsyncClient(headers=UA, timeout=120, follow_redirects=True,
                                 limits=limits) as client:
        await asyncio.gather(*(fetch(client, sema, k, v, out, counters)
                               for k, v in todo.items()))

    with RECORDS.open("a") as f:
        for rec in out:
            f.write(json.dumps(rec) + "\n")

    el = time.perf_counter() - counters["t0"]
    print(f"\n{'='*52}")
    print(f"elapsed        : {el:.0f}s ({el/60:.1f} min)")
    print(f"new files      : {counters['new']:,}")
    print(f"content dupes  : {counters['dupe']:,}  (same bytes, different id)")
    print(f"failed         : {counters['failed']:,}")
    print(f"downloaded     : {counters['bytes']/1e9:.2f} GB")
    non_pdf = sum(1 for r in out if r.get("ok") and not r.get("is_pdf"))
    if non_pdf:
        print(f"NOT PDF magic  : {non_pdf}  <- inspect these")


asyncio.run(main())
