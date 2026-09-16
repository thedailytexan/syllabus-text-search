# Syllabus policy classification — v6

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

## Two fields that sit OUTSIDE the 0-5 scale

The scale measures one thing only: how tightly USE is controlled. Two common
situations do not fit on that line, so they get their own fields.

**`<scale>_required`** (true/false) — does the syllabus tell students to HAVE or
BRING the thing? This is independent of the score. "Bring a laptop to every
class, and use it only for notes" is one coherent policy: `laptop_score` 4
(restricted) AND `laptop_required` true. Score 1 (required) is for the case
where a device is required and NO restriction on its use is stated. For AI,
`ai_required` true means students are made to use AI for some work, even when
the score is 3 because other work bars it.

**`<scale>_status`** — could a policy be determined at all?
- `clear` — a policy is determinable, including determinable silence (score 0).
  This is the normal case; use it unless one of the below plainly applies.
- `undecided` — the document raises the topic but never settles it. Unedited
  template blocks left in ("[PROHIBITION]" and "[PERMITTED]" both present),
  bracketed placeholders, a "Technology Policy" heading with no rule beneath
  it, or boilerplate addressed to faculty rather than students. The instructor
  did not make a choice.
- `contradictory` — the document states two rules that cannot both be followed,
  and neither is more specific. Quote both in the evidence array.

Score everything as best you can even when status is `undecided` or
`contradictory` — the score records your best reading, the status records that
it should not be counted in a strict-versus-lenient ratio.

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
the same device and neither is more specific, set status to `contradictory`,
score the one that states an enforceable rule, set confidence to "low", and
cite BOTH sentences in the evidence array.

**R9 — Class-recording statements are not device policies.** Most syllabi carry
the university statement about recording lectures (HOP 2-9970, "students may not
record class without permission"). That governs RECORDING, not whether a device
may be used in class. Never score it on the phone or laptop scale. The same goes
for a "Technology Policy" heading whose only content is the recording statement -
that is silence on device use, so score 0.

**R8 — Requirement and restriction together.** When a syllabus both requires a
device and limits its use, these are not in conflict and the status is NOT
`contradictory`. Set `<scale>_required` true and score the restriction. Do not
discard either fact.

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
    "phone_required": false,
    "phone_status": "clear",
    "phone_evidence": ["Cell phones must be muted and out of sight."],
    "phone_confidence": "high",
    "laptop_score": 4,
    "laptop_label": "restricted",
    "laptop_required": true,
    "laptop_status": "clear",
    "laptop_evidence": ["Laptops and tablets may be used only for typing notes."],
    "laptop_confidence": "high",
    "ai_score": 3,
    "ai_label": "conditional",
    "ai_required": false,
    "ai_status": "clear",
    "ai_evidence": ["You may use AI to brainstorm, but not to draft your essays."],
    "ai_confidence": "high",
    "coder_notes": null
  }
]
```

Labels must match the scale wording above exactly. Output nothing but the file.
