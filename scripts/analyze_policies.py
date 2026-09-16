"""Report the headline policy distributions.

Prints every figure three ways - by document, by section, and by instructor -
because a percentage means a different thing under each denominator and the
story has to name which one it used. See docs/methodology.md, section 3.

Usage:
    uv run --with "psycopg[binary]" python scripts/analyze_policies.py [version]

Defaults to the v7-full production run.
"""

import os
import pathlib
import sys

import psycopg

SCALES = ("phone", "laptop", "ai")

# Labels for the 0-5 anchors, short enough to fit a terminal table.
BINS = {
    0: "not addressed",
    1: "required/permitted, no limit",
    2: "permitted with guidance",
    3: "conditional",
    4: "restricted",
    5: "prohibited",
}

# Scores 4 and 5 are the strict end; 1 and 2 the permissive end. 3 is the
# middle and is reported on its own rather than forced to one side.
STRICT = (4, 5)
LOOSE = (1, 2)


def load_env():
    env = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def pct(n, total):
    return f"{100 * n / total:5.1f}%" if total else "    - "


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "v7-full"
    load_env()

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        # One row per document, carrying its section count and a representative
        # instructor. Instructor counts use DISTINCT on the name, so an
        # instructor teaching several courses is counted once per policy value.
        rows = conn.execute(
            """
            select p.*,
                   coalesce(s.n_sections, 0) as n_sections
              from document_policies p
              left join (
                   select document_id, count(*) as n_sections
                     from sections group by document_id
              ) s on s.document_id = p.document_id
             where p.prompt_version = %s
            """,
            (version,),
        )
        cols = [d.name for d in rows.description]
        data = [dict(zip(cols, r)) for r in rows.fetchall()]

        instructors = {}
        for r in conn.execute(
            """
            select p.document_id, s.instructor
              from document_policies p
              join sections s on s.document_id = p.document_id
             where p.prompt_version = %s and s.instructor is not null
            """,
            (version,),
        ):
            instructors.setdefault(r[0], set()).add(r[1])

    if not data:
        sys.exit(f"no rows for prompt_version={version!r}")

    n_docs = len(data)
    n_sections = sum(r["n_sections"] for r in data)
    all_instructors = set()
    for names in instructors.values():
        all_instructors |= names

    print(f"\nversion {version}")
    print(f"documents {n_docs}   sections {n_sections}   instructors {len(all_instructors)}\n")

    # Documents whose completeness is not 'full' are reported but excluded from
    # the strict/lenient ratio: a stub cannot be silent on a policy it never
    # had room to state.
    stubs = [r for r in data if r.get("document_completeness") != "full"]
    if stubs:
        print(f"excluded from ratios: {len(stubs)} documents not coded as 'full'\n")

    for scale in SCALES:
        score_col, status_col, req_col = f"{scale}_score", f"{scale}_status", f"{scale}_required"
        full = [r for r in data if r.get("document_completeness") == "full"]

        print(f"=== {scale.upper()} " + "=" * 56)

        # Status first: documents whose policy could not be determined do not
        # belong inside a strict-versus-lenient ratio at all.
        unclear = [r for r in full if r.get(status_col) in ("undecided", "contradictory")]
        clear = [r for r in full if r.get(status_col) == "clear"]
        print(f"  clear {len(clear)}   undecided/contradictory {len(unclear)}"
              f"  ({pct(len(unclear), len(full))} of coded)")

        print(f"\n  {'bin':32} {'docs':>7} {'':>7} {'sections':>9} {'':>7} {'instr':>7}")
        for score in range(6):
            hit = [r for r in clear if r[score_col] == score]
            d = len(hit)
            s = sum(r["n_sections"] for r in hit)
            names = set()
            for r in hit:
                names |= instructors.get(r["document_id"], set())
            print(f"  {score} {BINS[score]:30} {d:7} {pct(d, len(clear))} "
                  f"{s:9} {pct(s, n_sections)} {len(names):7}")

        # The headline ratio, on the documents that state a policy at all.
        addressed = [r for r in clear if r[score_col] > 0]
        strict = [r for r in addressed if r[score_col] in STRICT]
        loose = [r for r in addressed if r[score_col] in LOOSE]
        middle = [r for r in addressed if r[score_col] == 3]

        a_s = sum(r["n_sections"] for r in addressed)
        print(f"\n  addresses {scale:7} {len(addressed):6} docs {pct(len(addressed), len(clear))}"
              f"   {a_s:6} sections {pct(a_s, n_sections)}")
        if addressed:
            print(f"    of those: strict (4-5) {len(strict):5} {pct(len(strict), len(addressed))}"
                  f"   conditional (3) {len(middle):5} {pct(len(middle), len(addressed))}"
                  f"   permissive (1-2) {len(loose):5} {pct(len(loose), len(addressed))}")

        required = [r for r in full if r.get(req_col)]
        r_s = sum(r["n_sections"] for r in required)
        note = "  [inflated by generic device wording - see known-issues.md #5]" if scale != "ai" else ""
        print(f"  requires  {scale:7} {len(required):6} docs {pct(len(required), len(full))}"
              f"   {r_s:6} sections {pct(r_s, n_sections)}{note}")
        print()


if __name__ == "__main__":
    main()
