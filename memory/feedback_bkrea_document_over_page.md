---
name: feedback-bkrea-document-over-page
description: "THE recurring failure — read the DOCUMENT not the summary page, and never cap how many documents or pages you read"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-08-04T11:25:21.447Z
---

**DOCUMENTS OVER APPLICATION DETAILS. Never cap the read.** Operator, repeatedly, most bluntly on
2026-08-04: *"how many times do i have to say dont use the application details page. use the document"*
and *"you have the tendency to limit yourself with capping the number of pw1's and pages in the pw1's
so you either dont read enough to find the contact or you dont read the right section."*

**Why:** the BIS Application Details page renders §1–§24 and then throws a NullPointerException, so
§26 (property owner — the DEVELOPER's phone, e-mail and mailing address) is never reached. The page
gives a name; the PDF gives the contact. Measured cost of getting this wrong: developer phone sat at
**48%** while architect (§2, on the page) was 100%. Reading the PDF took it to **95%**. Separately,
`maxReads: 6` against a folder of 49 PW1s returned "no owner exists" on a job whose owner was
readable on the 9th document.

**How to apply:**
- Any reader that has a summary/details page and an underlying document: open the DOCUMENT. The page
  is only for finding *which* document.
- Caps are safety rails for a hand-run measurement, never for a pull. Default to reading the whole
  candidate list; if a cap is unavoidable, print what was skipped — a silent cap reads as "covered".
- Read every PAGE, not the last one: §26 is not reliably on the final page (job 440819795 ends at
  §25), so anchor on the section's own labels.
- **The falsifiable rule the operator gave, which makes every gap checkable:** an accepted PW1 must
  carry complete contacts for all parties. So any role short of ~100% means *the document was not
  opened* — it is a reader bug, not an absent record. Test it site by site with [[project-bkrea-reach-ladder-roles]].
