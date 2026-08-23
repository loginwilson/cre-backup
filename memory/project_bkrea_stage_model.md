---
name: bkrea-stage-model
description: "SETTLED development state machine — what counts as a development, the four stages and their triggers, status as one clock, and which DOB field proves each transition"
metadata: 
  node_type: memory
  type: project
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-07-31T11:38:42.077Z
---

**Settled with the operator 2026-07-30/31 over a long evidence-driven session. Every number below was measured, not assumed.**

**WHAT IS A DEVELOPMENT** — a filed project, nothing earlier. Signals (rezoning/variance applied, sale with dev intent, cleared, assembled) stack on the parcel as dated tags but never create a development. **Demolition is a SIGNAL, not a development** — only 47.3% of demolished BBLs ever see a build filed after (floor: same-BBL only, lineage would raise it), and 10,717 of 12,909 DM-governed sites are cleared lots with nothing filed. Dropping DM as a trigger takes the pipeline 92,498 → 79,589.

**THE TRIGGER** — qualifies if: `New Building` · `ALT-CO – NB with Existing Elements` · any A1/Alteration CO with `enlargement_sq_footage > 0` · or a conversion with `total_construction_floor_area ≥ 10,000 sf` (= the existing `DEFAULT_DEV_SITE.minRemainingSf`, so one constant). Never: demolition, companion filings ("PLUMBING SPECIFICATIONS FILED IN CONJUNCTION WITH…"), fences, sheds, scaffold. **Job type alone is NOT proof of intent** — A1 is 48.6% of the pipeline and spans warehouse→300 apartments down to a bathroom that shifted the occupancy code. The proof is added floor area or a new building.

**THE CHAIN**
```
filing            → PRE-DEVELOPMENT   (rungs: Filed → In review → Approved)
work permit ISSUED→ CONSTRUCTION
TCO (Initial)     → TEMPORARY OPERATION
final CO          → OPERATION / Delivered
```
⚠ **Job approval is NOT construction** — approval is the design passing plan exam; the work permit is a licensed contractor committing money. 85.5% approved vs 39.1% permitted: over half of approved jobs never pull a permit.

**STATUS = one value, one clock, everywhere:** Active (within clock, pre-Operation) · Stalled (clock expired) · Delivered (reached Operation, clock freezes on last filing). Stalled is ORTHOGONAL to stage (26,730 parcels, 29%) — never a tree level, it would double every lane. Each stage has its OWN natural clock: pre-dev = filing silence (no natural term, a judgment call), construction = **permit expiry** (an exact date), temporary operation = **TCO renewal, roughly quarterly** (45,846 renewals vs 8,741 initials ≈ 5 per building — the tightest clock in the system, currently on the loosest setting).

**VELOCITY = permit renewals.** Construction permits expire annually; renewing costs money. `sequence_number` + `filing_reason` (`Initial Permit` / `Renewal Permit With/Without Changes`) is the whole velocity signal compressed to one integer — which is why it won't drown like tracking every filing did. ⚠ `seq=1` is AMBIGUOUS: 51.7% of new buildings finish inside the one-year term (median 353 days). Disambiguate with completion — seq=1 + signed-off/CO = finished fast; seq=1 + expired, no completion = stalled.

**PHYSICAL PROOF differs by project type** (measured): new build = `Support of Excavation` / `Earth Work` / `Foundation` — you cannot pull a foundation permit without digging (SOE is 4.0% of NB permits vs 0.8% of alterations). Enlargement = Foundation appearing on an Alteration CO (8.6%). **Conversion = NO physical proof exists** — interior GC+MEP is indistinguishable from a renovation. So: one trigger, two labelled grades — **Physical** (ground permit) vs **Presumed** (GC only). Include conversions and say the evidence is weaker; holding them out would mean never tracking the LIC story.

**TWO ERAS.** 2002–2021 = PLUTO before/after snapshots (outcome only; these are resolved). 2022–now = DOB NOW end to end. Handoff crossed in 2021–22; since 2023 BIS has received **5 New Buildings** — the residue is legacy amendments. See [[bkrea-dob-field-traps]].

Related: [[bkrea-dev-card-grammar]], [[bkrea-devbulk]], [[bkrea-dream-card]], [[bkrea-change-tracking]].

**DEVELOPMENT CARD — CLOSED 2026-07-31 (operator: "I feel good about development and can always come back to it").** Shape settled: identification-only masthead (address · what-it-is · owner · BBL, one `space-y-1.5` rhythm, no toggle) → summary as **BEFORE → PROJECT → AFTER** ("An 81,500 sf 2-story commercial building, demolished in 2021 — designed by…") → 2×2 widget grid, **always four tiles**, dashes where absent, guarded so an all-empty row hides → category/status chips on the same grid → Project details as **discrete filled blocks** (`bg-white/[0.045]`, `gap-2`) because a hairline separates but does not GROUP. Development repainted off sky-blue onto the card palette — hue is reserved for FAMILY in the bucket tree.

