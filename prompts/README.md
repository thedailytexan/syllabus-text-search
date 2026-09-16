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
  - **R1 said any stated exception dropped a ban from 5 to 4.** 86% of syllabi
    in the corpus carry a disability accommodation clause, so read literally
    that rule would have emptied the strictest category almost entirely - the
    exact bin the story is about. Caught because the coder flagged the
    ambiguity rather than quietly picking one reading.
  - **R2 banned inference so broadly it suppressed real policies.** "Computer:
    PC or Mac" in a required-materials list was being scored 0, discarding a
    syllabus that does plainly tell students to have a computer.

- **v3** (current) — same three scales. Fixes both:
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
