---
name: project-decoder-phase-verbs
description: "The phase verbs (enumerate..produce) and the rule that EFFECT lives in the rule base joined at derive, never stamped on the extracted event"
metadata: 
  node_type: memory
  type: project
  originSessionId: 36a502fe-953e-4ab9-ab0c-cd3194ce697c
  modified: 2026-08-27T15:12:43.841Z
---

Login's phase vocabulary, 2026-08-27 (the three phases are unnamed; the verbs
are the settled part):

```
phase 1   enumerate → synchronize → navigate → register → document → organize
phase 2   prepare → extract → reorganize → resolve
phase 3   derive → produce
```

**⚠ `prepare` IS THE RULE BASE, NOT IMAGE PREP.** I assumed page-splitting and
resolution; login means assembling the REGULATORY FRAMEWORK decoding reads
against. That placement is what makes an event mean anything - a document says
`SATISFACTION OF MORTGAGE` and nothing in it says "this ends an encumbrance."

**⚠ THEREFORE `effect` DOES NOT BELONG ON THE EVENT ROW.** I had proposed the
extracted event carry begins/ends/modifies/transfers. Wrong twice over: it
makes extraction depend on the rule base (breaking the isolation rule), and it
freezes today's interpretation into the data. The split is:

| step | produces |
|---|---|
| prepare | the RULE - what a type/function does to a state |
| extract | the FACT - type, dates, parties, parcels, amounts + citation |
| derive | the JOIN - fact cite + rule cite → a state |

**The payoff: sharpen the rule base and every state table recomputes without
re-reading one document.** 20M extractions stay valid; only the join re-runs.
Effect baked into events would make a rule fix a re-extraction campaign. Same
principle as [[feedback-live-source-over-transcription]] - an event that has
already absorbed its effect cannot be re-interpreted later.

**`organize` vs `reorganize` are two DIFFERENT re-sorts** (this is why both
verbs exist): `organize` (end of phase 1) is document→lot, which is the keying
ladder plus `doc_lot`. `reorganize` (phase 2) is event→lot by EVENT date, and
is only possible after extract.

**⚠ `reorganize` MUST DO NO THINKING** - fan out by parcel, sort by date,
nothing else. It is the tripwire on extract: if reorganize ever needs to
decide something, extract did not finish its job. The judgment sits at the two
ends (isolated in extract, collective in resolve) with a mechanical step
between. Note it is a FAN-OUT, not a sort: an event on 4 lots appears in 4 lot
views, so counts multiply (~2.5x, same ratio as lots/doc).

**⚠ `extract` READS BOTH rd AND IMAGE. I over-generalized and login corrected
it 2026-08-27.** I had ruled "never show the reader the rd", inflating a
NARROW measured finding (priming the VLM with an OCR CANDIDATE FOR THE FIELD
IT IS READING transferred the error: `73241` → `732491` twice) into a blanket
ban on the rd. Two things break it: **174,142 documents have NO IMAGE**, so
that rule produces ZERO events for exactly the population keying exists to
serve; and the reader legitimately needs context. The surviving rule is
PER-FIELD, not per-source:

| the field is in | do |
|---|---|
| rd only (recording stamp, ACRIS type) | use it - no independence to lose |
| image only (Schedule A, metes, exhibits, terms) | rd cannot prime it |
| BOTH (parties, parcels, amount, dates) | read separately, RECONCILE |

The rd is a **separate CLAIM STREAM, not prompt context**. Both sources emit
claims; resolution reconciles - a claim can hold disagreement, an event
cannot. Narrow prohibition that remains: do not put the rd's value for field X
in the prompt while reading field X off the page. Bonus: disagreement rate
against fields ACRIS already publishes is a free, continuous quality signal on
the decoder.

See [[project-acris-party-not-a-key]] for the routes feeding `organize`,
[[project-decoder-seven-phases]] for the phase tree,
[[project-decoder-extraction-order]] for the isolation rule.
