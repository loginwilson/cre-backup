---
name: project_decoder_bootcamp
description: "THE BOOTCAMP is the one authority for the decoder's extraction model — its path, its rule (a rule not in the bootcamp is not a rule), and the lessons that keep getting re-learned"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-20T02:44:48.217Z
---

`D:\CRE Decoding System\Bootcamp\Bootcamp.md` — **the ONE authority.** Every
other md in the system (18 of them) carries a pointer header: *"Never redefine
a term in this file; correct it there and it corrects everywhere. A rule that
is not in the bootcamp is not a rule."* Login, 2026-08-19: *"each lesson
learned needs to go to bootcamp. we always forget and the convo compacts and
forgets."* **Read it before touching extraction.** Version-stamped (`hb-YYYY.MM.DD-rNN`)
and every extraction records the version that read it.

Its spine, so a fresh session knows what it will find:

- **the event row** — `mode · subject · function · effect · from · to · quantity · term`,
  plus `event_id | row` and provenance `doc_id | page | signed | effective | recorded`
- **three tiers** — SPINE (`mode·subject·function·effect`, never `unread`; below it
  there is no event, only a claim) / DIRECTION / MEASURE
- **`effect`** — `creates · transfers · modifies · releases`. Added 2026-08-19 by a
  4-page TL&R drawn at random: without it a termination is indistinguishable from a
  grant, and **20.7% of the corpus (4,977,173 docs, 17 types) is a release**. Never
  infer it from direction — role inversion scores 100% and reverses the lineage.
- **five states** for an unfilled field — value · `n/a`+reason · `unread` (held,
  unrecoverable) · `not attempted` (never opened) · **`unavailable`** (the source
  does not have the page). Each names a different owner of the gap — DOCUMENT,
  READER, SOURCE — and only `unread`/`not attempted` are work this system can do.
- **eleven functions**, closed set, `lexicon.canon()` the one normalizer
- **mold-then-freeze** — the bootcamp molds the table around COMMON patterns,
  then it FREEZES and the pull writes directly into it. Escalate, never add columns.

Lessons that cost the most and will be re-learned if forgotten:

⚠ **Read the WHOLE document.** A retracted "trial" was built from a legacy
decode while the 110-page PDF sat on disk. The per-lot numbers were in an
exhibit on page 38. G-027: *a test that cannot fail proves nothing.*

⚠ **The price is on the cover page, and two stamps cross-check it.** ACRIS
reports `document_amt = 0` for every DEVR. NYC RPTT ÷ 2.625% and NYS RETT ÷ 0.4%
both derived $5,000,000 to the dollar on `2010102601040006`. Two independently
rated taxes agreeing IS the confidence.

⚠ **The notices block and signature page unmask the SPE** — the index carried
three bare LLCs; the document named Extell/Dov Hertz and The Sabet Group/Alfred
Sabetfard, and showed one person signing two "different" owners. See
[[project_bkrea_reach_ladder_roles]].

⚠ **`executed` is two dates.** A dateline saying *made **as of*** is an
effective date; the acknowledgment is when signatures were taken. 307 days
apart on one instrument. Carry `signed`, `effective` and `recorded` separately.

⚠ **The source can be short and every check still reads clean.** The City
Register declared 116 pages; ACRIS serves 110 and the placeholder thereafter.
The only witness is the count printed on the cover — **which is an image** — so
`declared − held` is an extraction output, never a pipeline gate.

Related: [[project_decoder_function_model]] (the eleven nouns),
[[feedback_decoder_extraction_loop]] (the VLM loop's own rules),
[[feedback_confidence_backcheck]] (re-run every new trap over earlier work).
