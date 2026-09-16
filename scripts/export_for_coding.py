"""Write the documents to be classified out as text files, one per document.

Always regenerate before a classification run. The database is the source of
truth: re-extracting a syllabus updates it there, and a stale file on disk
means coders score text the corpus no longer contains. That happened once -
a document was re-OCRed, the database updated, the file left behind, and the
coder scored a page of mojibake that no longer existed.

Usage:  python scripts/export_for_coding.py <out-dir> [dev|gold|all]
"""
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent


def dsn():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip()
    sys.exit("no DATABASE_URL in .env")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    split = sys.argv[2] if len(sys.argv) > 2 else "dev"

    with psycopg.connect(dsn(), connect_timeout=30) as conn, conn.cursor() as cur:
        if split == "all":
            cur.execute("""select id, body from documents
                           where body is not null order by id""")
        else:
            cur.execute("""select p.document_id, d.body
                           from policy_sample p join documents d on d.id = p.document_id
                           where p.split = %s and d.body is not null
                           order by p.document_id""", (split,))
        rows = cur.fetchall()

    written = stale = 0
    for did, body in rows:
        f = out / f"{did}.txt"
        if f.exists() and f.read_text() != body:
            stale += 1
        f.write_text(body)
        written += 1
    print(f"wrote {written} documents to {out}")
    if stale:
        print(f"  {stale} were STALE and have been refreshed")


main()
