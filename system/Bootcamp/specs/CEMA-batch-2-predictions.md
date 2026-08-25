# CEMA BATCH 2 — PREDICTIONS, RECORDED BEFORE OPENING

Written from specs/CEMA.md as it stands after batch 1 (five members), **before
either document was rendered**. Banked before reading. Score against this file.

## THE DRAW

| # | id | shelf | borough | recorded | rd amount |
|---|---|---|---|---|---|
| 6 | `RC_146262` | CONSOLIDATION AGR | Richmond | 2019-07-11 | $0.00 |
| 7 | `RC_1474230` | CONSOLIDATION AGR | Richmond | 1983-12-01 | $0.00 |

**The axis under test is ERA.** The class currently spans 1970–2009; these are
2019 and 1983, both outside it. ⚠ **COST ACCEPTED: both are Richmond, already
the most-read custodian and already a CEMA member (r13).** Custodian variety is
sacrificed deliberately — the class already spans five custodians, and era is
the dimension with untested ends.

Sealed at draw (type · borough · recorded · rd amount · parties · parcel):
- #6 mortgagors MANGINE MATTHEW and LORI; mortgagees **MERS** and **ENVOY
  MORTGAGE, LTD**; BBL 5070540402.
- #7 mortgagor BLANK DONALD B; mortgagee **CHASE MANHATTAN BANK**; BBL
  5070481013; book 20 page 3979.

⚠ **A METHOD NOTE FROM THE DRAW.** The first era histogram was wrong: the
regex took the first four-digit number in the record and Richmond's `book`
values (18241, 20256) parsed as years 1824 and 2025. It produced recording
dates in 2079 and 2090, which is what exposed it. **The date field is
`recorded`.** A derived number that is obviously impossible is the cheapest
defect to catch; the 1824s would have been believed.

---

## THE STANDING PREDICTION (from specs/CEMA.md §6)

> **surprise falls below 5 on each; the arithmetic fits shape A, B or C without
> a fourth being needed; the holder chain resolves by one of the three known
> mechanisms.**
>
> **If surprise does not fall, the class is not converging and the method is
> not working.**

Batch 1 scored surprise 9 and 7.

---

## PREDICTIONS — #6 · `RC_146262` · 2019 Richmond residential

| # | prediction | basis |
|---|---|---|
| 6.1 | CAPITAL·modifies, `transacts` fires | signature, 5/5 |
| 6.2 | the operative sentence — "constitute in law but one mortgage, a single lien" or close kin — is present | 5/5, 1970–2009; this extends the span to 2019 |
| 6.3 | constituent debts recited with citations | ALWAYS, 5/5 |
| 6.4 | new money is present (a gap mortgage) | residential refinance shape, r13 and b1-4 |
| 6.5 | **arithmetic is SHAPE A** — unpaid balance + new money = consolidated, closing to the penny | r13 and b1-4, both residential |
| 6.6 | restated terms are IN THE FILING — most likely an appended Consolidated Note | b1-4; the field's corrected rule |
| 6.7 | a §255 affidavit is appended | r13, b1-4 — both modern residential |
| 6.8 | tax charged on the new money only | R13-1 |
| 6.9 | VALUE does not fire | 5/5 |
| 6.10 | **the holder chain rides MERS-as-nominee** and needs no assignment instrument | r13; MERS is named as a mortgagee in the sealed rd |
| 6.11 | the consolidated sum exists ONLY in the pdf — rd carries $0.00 | R13-4; rd amount is sealed at $0.00 |

## PREDICTIONS — #7 · `RC_1474230` · 1983 Richmond · Chase Manhattan

| # | prediction | basis |
|---|---|---|
| 7.1 | CAPITAL·modifies, `transacts` fires | signature, 5/5 |
| 7.2 | the operative sentence is present | 5/5 |
| 7.3 | constituents recited in the BODY, not as exhibits | small-document rule (r55, b1-5) |
| 7.4 | **a printed standard form** (NYBTU or similar), not a GSE form | 1983 predates the Fannie/Freddie 3172 material; b1-5's NYBTU 8026 is the nearest kin |
| 7.5 | the arithmetic fits shape A, B or C — **no fourth shape needed** | the standing prediction |
| 7.6 | restated terms are in the filing or named by it | corrected field rule |
| 7.7 | a §255 affidavit is either appended or stamped-and-absent | L-8 both ways |
| 7.8 | tax is $0.00, or charged on new money only | 5/5 |
| 7.9 | VALUE does not fire | 5/5 |
| 7.10 | the holder chain resolves by one of the three known mechanisms — assignment, succession, or probate | the standing prediction |

---

## WHAT WOULD FALSIFY THE METHOD

- Surprise at or above batch 1's level (9, 7) on either member.
- A fourth arithmetic shape.
- A fourth holder-chain mechanism.
- The operative sentence absent, breaking the class's only reliable
  in-document identifier.
