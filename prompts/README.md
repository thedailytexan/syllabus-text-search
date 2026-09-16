# Classification prompts

The coding instructions used to score syllabi. Versioned because the scores
depend entirely on them: if the wording changes, the numbers change, and any
published figure has to be traceable to the exact instructions that produced it.

`document_policies.prompt_version` records which version scored each row, so
revised instructions add a comparable pass rather than overwriting the old one.

## Versions

- **v1** (retired) — two scales, devices and AI. Piloted on 24 documents. It
  broke in five places, all of which v2 fixes:
  - Phones and laptops were one score, so "laptops for notes, phones out of
    sight" collapsed into a single number and lost the distinction the story is
    about.
  - No rule for instructor-permission exceptions, so two syllabi with the same
    "banned unless I permit it" structure scored 5 and 4.
  - No rule against inferring, so a mandatory clicker system was read as a
    device requirement in one syllabus and ignored in another.
  - Bans covering only some assignments were scored as course-wide bans.
  - Abridged syllabi that point elsewhere were scored "not addressed", which
    put them in the same bucket as syllabi that genuinely have no policy.

- **v2** (retired after one pilot round) — three scales: phone, laptop, AI,
  with rules R1-R5 and a `document_completeness` flag. Splitting phones from
  laptops proved worth it immediately: the two scored differently in 29% of the
  pilot documents. But R1 and R2 were both wrong in ways that mattered:
  - **R1 said any stated exception dropped a ban from 5 to 4.** Accommodation
    language is nearly universal in this corpus - 95% of documents contain the
    word "accommodation" and 75% name the disability services office by name -
    so read literally that rule would have emptied the strictest category almost
    entirely: the exact bin the story is about. Caught because the coder flagged
    the ambiguity rather than quietly picking one reading.
  - **R2 banned inference so broadly it suppressed real policies.** "Computer:
    PC or Mac" in a required-materials list was being scored 0, discarding a
    syllabus that does plainly tell students to have a computer.

- **v3** — same three scales. Fixed two rules:
  - **R1a**: disability accommodations never count as an exception. A ban that
    is absolute except for documented accommodations is still a 5.
  - **R2**: an explicit instruction to have or bring a device counts wherever it
    appears, including a requirements list; only course *mechanics* (clickers,
    Canvas quizzes, handwritten work) are excluded.
  - **R3**: requirements and restrictions are scored differently - a laptop
    required for workshop days only is still a requirement, not silence. For AI,
    required-for-some-and-barred-for-others is conditional, not required.
  - **R6**: contradictory sentences get the enforceable rule, low confidence,
    and both sentences quoted.
  - **R7**: a rule about generic "electronic devices" applies to both scales.

- **v4** — contract fix, no change to scoring. Two rules asked coders to write
  notes inside the evidence quote, which cannot be verbatim and annotated at the
  same time; every coder hit it. Evidence became an array of quotes, each checked
  on its own, with a separate `coder_notes` field.

- **v5** — two fields moved OFF the 0-5 scale, which now measures only
  how tightly use is controlled:
  - **`<scale>_required`**: whether students are told to HAVE the thing. A
    syllabus can require a laptop and restrict its use; that is one coherent
    policy, and the single scale could only hold half of it. Coders were
    discarding one of the two facts on about one document in twenty.
  - **`<scale>_status`** (`clear` / `undecided` / `contradictory`): whether a
    policy could be determined at all. Keeps two different situations apart -
    an instructor who wrote two rules that clash, and an instructor who shipped
    an unedited template and never chose. One coder put it plainly about a
    template case: the score has "no principled basis". Those belong outside a
    strict-versus-lenient ratio, not inside it.
  - **R8** states that a requirement plus a restriction is NOT a contradiction,
    so those cases do not get swept into `contradictory`.

- **v6** (current) — adds **R9**: the university class-recording statement
  (HOP 2-9970) is not a device policy. It appears in most syllabi and governs
  recording rather than device use, so leaving it to each coder's judgment would
  drift across hundreds of batches. A "Technology Policy" heading containing
  only the recording statement is silence on devices, and scores 0.

- **v7** (current) — resolves three inconsistencies that showed up once the run
  reached production scale, each reported independently by several coders:
  - **R10**: the UT "permitted on a partial basis" AI template appears in 437
    documents, 10.7% of the corpus, and was being scored 2, 3 or 4 depending on
    who read it. It now splits on what the instructor did with the template: naming
    permitted tasks is conditional (3), deferring entirely to later instructor
    permission is restricted (4), leaving more than one option in is `undecided`.
    The split preserves a real difference rather than flattening the template to
    one number.
  - **R11**: a device rule covering only exams is not a rule for ordinary class
    meetings, so the score stands, but scoring 0 there "asserts a silence that
    isn't real". The rule must now be recorded in `coder_notes` whenever that
    happens, so the 5% of documents affected stay recoverable.
  - **R12**: politely worded directives are still rules. "Please put your phone
    away" was being scored anywhere from 3 to 5 on verb strength alone. A
    directive to stop using a device scores 4-5; "silence your ringer" governs
    the ringer, not use, and scores 3.

