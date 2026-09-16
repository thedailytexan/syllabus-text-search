# Open issues in the classification run

Things known to be wrong, unresolved, or needing a cleanup pass before any
number is published. Kept separate from `docs/methodology.md` so it can be
worked through as a checklist and closed out.

Sizes are measured against the loaded database, not estimated.

---

## 1. R10 does not settle precedence when a syllabus both defers and specifies

**Corrected 2026-09-16.** An earlier version of this entry claimed the AI
strictness figure was unpublishable and swung between 40% and 66%. That was
wrong, and the error is recorded here rather than deleted, because it is the
same class of mistake this project exists to catch.

**The original claim and why it was wrong.** R10 sorts the UT "generative AI is
permitted on a partial basis" template by asking whether the instructor named
which tasks may use AI (score 3) or deferred permission to later written
instruction (score 4). A query suggested the deferral sentence appeared in only
18 documents, implying coders were guessing on the other ~975. The query looked
for "informed in writing"; the template actually reads "you will be informed **by
your instructor** in writing". The phrase is in **611** documents. The
conclusion drawn from the bad query was off by a factor of thirty.

**What is actually true.** R10 discriminates:

| | scored 3 | scored 4 |
|---|---|---|
| template + deferral language | 168 | 322 |
| template, no deferral language | 249 | 58 |

