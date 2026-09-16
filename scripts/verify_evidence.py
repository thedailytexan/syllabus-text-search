"""Re-verify every stored evidence quote against the stored syllabus text.

This is the audit behind the central claim of the project: no score above zero
sits in the database without a quote that really appears in the syllabus. The
loader enforces it at write time; this script proves it after the fact, over
every row, without trusting the loader.

It exists as a script rather than an ad-hoc query because getting it right is
fiddlier than it looks, and an ad-hoc version got it wrong twice:

  - `document_policies.<scale>_evidence` stores an ARRAY of quotes joined with a
    blank line. Each quote was verified separately at load time. Matching the
    joined string as if it were one quote fails on every multi-quote row and
    looks alarmingly like fabricated evidence. Split on the blank line first.
  - Normalization has to match the loader's: NFKC (which folds the non-breaking
    spaces UT boilerplate is full of), smart quotes and dashes flattened, and
    line-break hyphenation joined.

Usage:
    uv run --with "psycopg[binary]" python scripts/verify_evidence.py [version]
"""

import importlib.util
import os
import pathlib
import sys

import psycopg

SCALES = ("phone", "laptop", "ai")
SEPARATOR = "\n\n"


def loader_matcher():
    """Borrow the loader's own matcher so the audit cannot drift from it."""
    path = pathlib.Path(__file__).resolve().parent / "load_classifications.py"
    spec = importlib.util.spec_from_file_location("_loader", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["_loader"] = module
    spec.loader.exec_module(module)
    return module.find_evidence


def load_env():
    env = pathlib.Path(__file__).resolve().parent.parent / ".env"
    for line in env.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "v7-full"
    load_env()
    find_evidence = loader_matcher()

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        rows = conn.execute(
            """select p.document_id, d.body,
                      p.phone_score,  p.phone_evidence,
                      p.laptop_score, p.laptop_evidence,
                      p.ai_score,     p.ai_evidence
                 from document_policies p
                 join documents d on d.id = p.document_id
                where p.prompt_version = %s and d.body is not null
                order by p.document_id""",
            (version,),
        ).fetchall()

    checked = exact = normalized = 0
    failures = []
    for row in rows:
        doc_id, body = row[0], row[1]
        for i, scale in enumerate(SCALES):
            score, evidence = row[2 + i * 2], row[3 + i * 2]
            if not score or not evidence:
                continue
            for quote in (q for q in evidence.split(SEPARATOR) if q.strip()):
                checked += 1
                how = find_evidence(quote, body)
                if how == "exact":
                    exact += 1
                elif how == "normalized":
                    normalized += 1
                else:
                    failures.append((doc_id, scale, score, quote))

    print(f"\nversion {version}")
    print(f"  rows audited:            {len(rows)}")
    print(f"  quotes checked:          {checked}")
    print(f"  matched exactly:         {exact}  ({100*exact/checked:.2f}%)")
    print(f"  matched after cleanup:   {normalized}  ({100*normalized/checked:.2f}%)")
    print(f"  NOT FOUND:               {len(failures)}")

    for doc_id, scale, score, quote in failures[:25]:
        print(f"    doc {doc_id} {scale} score={score}: {quote[:70]!r}")
    if len(failures) > 25:
        print(f"    ... and {len(failures)-25} more")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
