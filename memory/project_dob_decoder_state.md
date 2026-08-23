---
name: project_dob_decoder_state
description: DOB decoder — document access REFUSED at the BIS edge; NOW has no zoning columns at all; a row is not a job; findings live in decoder/DOB_TRAPS.md
metadata: 
  node_type: memory
  type: project
  originSessionId: 5e3987d2-a689-4455-ba4f-ed13d53b22e6
  modified: 2026-08-14T18:39:41.263Z
---

Chat 2 of the parallel decoder project (`Decoder Prompt/decoder`). Full measured
findings are in **`decoder/DOB_TRAPS.md`**; `dob.py` carries them as code.

**⚠⚠ THE REFUSAL BELOW IS SUPERSEDED — SOLVED IN THE DEVELOPMENTS CHAT.**
Login, 2026-08-14: *"youre wrong. we figured that one out in the developments
chat."* Do NOT plan BIS acquisition from the note below and do NOT re-derive it
by probing; retrieve the working method from that conversation when BIS starts.
A stale blocker is as costly as a missing finding — this one would have thrown
away real coverage. The *rules* it carries still stand for other sources (a
policy in prose on a landing page counts; a refusal is recorded FAILED, never
"complete with 0 facts"); the BIS verdict does not.

**~~DOCUMENT ACCESS IS REFUSED~~ (tested 2026-08-06 — SUPERSEDED, see above).**
`a810-bisweb.nyc.gov` landing page returns 200, but
`/bisweb/JobsQueryByNumberServlet` returns **403 Access Denied at the Akamai
edge**. And there IS a published policy — not in `robots.txt` (both DOB hosts
403 their own), but in prose on the BIS landing page: DOB "may take steps to
protect our information systems against unauthorized software programs that
automatically extract data." The 403 is that step, already in force.
`a810-dobnow.nyc.gov` was separately in a maintenance outage.
Recorded in the sink as `DOB_DOCS` **FAILED**, never as "complete with 0 facts".

**⚠ DOB NOW HAS NO ZONING COLUMNS AT ALL** — checked against dataset metadata,
all 95 columns of `w9ak-ipjd`: no zoning district, no zoning floor area, no lot
area, no FAR. Absent from the schema, not sparse. It carries
`total_construction_floor_area`, which is NOT zoning floor area. NOW is the
current system, so for every new building filed since ~2021 the structured
envelope gap is 100% — and the document that closes it is behind the refusal.

**A ROW IS NOT A JOB — this dissolved the brief's headline gap.** BIS `doc__=01`
is the original, `02+` are amendments that restate nothing (zoning_dist1 present
on 0 of 63,293 NB amendment rows). On originals the district is 100%, not "24%
missing". The one real BIS gap is an ERA: `proposed_zoning_sqft` is 1.9% before
2008 and 100% from 2009. NOW: 939,107 rows = 555,652 jobs; New Building is 9,432
jobs, not 54,043 rows.

**Contacts:** only the developer genuinely needs the document. Architect
phone/email is NOT in DOB data — the licence register has no architect/engineer
type, applicants are PE/RA licensed by NY State, and joining on licence number
"resolves" 37% entirely by collision (23.9% of register numbers are reused
across types). Contractor phone is 99.6% of 4M BIS permits and unused. DOB NOW
does not name the permittee at all.

Related: [[reference_socrata_pagination_order]] (found here, affects every
decoder), [[project_bkrea_dob_field_traps]], [[feedback_bkrea_document_over_page]].
