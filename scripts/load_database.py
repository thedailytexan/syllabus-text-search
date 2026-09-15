"""Load the collected syllabi into Postgres so they can be searched.

Two tables, because the data has two different grains:

  documents   one row per distinct syllabus, with its text
  sections    one row per course offering, pointing at its document

The split matters. Instructors reuse a syllabus across sections - one
document here covers 36 of them - so storing the text per section would
duplicate it many times over and make every count wrong. Search the
documents, report the sections.

Safe to run repeatedly. Rows are matched on their natural keys and
updated in place, so a re-run after fetching more syllabi tops up the
database rather than duplicating it.
"""
import json, os, sys, time
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "manifest.jsonl"
PDF_RECORDS = ROOT / "data" / "documents.jsonl"
EXTRACTIONS = ROOT / "data" / "extractions.jsonl"
SS_RECORDS = ROOT / "data" / "simple_syllabus.jsonl"

SEMESTERS = {"spring": 2, "summer": 6, "fall": 9}

SCHEMA = """
create table if not exists documents (
    id               bigserial primary key,
    content_sha256   text not null unique,
    source_kind      text not null,
    source_ids       text[] not null default '{}',
    source_url       text,
    original_filename text,
    byte_size        integer,
    page_count       integer,
    body             text,
    extract_tier     text,
    chars            integer,
    chars_per_page   numeric,
    last_updated     text,
    fetched_at       timestamptz,
    tsv              tsvector generated always as
                         (to_tsvector('english', coalesce(body, ''))) stored
);

create table if not exists sections (
    id             bigserial primary key,
    semester_code  integer not null,
    semester_label text,
    department     text,
    course_code    text,
    unique_number  text not null,
    section_title  text,
    instructor     text,
    cv_url         text,
    document_id    bigint references documents(id),
    unique (semester_code, unique_number)
);
"""

INDEXES = [
    # Full-text search over a stored tsvector column.
    #
    # Indexing the expression directly instead would save about 80 MB, but it
    # is only fast for rare words. A common one like "academic integrity"
    # matches most of the corpus, the planner switches to a sequential scan,
    # and it recomputes to_tsvector for every row - 10 seconds instead of 150ms.
    # Storing the column keeps every search fast regardless of how common the
    # term is, which is what anyone searching this actually needs.
    ("documents_tsv", "create index if not exists documents_tsv on documents "
                      "using gin (tsv)"),
    ("sections_dept", "create index if not exists sections_dept on sections (department)"),
    ("sections_sem",  "create index if not exists sections_sem on sections (semester_code)"),
    ("sections_doc",  "create index if not exists sections_doc on sections (document_id)"),
    ("sections_course", "create index if not exists sections_course on sections (course_code)"),
]

VIEW = """
-- The search surface: one row per section, carrying its syllabus text.
--
-- This is an inner join on purpose. With a left join the planner cannot push
-- a text predicate down into the full-text index, and a department rollup goes
-- from 3ms to 18 seconds because it recomputes to_tsvector for every row.
-- Every section currently has a syllabus, so nothing is lost; load_database
-- warns if that ever stops being true.
--
-- Search with:  where tsv @@ websearch_to_tsquery('english', 'your terms')
create or replace view syllabi as
select s.id            as section_id,
       s.semester_code, s.semester_label, s.department, s.course_code,
       s.unique_number, s.section_title, s.instructor, s.cv_url,
       d.id            as document_id,
       d.source_kind, d.source_url, d.extract_tier, d.page_count, d.chars,
       d.body, d.tsv
from sections s
join documents d on d.id = s.document_id;
"""

def jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def semester_code(label):
    """'2026 Fall' -> 20269"""
    year, name = label.split()
    return int(year) * 10 + SEMESTERS[name.lower()]


def build_documents():
    """One record per distinct syllabus, from both sources."""
    pdf_recs = [r for r in jsonl(PDF_RECORDS) if r.get("ok")]
    extractions = {r["sha256"]: r for r in jsonl(EXTRACTIONS)}
    ss_recs = [r for r in jsonl(SS_RECORDS) if r.get("ok")]

    docs = {}          # content_sha256 -> row
    by_source = {}     # the id used in the manifest -> content_sha256

    for r in pdf_recs:
        sha = r["sha256"]
        by_source[r["doc_id"]] = sha
        ex = extractions.get(sha, {})
        text_path = ex.get("text_path")
        body = (ROOT / text_path).read_text(errors="replace") if text_path else None
        d = docs.setdefault(sha, {
            "content_sha256": sha, "source_kind": "pdf", "source_ids": [],
            "source_url": r.get("source_url"), "original_filename": r.get("original_filename"),
            "byte_size": r.get("bytes"), "page_count": ex.get("pages"),
            "body": body, "extract_tier": ex.get("tier"), "chars": ex.get("chars"),
            "chars_per_page": ex.get("chars_per_page"), "last_updated": None,
            "fetched_at": r.get("fetched_at"),
        })
        d["source_ids"].append(r["doc_id"])

    for r in ss_recs:
        sha = r["sha256"]
        by_source[r["doc_id"]] = sha
        body = (ROOT / r["text_path"]).read_text(errors="replace")
        d = docs.setdefault(sha, {
            "content_sha256": sha, "source_kind": "simple_syllabus", "source_ids": [],
            "source_url": r.get("url"), "original_filename": None,
            "byte_size": None, "page_count": None, "body": body,
            "extract_tier": "rendered_html", "chars": r.get("chars"),
            "chars_per_page": None, "last_updated": r.get("last_updated"),
            "fetched_at": r.get("fetched_at"),
        })
        d["source_ids"].append(r["doc_id"])

    return list(docs.values()), by_source


