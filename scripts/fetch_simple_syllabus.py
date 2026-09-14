"""Render the Simple Syllabus documents that UT links with a "View" button.

These are not files - each is an Angular single-page app that builds the
syllabus in the browser, so there is nothing to extract until it has run.
Two things make it work:

  * A real browser User-Agent. With Playwright's default headless UA the app
    errors out and renders an empty body.
  * A content-based wait. "networkidle" never settles on this app; poll the
    body text instead.

Saves rendered HTML alongside extracted text so the structured sections can be
re-parsed later without scraping again. Resumable - a re-run skips finished ids.
"""
import asyncio, hashlib, json, re, time
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
HTML_DIR = ROOT / "data" / "simple_syllabus"
MANIFEST = ROOT / "data" / "manifest.jsonl"
RECORDS = ROOT / "data" / "simple_syllabus.jsonl"

DOC_URL = "https://utexas.simplesyllabus.com/doc/{}"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
CONCURRENCY = 4
RETRIES = 3
MIN_CHARS = 500          # below this the app has not finished rendering
POLL_STEPS, POLL_WAIT = 80, 0.25
BLOCK = {"image", "font", "media"}


def load_targets():
    ids = {}
    for line in MANIFEST.read_text().splitlines():
        r = json.loads(line)
        if r["kind"] == "view_simplesyllabus":
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


async def block_assets(route):
    if route.request.resource_type in BLOCK:
        await route.abort()
    else:
        await route.continue_()


async def render(ctx, sema, doc_id, course, out, counters):
    async with sema:
        for attempt in range(RETRIES):
            page = await ctx.new_page()
            try:
                await page.route("**/*", block_assets)
                await page.goto(DOC_URL.format(doc_id),
                                wait_until="domcontentloaded", timeout=45000)
                text = ""
                for _ in range(POLL_STEPS):
                    text = await page.inner_text("body")
                    if len(text) >= MIN_CHARS:
                        break
                    await asyncio.sleep(POLL_WAIT)

                if len(text) < MIN_CHARS:
                    raise RuntimeError(f"only {len(text)} chars rendered")

                html = await page.content()
                title = await page.title()
                m = re.search(r"Last updated:\s*([0-9/]+\s*-\s*[0-9:]+\s*[AP]M)", text)

                (HTML_DIR / f"{doc_id}.html").write_text(html)
                (HTML_DIR / f"{doc_id}.txt").write_text(text)

                out.append({
                    "doc_id": doc_id, "ok": True,
                    "url": DOC_URL.format(doc_id),
                    "title": title,
                    "last_updated": m.group(1) if m else None,
                    "chars": len(text),
                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "html_path": f"data/simple_syllabus/{doc_id}.html",
                    "text_path": f"data/simple_syllabus/{doc_id}.txt",
                    "sample_course": course,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                })
                counters["ok"] += 1
                counters["chars"] += len(text)
                break

            except Exception as e:
                if attempt == RETRIES - 1:
                    out.append({"doc_id": doc_id, "ok": False, "error": str(e)[:200]})
                    counters["failed"] += 1
                else:
                    await asyncio.sleep(2 * (attempt + 1))
            finally:
                await page.close()

        n = counters["ok"] + counters["failed"]
        if n % 50 == 0:
            el = time.perf_counter() - counters["t0"]
            print(f"  {n:>4}/{counters['total']}  {el:6.0f}s  {n/el:4.2f}/s  "
                  f"ok={counters['ok']} failed={counters['failed']}", flush=True)


async def main():
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    targets = load_targets()
    done = already_done()
    todo = {k: v for k, v in targets.items() if k not in done}

    print(f"Simple Syllabus docs : {len(targets):,}")
    print(f"already rendered     : {len(done):,}")
    print(f"to render now        : {len(todo):,}\n")
    if not todo:
        print("nothing to do.")
        return

    out = []
    counters = {"ok": 0, "failed": 0, "chars": 0,
                "total": len(todo), "t0": time.perf_counter()}
    sema = asyncio.Semaphore(CONCURRENCY)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(user_agent=UA, locale="en-US",
                                        viewport={"width": 1280, "height": 900})
        try:
            await asyncio.gather(*(render(ctx, sema, k, v, out, counters)
                                   for k, v in todo.items()))
        finally:
            await browser.close()

    with RECORDS.open("a") as f:
        for rec in out:
            f.write(json.dumps(rec) + "\n")

    el = time.perf_counter() - counters["t0"]
    print(f"\n{'='*52}")
    print(f"elapsed   : {el:.0f}s ({el/60:.1f} min)")
    print(f"rendered  : {counters['ok']:,}")
    print(f"failed    : {counters['failed']:,}")
    if counters["ok"]:
        print(f"avg chars : {counters['chars']//counters['ok']:,}")


asyncio.run(main())
