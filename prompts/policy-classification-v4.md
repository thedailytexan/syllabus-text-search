# Syllabus policy classification — v4

You are coding university syllabi for a Daily Texan data story. Make THREE
separate judgments per syllabus, each on its own 0–5 scale. All three run the
same direction: 0 = the syllabus does not address it, 5 = strictest.

Phones and laptops are scored separately because syllabi routinely treat them
differently — "laptops for notes only, phones out of sight" is one policy, and
collapsing it into one number destroys the thing we are measuring.

## Scale A — phones (mobile phones, smartwatches)
## Scale B — laptops (laptops, tablets, computers in class)

Both use the same anchors:

0  not addressed — the syllabus says nothing about it
1  required      — students are told to bring or have one for class
2  permitted     — use explicitly allowed, no real restriction
3  discouraged   — asks students to limit or avoid use, but states no rule
4  restricted    — allowed only for stated purposes (notes, readings, in-class
                   activities), or only with the instructor's permission
5  prohibited    — banned with NO stated exception

## Scale C — generative AI (ChatGPT, LLMs, "AI tools") in coursework

0  not addressed — the syllabus says nothing about AI use
1  required      — AI use is built into assignments; students must use it
2  permitted     — broadly allowed, usually with disclosure or citation
3  conditional   — allowed for some tasks or assignments and barred for others
4  restricted    — only with explicit instructor permission
5  prohibited    — banned course-wide with NO stated exception

## Scoring rules

**R1 — An instructor-permission escape drops it to 4.** If the syllabus says the
instructor may allow otherwise ("unless authorized by the instructor", "except
where expressly permitted", "unless I indicate otherwise"), score 4, not 5.
Score 5 when the ban has no such escape. The escape is often the sentence right
after the ban, so read on.

**R1a — Disability accommodations are NOT an exception.** Almost every syllabus
carries a Services for Students with Disabilities / Disability & Access clause,
and an accommodation route is a legal obligation, not a relaxation of the
policy. Ignore accommodation language completely when applying R1. A ban that
is absolute except for documented accommodations is still a 5. Only a general
instructor-discretion escape triggers R1.

**R2 — Score statements, not mechanics.** Do not derive a policy from how the
course runs. Online quizzes, clicker or response systems (SquareCap, iClicker),
Canvas exams, or handwritten in-class work are NOT device policies on their own.

But an explicit instruction to have or bring a device IS a policy, wherever it
appears — including a requirements list. "Computer: PC or Mac" under required
materials, or "you will need a laptop for this course", scores 1. The test is
whether the syllabus TELLS students to have, bring, or use the device, not
whether the course implies one.

**R3 — Mixed rules.**

For AI: if some work allows AI and other work bars it, that is 3 (conditional) —
including when AI is *required* for part of the course. Use 1 only when AI is
required and nothing in the course bars it. Reserve 5 for a course-wide ban.

For phones and laptops, restrictions and requirements behave differently:
- Restrictions (3, 4, 5): if the rule varies by activity, score the rule for
  normal class meetings and say so in the evidence.
- Requirements (1): if students are told to bring a device for ANY class
  session — including workshop or lab days only — score 1. Do not discard a
  stated requirement because it covers only some meetings.

**R4 — Ignore the instructor's contact block.** "Phone: 512-555-0100" or
"Email / Phone" in a contact header is NOT a phone policy. This was the single
most common error in the last pass. Check that your evidence is an actual rule
about classroom use before scoring anything but 0.

**R5 — Body language beats headings.** A heading reading "REQUIRED DEVICES"
above a body that says a laptop is "highly suggested" is not a requirement.
Score the operative sentence, not the header.

**R6 — Contradictory sentences.** When two sentences state different rules for
the same device and neither is more specific, score the one that states an
enforceable rule, set confidence to "low", and cite BOTH sentences by putting
them in the evidence array (see below).

**R7 — Generic "devices".** A rule about "electronic devices" with no further
detail applies to BOTH the phone and laptop scales. Score both the same, quote
the generic sentence, and note the generic wording in `coder_notes`.

## Other requirements

- Read the WHOLE document before scoring. Policies sit under headings like
  "Class Policies", "Attendance", "Academic Integrity", or "Technology".
- **0 means genuinely silent.** Never use 0 as a middle value, and never infer
  a permissive policy from silence.
- A university-wide boilerplate statement still counts if it states a rule.
- `evidence` is an ARRAY of quotes copied EXACTLY as they appear in the file,
  each max ~200 characters. Usually one quote; use several when a rule is split
  across sentences (R6). Never join separate sentences into one string with
  "/" or "..." — each array element is checked against the document on its own
  and a stitched-together quote will be rejected. If the extracted text is
  garbled ("genera?ve"), reproduce the garbling. You may join lines wrapped
  mid-sentence and drop invisible zero-width characters; do not change any
  visible character. Use an empty array when the score is 0.
- `coder_notes`: optional, one short line. Use it for anything you would
  otherwise want to write into the evidence — generic wording, a rule that was
  close between two scores, a caveat. Never put commentary in `evidence`.
- `confidence`: "high" when the language is explicit, "medium" when you are
  reading between the lines, "low" when genuinely unsure.
- `document_completeness`: "stub" if this is an abridged summary or placeholder
  that points elsewhere for the real syllabus (its silence tells us nothing);
  otherwise "full".

## Output

Write a JSON array to the output file you are given. One object per document,
in the order given, exactly this shape:

```json
[
  {
    "document_id": 1234,
    "document_completeness": "full",
    "phone_score": 5,
    "phone_label": "prohibited",
    "phone_evidence": ["Cell phones must be muted and out of sight."],
    "phone_confidence": "high",
    "laptop_score": 4,
    "laptop_label": "restricted",
    "laptop_evidence": ["Laptops and tablets may be used only for typing notes."],
    "laptop_confidence": "high",
    "ai_score": 3,
    "ai_label": "conditional",
    "ai_evidence": ["You may use AI to brainstorm, but not to draft your essays."],
    "ai_confidence": "high",
    "coder_notes": null
  }
]
```

Labels must match the scale wording above exactly. Output nothing but the file.
