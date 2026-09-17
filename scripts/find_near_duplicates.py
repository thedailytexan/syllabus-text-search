"""Group syllabi that are the same document with the details changed.

Content hashing already collapses byte-identical files. It does not catch the
common case: one syllabus posted for many sections, differing in a section
number, a room, a date, or a sentence or two. Those survive as separate
documents and over-weight departments that template heavily - which matters for
a department-level breakout and much less for a corpus-level figure.

An earlier version of this script hashed the text with digits and punctuation
stripped and treated identical hashes as duplicates. That was too brittle: a
cluster of eleven cello-studio syllabi that are 99.9% identical produced eight
different hashes, because one changed word changes the hash. It found 77
clusters where the method below finds far more.

Method: reduce each document to a sketch of its character shingles (a MinHash),
block candidates by length so the comparison stays cheap, then join documents
whose estimated Jaccard similarity clears THRESHOLD into clusters.

Usage:
    uv run --with "psycopg[binary]" python scripts/find_near_duplicates.py [--write]
"""

import collections
import hashlib
import os
import pathlib
import re
import sys

import psycopg

# Words reduced to letters only, so section numbers, unique numbers, room
# numbers and dates - the things that legitimately differ between sections of
# one course - drop out.
LETTERS = re.compile(r"[^a-z]+")
SHINGLE = 5        # words per shingle
SKETCH = 256       # hashes kept per document
THRESHOLD = 0.70   # estimated Jaccard above which two syllabi are one template
MIN_WORDS = 120
LENGTH_TOLERANCE = 0.40  # only compare documents within 40% of each other


def load_env():
    env = pathlib.Path(__file__).resolve().parent.parent / ".env"
    for line in env.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def sketch(text):
    """The SKETCH smallest word-shingle hashes - a MinHash of the document.

    Shingles are WORD n-grams, not character n-grams. An earlier version hashed
    character runs from text with whitespace stripped out, sampling every third
    character. That is fragile in exactly the way this job cannot afford:
    inserting one word near the top shifts every later shingle boundary, so two
    syllabi differing only in their title shared almost no shingles and scored a
    Jaccard of 0.04 when they are in truth 98.5% identical. Word shingles are
    invariant to that shift.
    """
    words = [w for w in LETTERS.sub(" ", (text or "").lower()).split() if w]
    if len(words) < MIN_WORDS:
        return None, 0
    hashes = {
        int.from_bytes(hashlib.blake2b(
            " ".join(words[i:i + SHINGLE]).encode(), digest_size=8).digest(), "big")
        for i in range(len(words) - SHINGLE + 1)
    }
    return frozenset(sorted(hashes)[:SKETCH]), len(words)


def similarity(a, b):
    """Jaccard estimate for two bottom-k sketches.

    Intersecting the two sketches directly and dividing by their union
    underestimates badly: each sketch only holds the SKETCH smallest hashes of
    its own document, so shared shingles that fall outside one sketch's window
    are invisible. The unbiased form takes the SKETCH smallest hashes of the
    two sketches combined, and asks how many of those appear in both.
    """
    if not a or not b:
        return 0.0
    window = sorted(a | b)[:SKETCH]
    if not window:
        return 0.0
    return sum(1 for h in window if h in a and h in b) / len(window)


class Union:
    """Union-find, so A~B and B~C put all three in one cluster."""

    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def main():
    write = "--write" in sys.argv
    load_env()
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        rows = conn.execute(
            "select id, body from documents where body is not null").fetchall()

        sketches, lengths = {}, {}
        for doc_id, body in rows:
            s, n = sketch(body)
            if s:
                sketches[doc_id] = s
                lengths[doc_id] = n

        # Block by length so we compare only plausible pairs.
        order = sorted(sketches, key=lambda d: lengths[d])
        uf = Union()
        comparisons = 0
        for i, a in enumerate(order):
            for b in order[i + 1:]:
                if lengths[b] > lengths[a] * (1 + LENGTH_TOLERANCE):
                    break
                comparisons += 1
                if similarity(sketches[a], sketches[b]) >= THRESHOLD:
                    uf.union(a, b)

        clusters = collections.defaultdict(list)
        for doc_id in sketches:
            clusters[uf.find(doc_id)].append(doc_id)
        clusters = {k: sorted(v) for k, v in clusters.items() if len(v) > 1}

        inside = sum(len(v) for v in clusters.values())
        redundant = inside - len(clusters)
        print(f"\ndocuments examined:        {len(rows)}   (pairs compared: {comparisons:,})")
        print(f"near-duplicate clusters:   {len(clusters)}")
        print(f"documents inside clusters: {inside}")
        print(f"redundant copies:          {redundant} "
              f"({100*redundant/len(rows):.1f}% of the corpus)")
        print(f"distinct syllabi after collapsing: {len(rows) - redundant}\n")

        biggest = sorted(clusters.values(), key=len, reverse=True)[:10]
        print("  largest clusters:")
        for ids in biggest:
            dept = conn.execute(
                """select department, count(*) from sections
                    where document_id = any(%s) group by 1 order by 2 desc limit 1""",
                (ids,)).fetchone()
            label = dept[0].strip() if dept else "?"
            print(f"    {len(ids):3} copies  [{label:5}]  docs {ids[:6]}"
                  f"{' ...' if len(ids) > 6 else ''}")

        drop = [d for ids in clusters.values() for d in ids[1:]]
        print()
        for scale in ("phone", "laptop", "ai"):
            full = conn.execute(
                f"""select count(*) filter (where {scale}_score >= 4),
                           count(*) filter (where {scale}_score > 0)
                      from document_policies
                     where prompt_version='v7-full' and {scale}_status='clear'""").fetchone()
            ded = conn.execute(
                f"""select count(*) filter (where {scale}_score >= 4),
                           count(*) filter (where {scale}_score > 0)
                      from document_policies
                     where prompt_version='v7-full' and {scale}_status='clear'
                       and not (document_id = any(%s))""", (drop,)).fetchone()
            a = 100 * full[0] / full[1] if full[1] else 0
            b = 100 * ded[0] / ded[1] if ded[1] else 0
            print(f"  {scale:7} strict share  as-is {a:5.1f}%   deduplicated {b:5.1f}%"
                  f"   ({b-a:+.1f} pts)")

        if write:
            conn.execute("""alter table documents
                            add column if not exists near_duplicate_group text""")
            for root, ids in clusters.items():
                conn.execute(
                    "update documents set near_duplicate_group=%s where id = any(%s)",
                    (f"nd{root}", ids))
            conn.commit()
            print(f"\n  wrote near_duplicate_group for {inside} documents")


if __name__ == "__main__":
    main()