**TWO POPULATE-TIME CONTRACTS (operator, not yet built):**
1. **EXACT source document per block, never a generic label.** Today reads "DOB filing" / "PW1" / "ACRIS · billing lot"; must become `ZD1 · Q00697532-I1`, `PW1 · Q00697532-I1`, `ACRIS doc 2018103100123`, `MapPLUTO 26v1`. Every ID already exists in the pulled data.
2. **Every field editable.** `OverrideField` in `components/map/card/primitives.tsx` already implements it exactly — source vs override, status dot (sky = auto-pulled · emerald = you changed it · orange = needs input), `↺ reset`, provenance on hover. Needs override keys per dev field + each value wrapped. Do it AFTER the populate so overrides land on real values.

**RULE THAT GOVERNS THE CARD:** anything the SUMMARY asserts must exist as an inspectable FIELD in Project details — this caught the debt claim with no financing row, and the before-state opening a sentence with no "Previously" field. Details may hold more than the sentence says, never less.

**GOVERNING-JOB + PRECURSOR RULES (settled 2026-07-31, all proven on 22-09 Queens Plaza North — BBL 4004120001, where the operator knew the ground truth: two commercial buildings bought across two lots, demolished, NB filed 2022, stalled).**

⚠⚠ **THE CANDIDATE GATE WAS THE BIGGEST BUG.** devBulk's `OK` regex admitted only `APPROVED|PERMIT|SIGNED|COMPLETE|…` — so a job sitting in **"Objections"** was discarded before the governing-job rule ever saw it, and the signed-off DM governed a live development site. The card then named the DEMOLITION's parties (Errol Vidal / Criterion) instead of the building's (Shibber Khan / Astoria-LIC Development). Citywide, DISAPPROVED outnumbers APPROVED **38,761 to 21,027** — objections are the majority state of pre-development, not a disqualification. Gate now excludes only `WITHDRAWN`; the stall clock decides liveness, not the status string.

**THE BEFORE-STATE ANCHORS AT THE DEMOLITION, and is READ FROM IT.** Anchoring at the governing job's filing read the site *after its own teardown*, so a project that bought and cleared two standing buildings described itself as "previously vacant land" — erasing the acquisition. Two changes: the anchor is the earliest DM precursor's filing date, and the before-state reads the **precursor's own record** — BIS carries `existing_occupancy`/`existingno_of_stories` so a DM knows what it demolished, while DOB NOW has no existing-building fields at all.

**AN INTERVENING ARM'S-LENGTH SALE BREAKS THE PRECURSOR CHAIN** (operator: "the signal is if there was a legitimate sale between the dm and the nb or if it is the same firm — important to not trust an internal transfer either"). **The DEED is the test, never the entity names** — one operator files under many SPEs, which is the ambiguity the party registry exists to resolve. Internal transfers are already excluded because projectDebt only accepts a deed above $10,000 as an acquisition. ⚠ Degrades PERMISSIVELY: no ACRIS walk → no deed → precursor KEPT, because a missing lookup must never silently sever a real chain.

**THERE ARE FOUR STAGES AND "CLEARED SITE" IS NOT ONE** (operator). A lot demolished, filed and stalled before construction is **PRE-DEVELOPMENT**; the teardown is that project's precursor, not a stage. So a signed-off DEMOLITION promotes nothing — sign-off means Operation only for a job that builds (which also fixes the ~19,373 LOC-terminal jobs that could never leave Construction).

**PERMIT FEEDS PULLED** (`ipu4-2q9a` 1,108,522 rows · `rbx6-tga4` 976,803). GC = the **permittee**, resolved for **753,179 jobs** — the PW1 names architect/rep/owner but never the builder. ⚠ `permittee_s_phone__` is ~95% filled on BIS and **DOES NOT EXIST in DOB NOW**, so a pre-2022 job yields a reachable contractor and a current one yields only a name. ⚠ Also fixed: `writeFileSync` was used but never imported, so **every pull crashed after writing all its data and never advanced the cursor** — `delta` had nothing to resume from.

**EACH LENS SHOWS THE DEBT PHASE IT OWNS** (operator): Comparables the acquisition (leverage at trade, beneath the price), Development the construction facility + take-out, Opportunity whoever holds the paper now. No separate "construction lender" contact block — the financing row already names them, and a contact block earns its place only by holding what a line cannot (phone, mailing, other deals); promote it when the party registry can give a lender reach.
