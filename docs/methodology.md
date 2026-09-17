# How we measured device and AI policies in UT syllabi

**Status: complete. All 4,089 classifiable documents are coded and loaded.
Two cleanup items remain open and are flagged where they affect a number;
see `docs/known-issues.md`.**

This document explains where the data came from, how each syllabus was scored,
what we did to check the scores, and what the data cannot support. It is written
to be argued with. If you think a number is wrong, the last section tells you
exactly how to prove it.

---

## 1. The short version

We collected every syllabus UT published for Fall 2026 — 4,094 documents
covering 6,968 course sections and 2,475 instructors — converted 4,089 of them
to searchable text (§4 accounts for the five), and scored each one on three separate 0-5 scales: how tightly
it controls **phones**, how tightly it controls **laptops**, and how tightly it
controls **generative AI**.

The scoring was done by a language model working from a written codebook, in
batches of 25 documents, with no knowledge of the results of any other batch.

**The scoring is not asked to be trusted.** Every score above zero carries one
or more quotes pulled verbatim from the syllabus, and every quote was checked by
a program, character by character, against the stored text of that syllabus
before the score was allowed into the database. A score whose quote does not
literally appear in the document is rejected and never loaded. So the underlying
claim of this dataset is not "a model judged this syllabus strict." It is: *here
is the sentence the instructor wrote; here is the bin we put that sentence in;
go read it.*

That is a stronger evidentiary standard than most hand-coding projects meet,
because human coders rarely record the sentence that drove their decision.

---

## 2. Where the documents came from

Texas Education Code §51.974 requires public universities to post syllabi for
undergraduate courses on a publicly accessible website, no login required. UT
does this at:

```
https://utdirect.utexas.edu/apps/student/coursedocs/courses/nlogon/
```

We queried all 282 departments in the site's own dropdown for Fall 2026, in
residence. Everything we collected was already public and free to read; we
added no credentials and bypassed nothing. The technical quirks of the site are
documented in `docs/source-notes.md`.

Syllabi arrive through two channels, and both were collected:

| Channel | How it works | Documents |
|---|---|---|
| Direct download | A PDF or Word file at `/download/<id>/` | 3,282 |
| Simple Syllabus | A web app that renders the syllabus in the browser | 812 |

The second channel is the one worth flagging: those syllabi are not files. They
are pages built by JavaScript after the page loads, so an ordinary download gets
an empty shell. We rendered each one in a real headless browser and saved the
resulting text. Had we skipped them, we would have silently dropped a fifth of
the corpus, and not at random — Simple Syllabus adoption varies by college, so
the missing fifth would have been concentrated in particular schools.

**Deduplication.** Files are stored under the SHA-256 hash of their contents, so
a syllabus posted under several course IDs is stored once and linked to each.
This is why the document count (4,094) is smaller than the section count
(6,968): one document often serves many sections of the same course.

---

## 3. The unit-of-analysis problem

This matters more than any other methodological choice here, because it is the
one most likely to produce a wrong number in print.

A syllabus is not a course, and a course is not an instructor. The same PDF may
cover eleven sections. One instructor may post four different syllabi. So
"38% of syllabi restrict phones" and "38% of classes restrict phones" are
different claims, and only the first is what we measured.

Concretely: 1,383 **documents** mention ChatGPT, but those documents cover
2,259 **sections**. Reporting documents as if they were classes would be off by
roughly 900.

Three denominators are available, and the story should name which one it uses:

| Denominator | Corpus | Coded | What a percentage of it means |
|---|---|---|---|
| Documents | 4,094 | 4,089 | share of posted syllabi |
| Sections | 6,968 | 6,963 | share of scheduled class sections |
| Instructors | 2,475 | 2,473 | share of instructors |

The coded column is the denominator used in §9. It is smaller because four
encrypted files yielded no text and one document was quarantined (§4).

An early measurement of one indicator moved from 38.2% to 39.7% to 43.2% across
these three — same underlying data, three defensible sentences. **Recommended
default: sections**, because "what share of UT classes ban phones" is the
question readers actually have, and because it does not over-weight departments
that post one templated syllabus across many sections.

