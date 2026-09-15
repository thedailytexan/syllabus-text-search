"""Pull plain text out of the downloaded syllabus PDFs.

Almost every syllabus UT publishes is a Word or InDesign export with real
text already inside it, so we read that directly. Only a small tail are
genuine scans, and those get character recognition. Running OCR over
everything would be far slower and give worse results on the 98% that
don't need it, so it is a fallback, not the default.

Each PDF ends up in one of three buckets:

    text_layer  read straight out of the file
    ocr         no usable text, so we recognised the characters
    encrypted   password-protected by whoever uploaded it, cannot be opened
    failed      neither worked - listed at the end for a human to look at

The Simple Syllabus documents are already plain text on disk and skip
this step entirely.
"""
import json, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF_RECORDS = ROOT / "data" / "documents.jsonl"
TEXT_DIR = ROOT / "data" / "text"
OUT = ROOT / "data" / "extractions.jsonl"

MIN_CHARS_PER_PAGE = 200      # below this we treat the text layer as unusable
WORKERS = 8
OCR_TIMEOUT = 600


def run(cmd, timeout):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def page_count(pdf):
    try:
        out = run(["pdfinfo", str(pdf)], 60).stdout
        for line in out.splitlines():
            if line.startswith("Pages:"):
                return int(line.split()[1])
    except Exception:
        pass
    return 0


def read_text_layer(pdf):
    """-layout keeps columns and date tables readable instead of interleaving them."""
    r = run(["pdftotext", "-layout", str(pdf), "-"], 120)
    return r.stdout if r.returncode == 0 else ""


class Encrypted(Exception):
    """Locked with a password we do not have, so there is nothing to read."""


def ocr(pdf):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        side, out = tmp / "text.txt", tmp / "out.pdf"
        source = pdf

        # Some uploads carry permissions encryption that blocks OCR but opens
        # fine with an empty password. Strip it. A file that needs a real
        # password fails here and cannot be read at all.
        probe = run(["qpdf", "--decrypt", "--password=", str(pdf), str(tmp / "dec.pdf")], 120)
        if (tmp / "dec.pdf").exists():
            source = tmp / "dec.pdf"
        elif "invalid password" in (probe.stderr or "").lower():
            raise Encrypted("password protected by the uploader")

        r = run(["ocrmypdf", "--force-ocr", "--quiet", "--sidecar", str(side),
                 str(source), str(out)], OCR_TIMEOUT)
        if side.exists():
            return side.read_text(errors="replace")
        raise RuntimeError((r.stderr or "ocr produced no text")[:200])


def extract(rec, counters):
    sha, pdf = rec["sha256"], ROOT / rec["path"]
    result = {"sha256": sha, "pages": page_count(pdf)}
    try:
        text = read_text_layer(pdf)
        pages = result["pages"] or 1
        if len(text.strip()) / pages >= MIN_CHARS_PER_PAGE:
            result["tier"] = "text_layer"
        else:
            text = ocr(pdf)
            result["tier"] = "ocr"
        result["chars"] = len(text.strip())
        result["chars_per_page"] = round(result["chars"] / pages, 1)
        (TEXT_DIR / f"{sha}.txt").write_text(text, errors="replace")
        result["text_path"] = f"data/text/{sha}.txt"
        result["ok"] = True
    except Encrypted as e:
        result.update(ok=False, tier="encrypted", chars=0, error=str(e))
    except Exception as e:
        result.update(ok=False, tier="failed", chars=0, error=f"{type(e).__name__}: {e}"[:200])

    counters[result["tier"]] += 1
    n = sum(counters.values())
    if n % 250 == 0:
        el = time.perf_counter() - counters["_t0"]
        print(f"  {n:>5}/{counters['_total']}  {el:5.0f}s  "
              f"text={counters['text_layer']} ocr={counters['ocr']} "
              f"encrypted={counters['encrypted']} failed={counters['failed']}", flush=True)
    return result


def main():
    for tool in ("pdftotext", "pdfinfo", "ocrmypdf"):
        if not subprocess.run(["which", tool], capture_output=True).stdout:
            sys.exit(f"missing {tool} - run: brew install poppler ocrmypdf tesseract")

    TEXT_DIR.mkdir(parents=True, exist_ok=True)

    seen, docs = set(), []
    for line in PDF_RECORDS.read_text().splitlines():
        r = json.loads(line)
        if r.get("ok") and r["sha256"] not in seen:
            seen.add(r["sha256"])
            docs.append(r)

    done = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("ok"):
                done.add(rec["sha256"])

    todo = [d for d in docs if d["sha256"] not in done]
    print(f"unique PDFs   : {len(docs):,}")
    print(f"already done  : {len(done):,}")
    print(f"to extract    : {len(todo):,}\n")
    if not todo:
        print("nothing to do.")
        return

    counters = {"text_layer": 0, "ocr": 0, "encrypted": 0, "failed": 0,
                "_total": len(todo), "_t0": time.perf_counter()}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(lambda d: extract(d, counters), todo))

    with OUT.open("a") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    el = time.perf_counter() - counters["_t0"]
    ok = [r for r in results if r["ok"]]
    print(f"\n{'='*52}")
    print(f"elapsed     : {el:.0f}s ({el/60:.1f} min)")
    print(f"text layer  : {counters['text_layer']:,}")
    print(f"OCR applied : {counters['ocr']:,}")
    print(f"encrypted   : {counters['encrypted']:,}  (locked by the uploader)")
    print(f"failed      : {counters['failed']:,}")
    if ok:
        print(f"total text  : {sum(r['chars'] for r in ok)/1e6:.1f} M chars")
    for r in results:
        if r["tier"] == "failed":
            print(f"  FAILED {r['sha256'][:12]}  {r.get('error','')}")


main()