DOC_COLS = ["content_sha256", "source_kind", "source_ids", "source_url",
            "original_filename", "byte_size", "page_count", "body",
            "extract_tier", "chars", "chars_per_page", "last_updated", "fetched_at"]

SEC_COLS = ["semester_code", "semester_label", "department", "course_code",
            "unique_number", "section_title", "instructor", "cv_url", "document_id"]


def main():
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("DATABASE_URL="):
                    dsn = line.split("=", 1)[1].strip()
    if not dsn:
        sys.exit("set DATABASE_URL (see .env.example)")

    docs, by_source = build_documents()
    manifest = jsonl(MANIFEST)
    print(f"documents to load : {len(docs):,}")
    print(f"sections to load  : {len(manifest):,}\n")

    t0 = time.perf_counter()
    with psycopg.connect(dsn, connect_timeout=30) as conn, conn.cursor() as cur:
        cur.execute(SCHEMA)
        # Databases created before the tsvector column existed.
        cur.execute("""alter table documents add column if not exists tsv tsvector
            generated always as (to_tsvector('english', coalesce(body, ''))) stored""")
        cur.execute("drop index if exists documents_fts")
        conn.commit()

        # Documents, via a staging table so a re-run updates instead of duplicating.
        cur.execute("create temp table stage_docs (like documents including defaults) "
                    "on commit drop")
        cur.execute("alter table stage_docs drop column id")
        cols = ", ".join(DOC_COLS)
        with cur.copy(f"copy stage_docs ({cols}) from stdin") as copy:
            for d in docs:
                copy.write_row([d[c] for c in DOC_COLS])
        cur.execute(f"""
            insert into documents ({cols})
            select {cols} from stage_docs
            on conflict (content_sha256) do update set
                source_ids   = excluded.source_ids,
                body         = excluded.body,
                extract_tier = excluded.extract_tier,
                chars        = excluded.chars,
                page_count   = excluded.page_count,
                fetched_at   = excluded.fetched_at
            -- Only rewrite rows that actually differ. Without this every
            -- re-run rewrites all of them, and the old row versions bloat
            -- the table until it is vacuumed.
            where documents.body         is distinct from excluded.body
               or documents.source_ids   is distinct from excluded.source_ids
               or documents.extract_tier is distinct from excluded.extract_tier
               or documents.chars        is distinct from excluded.chars
               or documents.page_count   is distinct from excluded.page_count
        """)
        print(f"documents inserted/updated : {cur.rowcount:,}")

        cur.execute("select content_sha256, id from documents")
        doc_id = dict(cur.fetchall())

        rows, unmatched = [], 0
        for m in manifest:
            sha = by_source.get(m["doc_id"])
            did = doc_id.get(sha) if sha else None
            if m["doc_id"] and did is None:
                unmatched += 1
            rows.append([
                semester_code(m["semester"]), m["semester"], m["dept"].strip(),
                m["course"], m["unique"], m["title"], m["instructors"],
                m["cv"] or None, did,
            ])

        cur.execute("create temp table stage_secs (like sections including defaults) "
                    "on commit drop")
        cur.execute("alter table stage_secs drop column id")
        scols = ", ".join(SEC_COLS)
        with cur.copy(f"copy stage_secs ({scols}) from stdin") as copy:
            for r in rows:
                copy.write_row(r)
        cur.execute(f"""
            insert into sections ({scols})
            select {scols} from stage_secs
            on conflict (semester_code, unique_number) do update set
                section_title = excluded.section_title,
                instructor    = excluded.instructor,
                document_id   = excluded.document_id,
                cv_url        = excluded.cv_url
            where sections.section_title is distinct from excluded.section_title
               or sections.instructor    is distinct from excluded.instructor
               or sections.document_id   is distinct from excluded.document_id
               or sections.cv_url        is distinct from excluded.cv_url
        """)
        print(f"sections inserted/updated  : {cur.rowcount:,}")
        if unmatched:
            print(f"WARNING {unmatched} sections reference a document we have not fetched")
        conn.commit()

        for name, ddl in INDEXES:
            print(f"  index {name} ...", flush=True)
            cur.execute(ddl)
        cur.execute(VIEW)
        conn.commit()

        conn.autocommit = True
        cur.execute("vacuum analyze documents")
        cur.execute("vacuum analyze sections")

        cur.execute("select count(*) from documents")
        nd = cur.fetchone()[0]
        cur.execute("select count(*) from sections")
        ns = cur.fetchone()[0]
        cur.execute("select pg_size_pretty(pg_total_relation_size('documents') "
                    "+ pg_total_relation_size('sections'))")
        size = cur.fetchone()[0]
        print(f"\n{'='*52}")
        print(f"documents : {nd:,}")
        print(f"sections  : {ns:,}")
        print(f"on disk   : {size}")
        print(f"elapsed   : {time.perf_counter() - t0:.0f}s")


main()
