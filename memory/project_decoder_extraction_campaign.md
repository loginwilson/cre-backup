---
name: project-decoder-extraction-campaign
description: "Extraction campaign decisions 2026-08-24 — extraction-ready gate defined; single VLM + escalation ladder (OCR channel retired); three deliverables + evidence-only rule; mode vocabulary is the reader's first decision; bootcamp cross-grading; model chosen when compute arrives"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-24T12:39:14.504Z
---

**Login's five extraction-campaign decisions, 2026-08-24:**

1. **EXTRACTION-READY GATE (now defined):** a doc that has "passed
   synchronization" = doc id + both urls + recorded_details + pdf + keyed
   bbl — a pure column test. Edge: `imageless` is a VERDICT not a gap;
   those docs (FT_ era heavy) are extraction-ready FROM RD ALONE.
2. **SINGLE VLM, OCR CHANNEL RETIRED as design direction** — modern
   vision LLMs have OCR built in; the problem is hallucination, not
   reading. Anti-hallucination = evidence rules + multi-read bands +
   an ESCALATION LADDER: base model reads all; uncertainty triggers
   (self-disagreement, anchor-region failure, self-validation arithmetic
   failure, cross-grader disagreement) escalate the page to a much larger
   model (27B-class+; Kimi/Qwen-max/oss alphas). ⚠ MODEL NOT PINNED —
   deliberately decided when NYU-compute resources are in hand; models
   change too fast to pre-commit. NEAR-TERM TEST: distilled/quantized
   repo builds of 27B-class models at ~4B footprints in the open harness
   on the laptop.
3. **EXTRACTION'S THREE DELIVERABLES:** (a) read rd+pdf UNDER THE
   FUNCTIONS — every page understood as pertaining to the 11 functions;
   (b) events → clean data tables; (c) anybody summary GENERATED FROM the
   table. THE RULE ABOVE ALL: extract evidence and fact, never infer or
   assume — inference is hallucination; context-with-proof only.
   ⚠ MODE CORRECTED (2026-08-24, from Bootcamp.md itself): the mode
   vocabulary is SETTLED — three modes (transacts / observes / signals),
   clause-level, assigned PER EVENT never per document (one deed carries
   all three); it is NOT the instrument form and CANNOT be derived from
   doc-type codes ("many documents fail to capture their mode in the type
   filing and may have many" — login). The real gap = `observes` is weak
   ("reliably RECITAL, not proven observation") — the recital-laundering
   risk. Mode work = accrete case law THROUGH bootcamp runs, one miss per
   entry. Run order canon: functional read-through → data table → anybody
   summary → grade + why it matters → fixes + record → next run.
4. **GRADING = bootcamp loop, upgraded to CROSS-GRADING:** open model in
   harness extracts AND Claude extracts; each grades the other —
   disagreement doubles as an escalation trigger (two models rarely share
   a hallucination). bakeoff/extract.py = the mechanical regression floor
   (3 hand-keyed docs; the only role-assignment scorer) — run it, keep it
   as CI for the spec.
5. **Cluster harness = acquisition discipline applied to reading** (gates,
   denominators, zero-byte/resume traps) — engineering later; the draw
   board already selects docs by borough/type/era/pages.

Sequence while pdfs pull: bootcamp molds spec → mode vocabulary → test
distilled 27B-config + wire cross-grading → bakeoff as regression floor.
Timeline math: acquisition ≈ 20 days on the laptop (network-paced);
decode ≈ 100+ years on the laptop vs WEEKS on cluster (~750M pages) —
the compute IS the barrier to entry ([[project-decoder-philosophy]]).

Related: [[project-decoder-bootcamp]], [[project-acris-ocr-stack]],
[[project-decoder-phase-assertions]], [[project-acris-extraction-resolver]]
