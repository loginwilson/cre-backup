---
name: feedback_live_source_over_transcription
description: "Login's rule: live-feed the authoritative source (e.g. the Zoning Resolution) for anything needing exact values — a transcribed table cannot carry the footnote that IS the regulation"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 176544e8-656c-4540-a15c-f710beced15e
  modified: 2026-08-05T21:06:08.927Z
---

**Login, 2026-08-05:** *"You should probably live feed into the Zoning
Resolution as your source I would think for anything that relies on exact zoning
information."* Then: *"do you have direct acces to ZR or do i need to make an
excel for that too?"* — Answer: direct access, no Excel needed.

**Why:** a transcription flattens a conditional rule into a scalar. ZR 23-22
lists R6 at 2.20 in its own row and again as "R6¹" in the 3.00 row, where
footnote 1 reads *"For zoning lots, or portions thereof, located within 100 feet
of a wide street"*. A chart transcribed into a table has nowhere to put that, so
R6 becomes either 2.20 or 3.00 and one of them is wrong on every lot. Verified
live: 26 of 27 districts in the hand-transcribed table agreed with the
Resolution, and **the single disagreement was exactly the district whose rule
lived in a footnote** — someone had "corrected" R6 to a flat 2.20 and deleted a
real regulation.

The failure mode is not carelessness. It is that transcription has no slot for a
condition, so the loss is invisible in the result and the table looks complete.

**How to apply:**
- For anything requiring exact values, fetch the authority at run time rather
  than copying it. Cache the *parsed facts*, never the page — same discipline as
  [[project_acris_decoder]]'s document images.
- Keep the source's own version marker (`LAST AMENDED`) as part of the fact, so
  a re-run detects an amendment instead of silently serving a stale number. That
  is monitoring, which is a first-class goal here, not an extra.
- Model the value as **(value, condition)**, never a bare number, whenever the
  source states a condition.
- When a transcribed table already exists, do not discard it — run the live
  source against it and report the disagreements. The agreements tell you the
  transcription was careful; the disagreements tell you where its *format* could
  not hold the rule.
- Ask before building an intake path the user would have to feed by hand: check
  whether the source is directly reachable first.

Same family as [[feedback_confidence_backcheck]] — a new trap re-run over prior
work — and [[feedback_bkrea_scale_failure]], where the output validated itself.
