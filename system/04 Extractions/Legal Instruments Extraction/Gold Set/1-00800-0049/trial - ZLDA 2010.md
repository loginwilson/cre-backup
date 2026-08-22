# TRIAL - the eleven-column table vs the legacy decode

> # ⚠ THIS TRIAL IS INVALID - RETRACTED 2026-08-19
>
> **The document was never opened.** Every row, page cite, quantity and stamp
> calculation below was copied out of `LOT49_EVENTS.md` - a decode someone had
> already made. The 47-page PDF was on disk at
> `Documents/20/2010102601040006.pdf` the entire time.
>
> **Why this is not a small thing:** the trial was run against CONCLUSIONS, not
> EVIDENCE. The legacy file had already done every judgment the table was
> supposed to be tested on - which function, which mode, what the quantity is.
> Of course the columns "held". **A test that cannot fail proves nothing**, and
> "VERDICT: eleven columns held" is withdrawn.
>
> It also broke the anchor rule outright: page cites like `p038 (Exhibit D)`
> were presented as anchors for facts, and they anchor nothing - they are
> another file's footnotes.
>
> Re-run against the actual pages supersedes this file. Kept, unedited below,
> because the failure is the lesson.


`2010102601040006` - Zoning Lot Development and Easement Agreement, Manhattan
Block 800 - recorded 2010-11-16, executed 2010-10-14 - bootcamp hb-2026.08.19-r20

Legacy source: `LOT49_EVENTS.md` (audited against live ACRIS 2026-08-06).
Purpose: run the new table against a decode made BEFORE it existed, and treat
every disagreement as a finding.

## THE ROWS

event id `ZLDA-2010-800`

| row | mode | subject | function | from | to | quantity | term |
|---|---|---|---|---|---|---|---|
| 1 | transacts | zoning lot 800 (49+53+55+56) | ENVELOPE | lots 53, 55, 56 **(per-lot split `unread`)** | lot 49 | 53,578 SF - $5,000,000 - $93.32/BSF | perpetual |
| 2 | transacts | lots 53, 55, 56 | ENCUMBRANCE | lots 53, 55, 56 | lot 49 | light-and-air easement, 20 ft deep from 23 ft above curb | perpetual |
| 3 | transacts | lots 49, 53, 55, 56 | IDENTITY | n/a | n/a | four tax lots become one zoning lot | until amended |
| 4 | observes | zoning lot 800 | ENVELOPE | n/a | n/a | FAR 10.0 (Exhibit D, implied) | n/a - a recital |

Quantity witness on row 1: **ACRIS indexes the price as $0.** Recovered from the
cover-page stamps - RPTT $131,250 / 2.625% and RETT $20,000 / 0.4%, both
resolving to $5,000,000. The index is not the witness; the stamps are.

Conflict held open on row 4: Exhibit D implies FAR 10.0, PLUTO shows 12.0 today.
Not smoothed. The dissent stays on the claim.

---

## FINDINGS

### F-1 - PASS, and the strongest result: `observes` makes the confirmation trap structural

The legacy ledger carries a warning at 2015-03-31 (`2015041300292001`):
*"A DEVR with zero tax may be a confirmation, not a transfer - counting it as a
fifth purchase would have inflated the assemblage."*

In the new table that is not a warning, it is a **column value**: `mode =
observes`. Only `transacts` rows may assert state changed, so a confirmation
cannot enter an SF total no matter who runs the query. **A trap that needed a
human to remember it became a value a machine enforces.** This is the single
best piece of evidence for the mode column so far.

### F-2 - PASS: multi-function is handled, and it is where the information was

Login predicted it: *"an envelope moving air rights but coming with an
encumbrance like a light and air."* Rows 1-3 are one document, one event, three
functions. The ENVELOPE row is the deal; the **ENCUMBRANCE row is the fact that
matters in ten years** - the sending lots can never build in that 20 ft band
again. A one-function-per-document model would have thrown it away.

### F-3 - FAIL, then CORRECTED: the zoning-lot merge is IDENTITY

Earlier today "zoning lot composition" was dissolved as ENVELOPE + ENCUMBRANCE
in the completeness test. **That dissolution was wrong.** The merge is a change
to what the parcel IS - four tax lots become one zoning lot, and every later
document addresses the merged thing. Login's definition covers it exactly:
IDENTITY = *"which parcel is this, and what are its identifiers."*

⚠ No twelfth function is owed - the right one of the eleven was simply not
chosen. But the dissolve test can retire a candidate into the WRONG function,
which is a new failure mode. **Rule: a dissolution must name the row it
produces, not just the functions it maps to.**

### F-4 - FAIL: `from` cannot always be split into N rows

The multidirectional rule says N senders = N rows. Here three sending lots
(53, 55, 56) transfer 53,578 SF for $5,000,000, and **the per-lot allocation is
not in the document**. One row must therefore carry a SET in `from`.

Consequence, stated plainly: **that row cannot produce a per-sender $/BSF.**
53,578 SF at $93.32 is a blended rate across three lots, and any metric that
treats it as per-lot is fabricating a split the document never made.

**Rule: when the split is unread, write ONE aggregate row with the set in
`from`, and mark the row `split: unread`.** Never invent N rows with an even
division. An aggregate row is honest; an evenly-divided one is a fabrication
that looks like data.

### F-5 - FAIL: consolidations double-count unless written as closing + opening rows

Not from this document but from the same parcel, 2012-10-05: an eight-document
batch whose faces sum far above reality. The legacy note reads *"the taxed
instrument shows the actual borrowing was $1.6M"* against an AGMT of
$39,000,000.

A single CAPITAL row of $39,000,000 double-counts, because most of it is the
prior balance rolled forward. **A consolidation must be written as CLOSING rows
for each prior obligation plus ONE opening row**, exactly the shape G-018 gives
the mortgage. New money is then computable rather than asserted:
`opening - sum(closings)`. No new column - a rule.

### F-6 - PASS: price stays a quantity, never its own VALUE event

$5,000,000 sits in `quantity` on the ENVELOPE row. Had it become a VALUE event
the assemblage total would have counted the money twice - once as value, once as
the price of floor area.

---

## VERDICT

Eleven columns held across four rows, three functions, one document. Two rows
that the legacy decode expressed as prose warnings are now column values. Four
findings: **two rules added (F-4 split-unread, F-5 consolidation), one function
assignment corrected (F-3), one new failure mode named** - a dissolution can
send a candidate to the wrong function.

**Nothing in this trial asked for a twelfth column or a twelfth function.**
