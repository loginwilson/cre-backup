---
name: decoder-length-law
description: "The bootcamp verdict is a teaching artifact; the DB record is a distillation — claim gate, verbatim exception, summary generated from rows"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-22T23:53:47.061Z
---

Settled 2026-08-22: "the db is designed to distill documents and if we get
too long it would defeat its purpose."

- **Two products, never conflated.** The bootcamp verdict teaches (long on
  purpose, never stored). The DB record distills — already ~30:1 (run 20:
  27 pages → 2 rows). Rows aren't the bloat risk; CLAIMS are.
- **Claim gate:** a claim earns storage only if it (a) fills a row slot,
  (b) is a chain edge (cite to another instrument), or (c) changes what a
  broker would do. Test (c) kills the noise at 10M-document scale.
- **Verbatim is the paid exception** — store exact wording only where the
  words ARE the fact (sunset, exculpation, subordination conditions);
  paraphrase silently loses meaning. Anchors are addressing, always
  mandatory.
- **The summary is GENERATED FROM the rows, not written beside them** —
  1-2 sentences, composed after the table. Caps length structurally AND
  becomes a completeness check: a sentence needing facts the rows lack
  means the rows are incomplete.
- **Budget = signal, not cap:** 1-5 rows · ≤15 claims · ≤3 sentences.
  Exceeding it means the document is a PACKAGE to split, or the gate
  isn't being applied. Never truncate to hit the number.
- **Compute:** at ~60M pages output tokens dominate; 800 tok/page vs 250
  roughly triples cluster wall-clock. Terseness is throughput.

Full text in `D:\CRE Decoding System\Bootcamp\Bootcamp.md` (THE LENGTH
LAW). See [[project-decoder-bootcamp]], [[assumption-law-grading]].