**Near-duplicates, measured.** Content hashing catches only byte-identical
files. Syllabi differing by a section number, a room or a date hash differently
and survive as separate documents. `scripts/find_near_duplicates.py` groups them
by word-shingle similarity: **354 clusters covering 978 documents, of which 624
are redundant copies — 15.3% of the corpus.** The largest are a 27-copy rhetoric
template, a 22-copy Spanish template and a 13-copy cello studio family.

Collapsing them moves the headline figures by **−0.7 to +1.3 points**, so
corpus-level percentages stand as reported. Department-level breakouts do not:
templating is concentrated in particular departments, so a Spanish or rhetoric
breakout computed per document would be badly over-weighted. Compute those per
cluster, using the `near_duplicate_group` column.

---

## 4. Getting the text out

Nothing can be scored that was not read correctly, so this stage got its own
verification.

| Method | Documents | Notes |
|---|---|---|
| Existing text layer | 3,257 | Read directly from the PDF |
| Rendered from web app | 812 | Simple Syllabus, captured from the browser |
| OCR | 20 | Scanned or image-only PDFs |
| Encrypted, not recovered | 4 | Password-protected; decryption failed, no text |
| Quarantined | 1 | See below |
| **Total** | **4,094** | of which **4,089 yielded text and were coded** |

The four encrypted files are the only genuine extraction losses: 0.1% of the
corpus. They are counted here rather than quietly dropped, and they are excluded
from every percentage in §9 because there is nothing in them to score.

Two failure modes were found and fixed during this stage, and both are the kind
that would have quietly corrupted results:

**Text that isn't text.** Nine PDFs had a text layer that passed every
size-based sanity check but decoded to gibberish — the font was subset with a
scrambled character map, so the file "contained text" that was really a cipher.
A character-count check cannot catch this. We added a check that looks for
common short words, and re-OCR'd the failures. Eight recovered cleanly. The
ninth was a French-language syllabus that our English-only word list had falsely
accused, which is why the check now covers six languages.

**Columns read across, not down.** 71 PDFs are laid out in multiple columns, and
the default extraction setting interleaves the columns line by line, producing
text that looks fine but reads as nonsense across column boundaries. These are
recorded in `data/multicolumn_ids.json` and re-extracted with column-aware
settings. *(Cleanup pass in progress.)*

**One document was removed from the corpus.** Document 2040 is not a syllabus.
It is a 14 MB file of personnel records — roughly 43 job interviews for a
College of Liberal Arts career-coach position, with named candidates and
written assessments of each. It was published on UT's public syllabus site,
where it remains live. We removed its text from our database, deleted our copy
of the text, and logged the removal in a `quarantined_documents` table rather
than deleting the record silently. A scan of the full corpus found no other
document of this kind. **An open editorial question: whether to notify UT that
the file is exposed, and whether the exposure is itself a story.**

---

## 5. What was actually measured

Three scales, scored independently, 0-5. Zero always means the syllabus does not
address that thing; 5 is the tightest control. The full anchors are in
`prompts/policy-classification-v7.md`.

Alongside each scale, two fields that deliberately sit **off** the 0-5 axis:

- **`<scale>_required`** — whether students are told to *have* the thing. A
  syllabus can require a laptop and restrict its use in class; that is one
  coherent policy, and a single strictness scale can only hold half of it.
  Before this field existed, coders were discarding one of the two facts on
  roughly one document in twenty.
- **`<scale>_status`** — `clear`, `undecided`, or `contradictory`. This keeps
  apart two situations that look identical in a single number: an instructor who
  wrote two rules that genuinely conflict, and an instructor who posted an
  unedited template and never chose. As one coder wrote about a template case,
  the score has "no principled basis." Those documents belong outside a
  strict-versus-lenient ratio, not averaged into it.

### How the codebook was built

The instrument went through seven versions before the production run. Every
revision is recorded in `prompts/README.md`, including what broke and why. Two
are worth repeating here, because they are cases where a plausible-looking rule
would have produced a badly wrong published number:

