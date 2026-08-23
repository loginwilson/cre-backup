---
name: bkrea-dev-card-grammar
description: "The DEVELOPMENT card's settled design grammar (2026-07-30) — what lives where, status/category vocabulary, formatting rules"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-07-30T21:33:40.544Z
---

The DEVELOPMENT card's settled grammar (operator-iterated 2026-07-30, live in PropertyCard.tsx):
**Name↗ (name IS the look-it-up link) → summary → widgets → category+status chips → PROJECT DETAILS.**
Sentence = TYPE + PEOPLE + MONEY only ("A residential new build designed by Eric Chang at EJC Engineering, PLLC, developed by George Xu at Century Development Group, with no recorded debt" — debt from ACRIS `debt.amount`/`parties.lender`). Widgets = Total SF · Units · Floors. Chips = category + status·date. Details = field blocks (Total/splits sub-rows), contacts as SIX discrete fields (name/company/**real company**/phone/email/mailing — real-company crossing is for the DEVELOPER only; architect/rep file as themselves), staged timeline.

**Why:** each fact appears once, in its register — repetition between summary and chips was the flaw iterated out.

**Vocabulary:** category from the CERTIFICATE chain (final CO → Operation; TCO-only → **Temporary operation**; permitted → Construction; else Pre-development), dated by STAGE ENTRY (first TCO, not later sign-off). Status: **Delivered** = TCO-no-final-CO (operator rejected "Partially complete"); **Complete** = final CO only; **Unassigned** until the stalled-clock filter lands. Timeline: sign-off during TCO lands under Temporary operation; Operation row hollow until final CO ("operation means CO").

**How to apply:** never truncate — wrap whole chips (`flex-wrap` + `whitespace-nowrap`); `tc()` title-case with initialism/suffix guards, `fmtPhone` → (718) 939-1060, emails lowercase. ⚠ NOW cofo feed keys by `job_filing_name` and BIS by `job_number`/`issue_type`/`c_o_issue_date` — wrong names silently fold nothing. See [[bkrea-devbulk]].
