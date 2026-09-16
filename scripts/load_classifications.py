"""Load policy classifications into the database.

Takes the JSON files produced by the classification pass and writes them into
document_policies, one verdict per document per prompt version. Validates
before writing: scores must be 0-5, labels must match the scale, and any
non-zero score needs a verbatim evidence quote that actually appears in the
document. Anything that fails is reported and skipped rather than loaded.

Usage:
    python scripts/load_classifications.py <dir-of-json-files> <prompt-version>
"""
import difflib, json, re, sys, unicodedata
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent

# Phones and laptops share anchors; AI differs at 3.
DEVICE_LABELS = {0: "not addressed", 1: "required", 2: "permitted",
                 3: "discouraged", 4: "restricted", 5: "prohibited"}
AI_LABELS = {0: "not addressed", 1: "required", 2: "permitted",
             3: "conditional", 4: "restricted", 5: "prohibited"}
SCALES = {"phone": DEVICE_LABELS, "laptop": DEVICE_LABELS, "ai": AI_LABELS}
CONFIDENCE = {"high", "medium", "low"}
COMPLETENESS = {"full", "stub"}

FIELDS = (["document_id", "document_completeness", "coder_notes"]
          + [f"{s}_{f}" for s in SCALES
             for f in ("score", "label", "evidence", "confidence")]
          + ["evidence_notes"])


def dsn():
    env = ROOT / ".env"
    for line in env.read_text().splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip()
    sys.exit("no DATABASE_URL in .env")


ZERO_WIDTH = re.compile(r"[\u200b-\u200f\u00ad\ufeff]")
SMART = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                       "\u2013": "-", "\u2014": "-", "\u2212": "-"})


def normalize(s):
    """Fold away PDF extraction noise without hiding a fabricated quote.

    Extracted text carries zero-width characters, smart quotes, soft hyphens and
    words broken across lines. A quote that differs only by those is the same
    quote. A quote that differs by actual words is not.
    """
    s = unicodedata.normalize("NFKC", s or "")
    s = ZERO_WIDTH.sub("", s).translate(SMART)
    # A line can break at a real hyphen ("in-\nclass"), so removing the hyphen
    # and keeping it are both plausible readings. Drop hyphens on both sides of
    # the comparison instead of guessing which one it was.
    s = re.sub(r"-\s*\n\s*", "", s)
    s = s.replace("-", "")
    return " ".join(s.split()).lower()


def as_quotes(ev):
    """Evidence may be one quote or several.

    A contradictory policy needs both sentences cited, and two non-adjacent
    sentences joined into one string is not a substring of anything. So a list
    is allowed, and each element is verified on its own.
    """
    if ev is None:
        return []
    if isinstance(ev, str):
        return [ev] if ev.strip() else []
    return [q for q in ev if isinstance(q, str) and q.strip()]


def find_evidence(quote, body):
    """Return 'exact', 'normalized', or None."""
    q, b = normalize(quote), normalize(body)
    if not q:
        return None
    if q in b:
        return "exact"
    # Slide a window the length of the quote and take the best similarity.
    # 0.92 tolerates broken ligatures and stray characters; it does not
    # tolerate a sentence the document never contained.
    best, step = 0.0, max(1, len(q) // 4)
    for i in range(0, max(1, len(b) - len(q) + 1), step):
        r = difflib.SequenceMatcher(None, q, b[i:i + len(q)]).ratio()
        if r > best:
            best = r
        if best >= 0.92:
            return "normalized"
    return None


def validate(rec, bodies, problems):
    did = rec.get("document_id")
    if did not in bodies:
        problems.append(f"{did}: not a document we asked for"); return False
    comp = (rec.get("document_completeness") or "").strip().lower()
    if comp not in COMPLETENESS:
        problems.append(f"{did}: document_completeness {comp!r} not full/stub"); return False
    rec["document_completeness"] = comp
    for scale, labels in SCALES.items():
        score = rec.get(f"{scale}_score")
        if score not in labels:
            problems.append(f"{did}: {scale}_score {score!r} not 0-5"); return False
        label = (rec.get(f"{scale}_label") or "").strip().lower()
        if label != labels[score]:
            problems.append(f"{did}: {scale}_label {label!r} does not match "
                            f"score {score} ({labels[score]!r})"); return False
        conf = (rec.get(f"{scale}_confidence") or "").strip().lower()
        if conf not in CONFIDENCE:
            problems.append(f"{did}: {scale}_confidence {conf!r} invalid"); return False
        quotes = as_quotes(rec.get(f"{scale}_evidence"))
        if score == 0:
            if quotes:
                problems.append(f"{did}: {scale} scored 0 but has evidence"); return False
            rec[f"{scale}_evidence"] = None
        else:
            if not quotes:
                problems.append(f"{did}: {scale} scored {score} with no evidence"); return False
            # every quote has to really be in the document - this is what stops
            # a plausible-sounding but invented citation reaching print
            for q in quotes:
                how = find_evidence(q, bodies[did])
                if how is None:
                    problems.append(f"{did}: {scale} evidence not found in document "
                                    f"-> {q[:60]!r}")
                    return False
                if how == "normalized":
                    rec.setdefault("_notes", []).append(
                        f"{scale}: matched after normalizing extraction noise")
            rec[f"{scale}_evidence"] = "\n\n".join(quotes)
    return True


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    indir, version = Path(sys.argv[1]), sys.argv[2]

    records = []
    for f in sorted(indir.glob("*.json")):
        data = json.loads(f.read_text())
        records.extend(data if isinstance(data, list) else [data])
    print(f"read {len(records)} records from {len(list(indir.glob('*.json')))} files")

    conn = psycopg.connect(dsn(), connect_timeout=30)
    with conn, conn.cursor() as cur:
        ids = tuple({r.get("document_id") for r in records if r.get("document_id")})
        cur.execute("select id, body from documents where id = any(%s)", (list(ids),))
        bodies = dict(cur.fetchall())

        problems, good = [], []
        seen = set()
        for r in records:
            if r.get("document_id") in seen:
                problems.append(f"{r.get('document_id')}: duplicate record"); continue
            if validate(r, bodies, problems):
                seen.add(r["document_id"]); good.append(r)

        softened = [r for r in good if r.get("_notes")]
        print(f"valid: {len(good)}   rejected: {len(problems)}")
        for r in softened:
            print(f"  NOTE   {r['document_id']}: {'; '.join(r['_notes'])}")
        for p in problems[:20]:
            print(f"  REJECT {p}")
        if len(problems) > 20:
            print(f"  ... and {len(problems)-20} more")

        if good:
            updatable = [f for f in FIELDS if f != "document_id"]
            placeholders = ",".join(["%s"] * (len(FIELDS) + 2))
            cur.executemany(f"""
                insert into document_policies
                  ({', '.join(FIELDS)}, prompt_version, model)
                values ({placeholders})
                on conflict (document_id, prompt_version) do update set
                  {', '.join(f'{f}=excluded.{f}' for f in updatable)}
            """, [[r.get(f) if f != "evidence_notes"
                   else ("; ".join(r["_notes"]) if r.get("_notes") else None)
                   for f in FIELDS] + [version, "subagent"] for r in good])
            print(f"\nloaded {len(good)} into document_policies (version {version})")


main()