- **v2's rule R1** said that any stated exception dropped an absolute ban from 5
  to 4. But accommodation language is nearly universal: 95% of documents in this
  corpus contain the word "accommodation" and 75% name UT's disability services
  office. Read literally, that rule would have emptied the strictest category
  almost completely — the exact bin the story is about. It was caught because a
  coder flagged the ambiguity instead of quietly picking a reading.
- **v2's rule R2** banned inference so broadly that "Computer: PC or Mac" in a
  required-materials list scored as *silence on laptops*, discarding a syllabus
  that plainly does tell students to have a computer.

Neither error would have been visible in the output. Both were found by reading
what the coders said they struggled with — which is why every batch is asked to
report its hard calls, and why those reports are read.

### The scoring was version-controlled

`document_policies.prompt_version` records which codebook version produced each
row. Revised instructions add a comparable pass rather than overwriting the old
one, so the size of a revision's effect can be stated rather than asserted.

900 documents carry scores under both v6 and v7. Comparing them:

| scale | scores changed | moved 2+ bins | strict share, v6 → v7 |
|---|---|---|---|
| Phone | 4.6% | 20 | 75.8% → 79.0% (+3.2) |
| Laptop | 4.2% | 21 | 53.7% → 56.2% (+2.5) |
| **AI** | **11.3%** | 12 | **36.7% → 46.4% (+9.8)** |

This is worth sitting with. The device scales barely moved — v7's device changes
were clarifications, and they behaved like clarifications. **The AI scale moved
almost ten points** on the same 900 documents, because v7 rewrote the rule
governing the university's "partial basis" template, which a quarter of the
corpus uses.

Two things follow. First, the instrument is sensitive to how one rule is worded
on the scale where the language is newest and least settled, which is exactly
what §7.7 says about the remaining band. Second, this is why a published figure
has to name its codebook version: "half of AI policies are restrictive" and
"a third of AI policies are restrictive" are both defensible sentences about the
same syllabi under two versions of the same instrument, six weeks apart. The
version is part of the claim, not a footnote to it.

---

## 6. How the scores are checked

Four independent checks. They test different things, and none of them requires
taking the classifier's word for anything.

### 6.1 Every quote is machine-verified (audited: 11,497 quotes, 0 failures)

This is the backbone. Each score above zero must carry verbatim evidence, and a
loader program checks each quote against the syllabus text as stored in the
database. Quotes that do not match are **rejected and never loaded** — the record
is skipped whole and the reason written to `data/rejected.jsonl`.

The check normalizes only what PDF extraction demonstrably breaks: smart quotes,
zero-width characters, the non-breaking spaces UT boilerplate is full of, and
line-break hyphenation. It does not normalize meaning and does not accept
paraphrase. Coders are forbidden from stitching sentences together or
reconstructing across column breaks. A looser second pass would accept a 0.92
similarity match to tolerate broken ligatures.

**The audit.** `scripts/verify_evidence.py` re-checks every stored quote against
every stored document after the fact, without trusting the loader:

| | |
|---|---|
| rows audited | 4,089 |
| quotes checked | 11,497 |
| matched exactly | **11,497 (100.00%)** |
| needed the looser pass | 0 |
| not found | **0** |

Every quote matches its syllabus character for character. The looser pass exists
but was never once required. Run the script to reproduce this.

**This check caught a real error of ours.** We re-extracted document 2352's text
and updated the database but forgot to regenerate the copy the coder was reading.
The coder scored 86 KB of mojibake that no longer existed anywhere. The validator
caught it immediately, because it checks against the database rather than against
the coder's input. `scripts/export_for_coding.py` now regenerates coder files
from the database and reports any that were stale.

### 6.2 Inter-coder agreement (175 documents, measured)

Seven batches, selected by a recorded random seed before the run began, were
coded a second time by an independent coder that never saw the first result.

**Results.** Krippendorff's alpha uses the ordinal difference function; exact and
within-one agreement are also given, because alpha alone is hard to interpret.