The near-even 48/46 aggregate split across all template documents is not coder
disagreement on identical text. It is the corpus genuinely containing both kinds
of syllabus. Reading six documents from each group confirms it: the 3s carry
instructor-written task splits ("you may use AI to study, check your own work";
"you are not permitted to use AI to directly generate responses to homework"),
and the 4s carry per-assignment deferrals ("only when specifically stated on the
assignment", "read the instructions in each assignment").

**The real defect, which is narrower.** Where a syllabus carries *both* a
deferral sentence and an instructor-written task split, R10 states no precedence.
Several coders reported this independently and resolved it the same way — the
specific split governs — which is defensible but is their judgment, not the
codebook's instruction. That accounts for most of the 168 documents that defer
yet scored 3.

**Size and effect.** 226 documents (7.5% of those stating an AI policy) carry a
score that disagrees with the textual signal. Flipping all of them bounds the
figure:

| | strict (4-5) |
|---|---|
| all contested read as conditional | 50.2% |
| as coded | **52.2%** |
| all contested read as restricted | 57.8% |

**Roughly half of stated AI policies are restrictive, with about a 3-point band.**
Publishable with the caveat stated.

**Recommended fix.** One sentence in v8: where both a deferral and a named task
split appear, the named split governs and the score is 3. Then re-code the ~168
affected documents — not the whole template group.

**Process note worth keeping.** The underlying ambiguity was found by reading
what coders reported struggling with, which worked. The tenfold mis-sizing came
from trusting a regex over the source text, and was corrected by reading twelve
documents. Any corpus-level claim in this project should be checked against the
actual text before it is written down; see also the two figures corrected in
`prompts/README.md`.

---

## 2. Exam-only device requirements are coded two ways — SYSTEMATIC

**The problem.** Rules R3 and R11 give opposite answers for the same sentence.
R3 says a requirement scores on the requirement fields even if it binds only
some meetings. R11 says a rule covering only exams leaves ordinary class
meetings unaddressed, so the score stays 0. A sentence like

> On exam days, you must bring a charged device that has the LockDown Browser
> installed

is both at once, and coders split on it. Seven different coders raised this
independently, which is how it was found.

**Size.** 94 documents mention LockDown Browser; 78 are coded so far.

| laptop_score | laptop_required | documents |
|---|---|---|
| 0 | false | 10 |
| 1 | true  | 58 |
| 4 | false | 3 |
| 4 | true  | 6 |
| 5 | true  | 1 |

The 0-versus-1 split is the disagreement: 58 one way, 10 the other, on
substantially the same template. A further 46 documents use the "charged
device" phrasing without naming LockDown Browser.

**Why it matters more than 2% of the corpus suggests.** These are concentrated
in one department's language-course template. One coder reported the sentence
driving 16 of 25 laptop scores in a single batch. A corpus-level laptop figure
barely moves; a department-level breakout for Spanish & Portuguese moves a lot.

**Recommended fix.** v8 needs one sentence resolving the precedence, applied as
a re-code of the affected documents rather than a patch. The majority reading
(score 1, required true, exam scope in `coder_notes`) is defensible and is what
most coders chose; the minority 10 should be brought into line with whichever
reading is adopted. **Do not publish a laptop-requirement figure until this is
closed.**

---

## 3. Multi-column PDFs extracted with interleaved columns

71 documents are laid out in columns, and `pdftotext -layout` interleaves them
line by line. The text is verbatim but reads as nonsense across column
boundaries. IDs are in `data/multicolumn_ids.json`.

Confirmed: plain `pdftotext` (no `-layout`) reads these in the correct order.

Two knock-on effects seen in coding: evidence quotes from these documents come
back as unreadable fragments ("W  e are a tech-free"), and at least one coder
had to split a single sentence into two half-quotes because the rule forbids
stitching across a column break. Both are correct behavior given bad input.

**Status: re-extraction pending, then re-code those 71.**

---

## 4. Chemistry exam-clause documents

21 documents carry an exam-integrity clause that reads as a device rule.
Recommended handling: score 3, with the exam scope in `coder_notes`. Not yet
normalized.

---

## 5. Near-duplicate syllabi are not deduplicated

Exact content hashing catches byte-identical files (60 clusters). Syllabi that
differ only by a section number or a date hash differently and survive as
separate documents. Coders reported these constantly — one batch was "effectively
21 distinct documents" out of 25; another had five byte-identical copies of one
statistics syllabus.

This inflates the weight of departments that template heavily. **Any
department-level breakout needs a near-duplicate pass first.** A corpus-level
figure is affected much less.

---

## 6. Generic device wording inflates the phone scale

Rule R7 applies a rule about "electronic devices" to both the phone and laptop
scales, which is the right reading of the text but has two consequences:

- `phone_required` is overstated wherever a syllabus requires "a device" and
  means a computer. Coders flagged disjunctive requirements repeatedly
  ("a computer, tablet, or smartphone", "phone or device to take pictures").
  **Needs a correction factor before the figure is quoted.**
- Identical phone and laptop scores may mean the syllabus never distinguished
  them, not that the instructor set matching policies. Report phone/laptop
  agreement only with this stated, or use a three-bucket framing: names phones
  specifically / names laptops specifically / generic device language.

---

## 7. Rule gaps coders reported but v7 does not cover

Recorded because each one is a place where the score is the coder's judgment
rather than the codebook's instruction. None is resolved.

- **Emergency carve-outs.** "Banned unless it is a life-threatening emergency"
  is a stated exception that is not instructor discretion. R1 only describes
  instructor-permission escapes, so 4-versus-5 here is unguided.
- **No "discouraged" anchor on the AI scale.** "Strongly discouraged but not
  barred" has no clean home; coders put it at 2 with low confidence.
- **Boilerplate versus instructor text.** Where college boilerplate ("phones are
  turned off") contradicts the instructor's own permissive rule, v7 gives no
  tiebreak. Coders split between `contradictory` and letting the more specific
  text govern.
- **"Partial basis" template with no split named.** R10 has three branches;
  a template that neither enumerates tasks nor defers to the instructor fits
  none of them. Coders defaulted to 3.
- **Rules stated as a grade consequence** ("check your phone, anticipate zero
  points") rather than as a prohibition. Not covered by R12.
- **Non-policy prose** — a phone mentioned in a grade description or on an
  appended recruitment flyer. Coders split between 0-with-a-note and scoring it.

---

## 8. Loader rejections — CLOSED

13 rejections were logged to `data/rejected.jsonl` across the run. All were
re-coded and passed on a later attempt; none is outstanding. The final load is
4,089 records with zero rejections, and `scripts/verify_evidence.py` re-checks
all 11,497 stored quotes against the stored documents: **100% match exactly,
zero not found.**

A note on reading that log: the loader stores an evidence *array* joined with a
blank line. Checking the joined string as though it were one quote fails on
every multi-quote row and looks exactly like fabricated evidence. Two ad-hoc
audits made that mistake before `verify_evidence.py` was written to do it once,
correctly. Use the script rather than a fresh query.

---

## 9. Document 2040 — re-coded once after quarantine, now fixed

A file of personnel records — roughly 43 job interviews with named candidates —
was published on UT's public syllabus site. It is quarantined on our side and
still live on theirs.

**It came back once.** The document's text had been removed from the database,
but a coder file still existed on disk when batch 081 was coded, so the document
was scored and the row loaded — carrying an interview record header as evidence.
It was caught by reconciling the coded count against the corpus count: one more
policy row than there were documents with text. The row is deleted, the record
purged from the batch file, and the loader now refuses outright to score any
document whose text is null, so a stale coder file cannot reinstate one.

**Two open editorial decisions: whether to notify UT, and whether the exposure is
itself a story.** See `docs/methodology.md` §4.

---

## 10. Not a data issue: database credential

The Neon connection string was shared in plaintext at the start of this project
and has not been rotated.
