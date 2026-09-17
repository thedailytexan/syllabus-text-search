# How we measured generative-AI policies in UT syllabi

This is the reporting method for the generative-AI findings only. Phone and
laptop policy scores are excluded: independent re-coding found those device
rules too ambiguous for publication.

## Collection and text extraction

UT's public Syllabi & CVs site was queried department by department for every
Fall 2026 in-residence section. Querying by department avoids the site's
1,000-result cap; the collection covered 282 departments and 6,968 sections.

The site publishes two kinds of syllabus. We downloaded 3,282 unique direct
PDF/Word documents and rendered 812 Simple Syllabus web-app documents in a real
browser, because their initial HTML is an empty application shell. PDFs with a
usable text layer were read directly; scanned documents were OCR'd. The
collection keeps source URLs, content hashes, extracted text, and source IDs so
each result can be traced back to the public record.

Exact duplicate files are stored once by SHA-256 hash but remain linked to every
section that uses them. This is storage deduplication, not analytic merging.
Near-identical syllabi that differ by a date, room, or section number remain
separate source documents until the class-policy grouping rule is applied.

The extraction audit found 71 multi-column PDFs whose original layout-preserving
text interleaved columns. Those were downloaded again, hash-checked against the
stored corpus, re-extracted with plain `pdftotext`, and re-coded before the
canonical results below were computed.

## Getting the text out

Text extraction was deliberately verified before policy coding. The corpus has
five mutually exclusive outcomes:

| Method or outcome | Documents | Handling |
|---|---:|---|
| Existing PDF text layer | 3,257 | Read directly with Poppler |
| Rendered Simple Syllabus page | 812 | Browser-rendered text saved from the web app |
| OCR | 20 | Character recognition after the PDF text layer failed |
| Encrypted | 4 | Retained in the corpus count but excluded from policy analysis |
| Quarantined | 1 | Retained as an audit record but excluded from policy analysis |

Before accepting an embedded PDF text layer, the extractor checks both text
density per page and whether it contains ordinary words across six languages.
This catches subset-font PDFs that contain plenty of decodable characters but
actually produce a substitution cipher. Failed text layers were OCR'd; OCR was
not run over the whole corpus because it is slower and can degrade documents
that already contain usable text.

The four encrypted files could not be opened without an uploader password. The
quarantined file was publicly posted by UT but was not a syllabus; its text was
removed to avoid retaining personnel records. Neither category is silently
dropped: both remain in the corpus accounting and neither receives an AI score.

Multi-column layout was a separate failure mode. `pdftotext -layout` preserved
tables but interleaved text across columns in 71 files, leaving sentences in the
wrong order. The corrected pass uses plain `pdftotext` for those identified
documents and verifies that each downloaded source still has the original
SHA-256 hash before replacing its stored text.

## Corpus and reporting dataset

We collected Fall 2026 syllabi published by UT Austin: 4,094 unique documents
covering 6,968 sections. Four encrypted documents and one quarantined,
non-syllabus file have no usable text, leaving 4,089 classifiable documents.

`reporting_policies` is the canonical dataset. It uses the targeted v8 record
where a document was corrected and its v7 record otherwise, giving one AI score
per classifiable document. Percentages must state their denominator: documents,
sections, and instructors are not interchangeable.

For the class-policy results below, repeated offerings collapse only when the
same instructor teaches the same course with the same complete AI-policy vector
(score, status, and requirement flag). Different instructors and different
courses remain distinct even if they use a common template.

This means a class-policy count can exceed the number of unique documents. One
stored document is linked to 32 percussion sections across course codes including
`PER 201`, `PER 210`, `PER 251`, `PER 260`, and `PER 490`, with several
instructors. It is one uploaded file but many instructor–course observations.
Conversely, repeated sections by the same instructor in the same course with
the same policy count once. The resulting 4,790 class-policy groups are fewer
than 6,963 sections but more than 4,089 unique documents.

## AI scale

Scores run from 0 to 5: 0 not addressed; 1 required; 2 permitted; 3 conditional
(allowed for some tasks and barred for others); 4 restricted (only with explicit
permission); 5 prohibited. The complete rules are in
`prompts/policy-classification-v7.md` and `policy-classification-v8.md`.

The v8 clarification matters: when a syllabus both defers AI permission and
names permitted or prohibited tasks, the named task split controls and scores 3.

Every nonzero score has verbatim evidence. The loader rejects a record unless
each quote is found in the stored syllabus text after only extraction-noise
normalization.

The full corpus evidence audit checked 11,497 stored quotes; the targeted v8
correction checked 1,529 more, all exact matches. Each score is therefore an
inspectable claim about a sentence in the source, not a trust-me model summary.

## Results

Of 4,089 classifiable syllabi, 3,369 (85.3%) address generative AI; they cover
5,800 of 6,963 class sections (83.3%). Among syllabi that address AI, 50.9% are
restricted or prohibited (scores 4–5), 34.6% conditional (3), and 14.5%
permissive or requiring AI (1–2).

The table exposes every bin. “Documents” counts distinct syllabus documents;
“class-policy groups” applies the instructor–course grouping rule above. The
clear denominators are 3,949 documents and 4,599 class-policy groups.

| AI score | Meaning | Documents | Class-policy groups |
|---:|---|---:|---:|
| 0 | Not addressed | 580 | 674 |
| 1 | Required | 39 | 47 |
| 2 | Permitted | 450 | 532 |
| 3 | Conditional | 1,166 | 1,327 |
| 4 | Restricted | 733 | 815 |
| 5 | Prohibited | 981 | 1,204 |
|  | **Total, clear policies** | **3,949** | **4,599** |

Under the class-policy grouping, 3,925 groups address AI. Of those, 2,019
(**51.4%**) are restricted or prohibited, 1,327 (33.8%) are conditional, and
579 (14.8%) are permitted or require AI. This is close to the document-level
strict share of 50.9%, so repeated offerings do not drive the AI headline.

## Independent re-coding

Two blinded, non-overlapping random samples of 200 syllabi were re-coded by
independent model agents using the written rules. The second sample excluded
every document in the first. This measures model-to-model reproducibility, not
human validity.

| Sample | Exact agreement | Within one bin |
|---|---:|---:|
| First 200 | 91.0% | 100.0% |
| Second 200 | 90.0% | 96.0% |

All 396 AI evidence quotes in the first sample and every quote in the second
sample were checked against their source text; the second sample required three
quote corrections before passing validation. Across both samples, 361 of 400
scores matched exactly (90.3%) and 392 were within one bin (98.0%). The observed
disagreement is much lower than for device policies, but reproducibility is not
proof that the bins are objectively correct. 

## What the model did—and did not do

The model applied a written, versioned codebook and returned the source quote
for each nonzero score. It did not choose what to measure, invent the score
anchors, or supply an uncited headline statistic. The central risk remains
correlated error: multiple model runs can make the same systematic mistake on a
common wording. Independent model agreement reduces concern about random drift,
but it does not replace a human audit.
Human auditor reviewed 20-ish syllabi by hand and found that scores were mostly 
consistent.

## Limits

This measures written syllabus policies, not classroom enforcement or student
experience. It is one semester, so it does not establish change over time.
The scale is a transparent editorial choice, not a natural fact; readers can
inspect the source quote and disagree with a bin.

The collection is limited to what UT publicly posted at collection time. Four
encrypted documents could not be read, and one publicly posted file that was
not a syllabus was quarantined and excluded rather than silently deleted.
