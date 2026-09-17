"""Inter-coder agreement between the production pass and an independent re-code.

The second coder never sees the first coder's output; it works from the same
documents and the same written instructions. Comparing them measures how much of
a score comes from the codebook and how much from whoever applied it - the
number a content-analysis reviewer will ask for first.

Reports, per scale:
  - exact agreement, and agreement within one bin
  - Krippendorff's alpha with the ordinal difference function

Alpha rather than percent agreement, because percent agreement is inflated by a
skewed distribution: 59% of syllabi say nothing about phones, so two coders who
both guessed "0" every time would look like they agreed. Alpha corrects for the
agreement expected by chance given the observed distribution.

Conventional reading: alpha >= 0.800 is reliable, 0.667-0.800 supports tentative
conclusions, below that is not usable.

Both passes live in the database, so the figure is reproducible from Neon alone
and does not depend on a working directory surviving. Directories of raw coder
JSON are still accepted, for checking a pass before it is loaded.

Usage:
    uv run --with "psycopg[binary]" python scripts/coder_agreement.py [first] [second]

    Defaults to the two stored versions:  v7-full  v7-double
    An argument that is an existing directory is read as coder JSON instead.
"""

import collections
import json
import os
import pathlib
import sys

SCALES = ("phone", "laptop", "ai")


SCORE_FIELDS = [f"{s}_{f}" for s in SCALES
                for f in ("score", "required", "status")]


def load_env():
    env = pathlib.Path(__file__).resolve().parent.parent / ".env"
    for line in env.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load(source):
    """Map document_id -> record, from a directory of coder JSON or from a
    stored prompt_version in the database."""
    path = pathlib.Path(source)
    if path.is_dir():
        out = {}
        for f in sorted(path.glob("batch_*.json")):
            for rec in json.loads(f.read_text()):
                out[rec["document_id"]] = rec
        return out

    import psycopg

    load_env()
    columns = ", ".join(SCORE_FIELDS)
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        rows = conn.execute(
            f"select document_id, {columns} from document_policies"
            " where prompt_version = %s",
            (source,),
        ).fetchall()
    if not rows:
        sys.exit(f"no rows stored for prompt_version {source!r}")
    return {r[0]: dict(zip(SCORE_FIELDS, r[1:])) for r in rows}


def alpha_ordinal(pairs):
    """Krippendorff's alpha for two coders, ordinal difference function.

    `pairs` is a list of (value_a, value_b). Both coders rate every unit, so
    each unit contributes one coincidence in each direction.
    """
    values = sorted({v for pair in pairs for v in pair})
    if len(values) < 2:
        return 1.0  # No variation to disagree about.

    # Coincidence matrix: o[c][k] counts coder-pair observations.
    o = collections.defaultdict(float)
    for a, b in pairs:
        o[(a, b)] += 1.0
        o[(b, a)] += 1.0

    n_v = collections.Counter()
    for a, b in pairs:
        n_v[a] += 1
        n_v[b] += 1
    n = sum(n_v.values())

    def delta2(c, k):
        """Ordinal distance: squared gap weighted by how populated the
        intervening bins are, so a 0->1 step counts differently from 4->5."""
        lo, hi = sorted((values.index(c), values.index(k)))
        run = sum(n_v[values[g]] for g in range(lo, hi + 1))
        return (run - (n_v[c] + n_v[k]) / 2.0) ** 2

    d_obs = sum(o[(c, k)] * delta2(c, k) for c in values for k in values) / n
    d_exp = sum(
        n_v[c] * n_v[k] * delta2(c, k) for c in values for k in values
    ) / (n * (n - 1))
    return 1.0 - d_obs / d_exp if d_exp else 1.0


def main():
    args = sys.argv[1:] or ["v7-full", "v7-double"]
    if len(args) != 2:
        sys.exit(__doc__)
    print(f"\ncomparing {args[0]}  vs  {args[1]}")
    first, second = load(args[0]), load(args[1])
    shared = sorted(set(first) & set(second))
    if not shared:
        sys.exit("no documents coded by both passes yet")

    print(f"\ndouble-coded documents: {len(shared)}\n")
    print(f"  {'scale':8} {'exact':>8} {'within 1':>10} {'alpha':>8}   {'disagreements':>13}")

    for scale in SCALES:
        key = f"{scale}_score"
        pairs = [(first[d][key], second[d][key]) for d in shared]
        exact = sum(1 for a, b in pairs if a == b)
        within = sum(1 for a, b in pairs if abs(a - b) <= 1)
        a = alpha_ordinal(pairs)
        print(f"  {scale:8} {100*exact/len(pairs):7.1f}% {100*within/len(pairs):9.1f}%"
              f" {a:8.3f}   {len(pairs)-exact:13}")

    # The booleans and the status field are nominal, so report plain agreement.
    print()
    for field in ("phone_required", "laptop_required", "ai_required",
                  "phone_status", "laptop_status", "ai_status"):
        same = sum(1 for d in shared if first[d].get(field) == second[d].get(field))
        print(f"  {field:18} {100*same/len(shared):6.1f}% agreement")

    # Where the two passes diverge by more than one bin, the cause is usually a
    # rule gap rather than a slip - worth listing for the codebook review.
    print("\n  documents differing by 2+ bins on any scale:")
    wide = []
    for d in shared:
        for scale in SCALES:
            k = f"{scale}_score"
            if abs(first[d][k] - second[d][k]) >= 2:
                wide.append((d, scale, first[d][k], second[d][k]))
    for d, scale, a, b in wide[:25]:
        print(f"    doc {d:5} {scale:7} first={a} second={b}")
    print(f"    ({len(wide)} total)" if wide else "    none")


if __name__ == "__main__":
    main()