| scale | exact | within one bin | alpha | documents differing |
|---|---|---|---|---|
| Phone | 96.6% | 99.4% | 0.982 | 6 |
| Laptop | 98.3% | 99.4% | 0.992 | 3 |
| AI | 98.3% | 100.0% | 0.995 | 3 |

The off-scale fields agree at 98.9-100%. Only **two** documents in 175 differ by
more than one bin on any scale.

**Independence was verified, not assumed.** Two passes could agree because one
saw the other. They did not: on 74% of documents the two coders chose *different
verbatim quotes* to justify the same score, and 99% of their written notes differ
entirely. The scores converge while the reasoning artifacts diverge, which is
what genuine independent coding looks like.

**What this number does and does not mean — read this before quoting it.**

Alpha of 0.98 is higher than published content analysis usually reports, and
that should raise an eyebrow rather than settle the question. The reason is that
both coders are the same kind of reader applying the same instructions. Two human
undergraduates bring different priors, different attention, and different
tolerance for ambiguity; two runs of the same model bring far less of that
variation. So this figure measures the **reproducibility** of the instrument -
does the codebook return the same answer when applied again - and not its
**validity**, which is whether that answer is correct.

A codebook can be perfectly reproducible and consistently wrong. If a rule
mis-reads a common phrasing, both passes mis-read it identically and agreement
stays at 0.98. That is precisely the correlated-error risk described in §8, and
this statistic is blind to it by construction.

**So the honest claim is narrow:** the scores are not arbitrary, and re-running
the process would produce materially the same dataset. Anyone who wants to know
whether the scores are *right* has to look at §6.3, which is the only check that
compares against a different kind of reader.

**The disagreements are informative.** Both wide ones sit exactly where coders
reported the codebook is thin: document 251 (laptop 2 vs 0) turns on whether a
passing mention of a device is a permission or silence, and document 1005 (phone
3 vs 5) on whether a politely worded directive with a soft hedge is a rule or a
preference. Both are on the v8 list in `prompts/README.md`.

### 6.3 Sealed human validation set (200 documents)

200 documents were drawn at random and sealed **before any instructions were
written**, and have never been used to develop or tune the codebook. Desk staff
can code these by hand from the same written instructions and compare against
the machine scores.

This is the check that answers "should we believe any of this," and the only one
that requires no trust in the classifier at all. It is deliberately sized so that
a few people can finish it in an afternoon. **We recommend doing it before
publication, and reporting the result whatever it is.**

### 6.4 Spot-checking by anyone, at any time

Because every score carries its quote and its source URL, any individual row can
be verified in about thirty seconds by opening the syllabus and reading the
sentence. There is no step where a reader has to accept a judgment they cannot
inspect. An editor who wants to check twenty rows before signing off can do
that.

---

## 7. What this data cannot tell you

Stated plainly, because these will be asked. Open defects and pending cleanup
are tracked separately in `docs/known-issues.md`, with measured sizes.


1. **A syllabus is not a classroom.** We measured what instructors *wrote*, not
   what they enforce or what students experience. A strict written policy that
   is never enforced scores 5. This is a real and unfixable limitation of
   syllabus data, and the story should say so early rather than defend it later.

2. **We cannot measure change over time yet.** This is one semester. Any claim
   that policies got stricter "this year" needs a prior-year corpus, which we do
   not have. The site does serve past semesters, so this is collectable — but it
   is not collected, and the current data cannot support a trend sentence.

3. **Generic device wording blurs the phone/laptop distinction.** Many syllabi
   say "electronic devices" without naming phones or laptops. Rule R7 applies
   such a rule to both scales, which is the right reading of the text, but it
   means that when a document's phone and laptop scores are identical, that may
   reflect *absence of specificity* rather than a deliberate matching policy.
   Do not report phone/laptop agreement rates without accounting for this.
   A three-bucket framing — names phones specifically / names laptops
   specifically / generic device language — is more honest than a two-way split.

4. **`phone_required` is inflated** by the same generic wording, and needs a
   correction factor before it is quoted.