## Measuring reliability

The results are checked three ways, and all three have to be set up during the
run because none can be reconstructed afterwards:

1. **Inter-coder agreement** — eight batches (200 documents) are coded a second
   time by an independent coder that never sees the first result. Reported as
   exact and within-one agreement per scale.
2. **Human validation** — 200 documents were drawn and sealed before any
   instructions were written, and have never been used to tune them. Desk staff
   can code these by hand and compare.
3. **Per-row verification** — every non-zero score carries a quote checked
   character-by-character against the stored syllabus text, so any single row
   can be confirmed without trusting the classifier at all.


## A note on the figures above

The corpus counts quoted in this file were re-measured against the loaded
database on 2026-09-16 and two were corrected: the accommodation-clause share
(previously given as 86%) and the size of the "partial basis" AI template
(previously given as 955 syllabi / 23%). Both originally came from ad-hoc
queries during development and neither reproduced. The queries behind the
current figures are in `docs/methodology.md`, §5 and §10.

## Proposed for v8

Every item below was reported independently by several coders during the v7
production run, in their own words, as a place where the codebook does not
settle the call. Sizes are measured against the database where measurable. None
is a defect in the data already collected — each is a place where the score
records the coder's judgment rather than a written rule, which is exactly what a
codebook exists to prevent.

Ordered by how many documents each would move.

1. **R10 precedence: deferral plus a named split.** Where a syllabus both defers
   AI permission to later instruction AND names which tasks may use AI, R10 does
   not say which governs. Coders consistently let the specific split win, which
   is the right reading and should be written down. **~168 documents.**

2. **R3 vs R11 for exam-only device requirements.** "On exam days, bring a
   charged device with LockDown Browser installed" is both a requirement (R3
   scores it) and exam-scoped (R11 leaves normal meetings at 0). v8 must pick
   one. **94 documents mention LockDown Browser, 46 more use "charged device"
   phrasing, plus a College of Pharmacy ExamSoft block in 11 syllabi.**
   Concentrated in language and pharmacy templates, so it distorts department
   breakouts more than corpus figures.

3. **Where wearables belong.** 200 documents mention smart glasses or display
   eyewear, and UT colleges are now issuing a dedicated smart-glasses policy.
   Eyewear is neither a phone nor a laptop, so those bans currently score 0 with
   a note — and **56 documents score 0 on both device scales while carrying an
   outright device ban**, reading as silent when they are not. Either add a
   fourth scale or state that a wearable ban counts on Scale A.

4. **Disjunctive requirements.** "A computer, tablet, or smartphone", "bring
   your smartphone or laptop", "a phone or device to take pictures" — no single
   device is actually required, but the `_required` fields have no way to record
   "one of these". Coders variously set one flag, both, or neither. This is the
   main driver of the `phone_required` inflation already noted.

5. **Exceptions that are not instructor discretion.** R1 describes
   instructor-permission escapes and R1a exempts accommodations, but neither
   covers "banned unless it is a life-threatening emergency", a scheduled break
   for catching up on messages, or "step outside to take the call". Coders split
   4 vs 5 on these.

6. **No "discouraged" anchor on the AI scale.** "Strongly discouraged but not
   prohibited" has no home; coders default to 2 at low confidence.

7. **Boilerplate versus instructor text.** Where college boilerplate ("phones
   are turned off") contradicts the instructor's own permissive rule, v7 gives no
   tiebreak, and coders split between `contradictory` and letting the more
   specific text govern.

8. **Leftover faculty-facing template notes.** R10's third branch sends a
   syllabus to `undecided` when the section is addressed to faculty. It fires too
   readily: several syllabi keep a "[Note: instructors may customize...]" line
   but add a real rule beneath it. v8 should say the instructor's own rule
   overrides a leftover note.

9. **Software requirements that imply a device.** "Install R on your computer",
   "have a full copy of Excel", "download the Honorlock extension" — a device
   requirement, or course mechanics? R2 excludes mechanics but does not address
   software.

10. **Rules stated as a grade consequence.** "Check your phone and anticipate
    zero points" is a rule, but R12 only covers directives.

11. **Activity bans that name no device.** "No texting, surfing, or tweeting"
    closes off phone use without banning the phone, and leaves laptop
    note-taking open. The anchors do not cover "device allowed, these uses
    barred".

### One mechanical note, already handled

Several coders reported that UT boilerplate contains non-breaking spaces
(U+00A0) mid-sentence, so a quote retyped with ordinary spaces fails a literal
substring check. The loader normalizes NFKC before comparing, which maps U+00A0
to a space, so this never caused a rejection. Coders writing their own
verification scripts should normalize the same way.