5. **Exam-only rules are not class rules — and the codebook is not yet
   consistent about them.** A ban that applies only during exams leaves ordinary
   class meetings unaddressed, and scores 0 with a note. Scoring it otherwise
   would assert a restriction the instructor did not write — but scoring 0
   without the note, as one coder put it, "asserts a silence that isn't real."

   A sentence that is *both* a requirement and exam-scoped ("on exam days, bring
   a charged device with LockDown Browser installed") hits two rules that point
   opposite ways, and coders split on it: of 78 affected documents coded so far,
   58 scored the laptop requirement and 10 scored silence. This is the clearest
   example of the correlated-error risk described in §8, and it was found the way
   §8 says such errors get found — seven coders raised it independently. It is
   tracked as issue 1 in `docs/known-issues.md`. **A laptop-requirement figure
   should not be published until it is resolved.**

6. **Smart glasses and display eyewear sit outside all three scales.** 200
   documents (4.9%, covering 382 sections) mention them, and a new McCombs
   "Smart Glasses Course Policy" bans them outright. Because eyewear is neither
   a phone nor a laptop, those bans are recorded in `coder_notes` and score 0.
   **56 documents — about a third of the coded smart-glasses set — score 0 on
   both device scales while actually carrying a device ban**, so they read as
   silent when they are not. That is 1.4% of the corpus, and it understates the
   strict end rather than overstating it. They are scored 0 with a note, because they are
   neither phone nor laptop. This is arguably its own small story rather than a
   flaw.

7. **The AI conditional/restricted boundary carries about a 3-point band.**
   A quarter of the corpus uses UT's "generative AI is permitted on a partial
   basis" template. The rule that sorts those documents asks whether the
   instructor named which tasks may use AI or deferred to later instruction, and
   it does discriminate — but it does not say which wins when a syllabus does
   both. 257 documents (7.6% of those stating an AI policy) are affected.
   Flipping all of them moves the strictness figure between **49.1% and 56.7%**
   against 50.9% as coded. Report the band; do not report a bare 51%. Tracked as
   issue 1 in `docs/known-issues.md`.

8. **The codebook is a set of choices, not a law of nature.** Where to draw the
   line between 3 and 4 is a judgment. It is written down, applied consistently,
   and versioned — but a different newsroom drawing the line differently would
   get different percentages from the same syllabi. The bins are in the repo;
   anyone is free to disagree with them in public.

---

## 8. On the use of a language model

Most of this desk is skeptical of AI-produced work, and the skepticism is
well-placed. So it is worth being precise about what the model did and did not
do here.

**What it did not do:** it did not decide what to measure, did not write the
scales, did not choose the bins, and did not produce a single number that goes
into the story without a human-readable quote attached.

**What it did:** read 4,094 documents and apply a written codebook to each one —
the mechanical part of content analysis. That work is normally done by
undergraduate coders working from exactly this kind of codebook, with exactly
this kind of reliability check. The method here is standard content analysis;
only the coder changed.

**Why that is checkable in a way "the AI said so" is not:**

- Every score is anchored to a verbatim quote, machine-verified against the
  source. There is no step that rests on the model's summary of a document.
- The quotes make the classifier's errors *visible*. If it mis-scores, the quote
  it cited is right there and obviously does not support the bin.
- Agreement is measured, not assumed (§6.2), and against humans, not just
  against itself (§6.3).
- The codebook is versioned, so a published number is traceable to the exact
  instructions that produced it.

**The honest risk** is not random error — the per-row check handles that. It is
*correlated* error: a systematic misreading of one common phrasing, applied the
same way to hundreds of documents. The v2 R1 near-miss described in §5 is
exactly this failure mode. Three things guard against it: the sealed human set
(§6.3), which would show a systematic gap; the requirement that every batch
report its hard calls, which is how R1, R2, R10 and R12 were all caught; and the
version comparison, which puts a size on how much a rule change moves the
numbers.

**What we recommend before publication:** complete the human validation set
(§6.3) and report the agreement figure in the story or a methods box, whatever
it turns out to be. If the desk codes 200 syllabi by hand and agrees with the
machine on the great majority, the finding stands on evidence rather than on
anyone's confidence in the tool. If it does not, we would rather find out
ourselves.

---

## 9. Results

All 4,089 classifiable documents, covering 6,963 sections and 2,473 instructors.
Run `scripts/analyze_policies.py` to regenerate every figure below; it prints
each one by document, by section and by instructor, so the denominator is never
implicit. Percentages here are by document unless stated.

### Does the syllabus address it at all?

| | documents | share | sections | share |
|---|---|---|---|---|
| Phones | 1,606 | 39.7% | 2,945 | 42.3% |
| Laptops | 2,067 | 51.1% | 3,564 | 51.2% |
| Generative AI | 3,369 | 85.3% | 5,800 | 83.3% |

**Most syllabi say nothing about phones at all.** Three in five are silent.
That is itself a finding, and it is the necessary context for everything below:
the strictness figures describe the minority of instructors who chose to write a
rule.

### Among those that do address it, how strict?

| | strict (4-5) | conditional (3) | permissive (1-2) |
|---|---|---|---|
| **Phones** | **80.8%** | 9.2% | 10.0% |
| **Laptops** | 57.8% | 3.7% | 38.5% |
| **Generative AI** | 50.9% | 34.6% | 14.5% |

### The headline

**When a UT instructor writes a phone policy, four times in five it restricts or
bans the phone outright.** 546 syllabi (13.5% of all documents) prohibit phones
with no stated exception; another 751 restrict them to permitted uses. Only 161
syllabi that mention phones are permissive about them.

**Laptops are a different story, not a milder version of the same one.** 1,092
syllabi — 26.9% — *require* students to have a laptop, and 38.5% of those that
address laptops are permissive. Instructors are not moving against screens in
general; they are moving against phones specifically, while increasingly
depending on laptops.

**AI is the most-addressed and least-settled.** 85.3% of syllabi take a position,
but they scatter: a quarter prohibit it outright, a third set conditions, and
2.8% could not be scored at all because the instructor left an unedited template
with more than one option still in it — the highest unscorable rate of the three
scales, and a sign of how recently this language was bolted on.

### Figures that carry a caveat

- **AI strictness: 50.9%, band 49.1-56.7%.** 257 documents (7.6% of those
  stating an AI policy) sit on an unsettled rule boundary. See §7.7.
- **`phone_required` (5.3%) and `laptop_required` (26.9%) are overstated** by
  syllabi that require "a device" generically. See §7.3 and issue 6.
- **56 syllabi that ban smart glasses score 0 on both device scales**, so the
  strict end is understated by roughly that much. See §7.6.
- **Department-level breakouts must be computed per near-duplicate cluster**,
  not per document. See §3.

## 10. How to audit this yourself

Everything below runs against the database and needs no special access beyond
the connection string.

**Check a single score.** Every row in `document_policies` has a document ID.
Join to `documents` for `source_url`, open the syllabus, and read the sentence in
`phone_evidence`, `laptop_evidence`, or `ai_evidence`. If the quote is not there
or does not support the score, that is a finding — please report it.

**Check a random sample.** Pull 20 rows at random, verify each. Twenty rows is
about ten minutes and is enough to notice a systematic problem.

**Re-run the quote verification from scratch.** `scripts/load_classifications.py`
performs the check described in §6.1. It can be run against the raw classifier
output at any time and will report every mismatch.

**Re-code a batch by hand.** `prompts/policy-classification-v7.md` is the full
codebook. Anyone can apply it to 25 syllabi and compare.

**Re-run everything from the source.** `scripts/build_manifest.py`,
`fetch_pdfs.py`, `fetch_simple_syllabus.py`, `extract_text.py` and
`load_database.py` rebuild the corpus from UT's website. The syllabus site is
public and unauthenticated.

**Reported figures must name their codebook version** (`prompt_version`) and
their denominator (§3). A percentage without both is not reproducible.
