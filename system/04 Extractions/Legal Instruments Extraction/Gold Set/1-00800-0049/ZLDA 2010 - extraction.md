# EXTRACTION — ZLDA `2010102601040006`
Manhattan Block 800, Lots 49 / 53 / 55 / 56 · bootcamp **hb-2026.08.19-r41**

**Pages read: 1–110 of 110 held. Pages 111–116: `unavailable`.** The cover
declares a 114-page document (116 with covers); ACRIS serves the placeholder md5
from page 111 onward (probed 2026-08-19). **Acquisition is complete; the source
is short.** This reclassifies what the r27 read called an "acquisition gap" —
see Bootcamp D-8 / D-8a.

Supersedes the r27 partial read (pages 1–5) and `trial - ZLDA 2010.md`
(retracted — built from a prior decode, not the document).

## THE INSTRUMENT

| field | value | anchor |
|---|---|---|
| instrument | ZONING LOT DEVELOPMENT AND EASEMENT AGREEMENT | p4 |
| indexed type | DEVELOPMENT RIGHTS | p1 |
| **signed** | 2009-12-11 — acknowledgment, both parties, same notary | p27 |
| **effective** | 2010-10-14 — "made **as of** the 14th day of October" | p4, p1 |
| prepared | 2010-11-11 | p1 |
| recorded | 2010-11-16 15:35 · CRFN 2010000384312 | p1 |
| declared pages | 114 (+2 covers = 116) · **110 served** | p1 |
| cross-refs | 2010102601040002 / ...003 / ...004 / ...005 | p1, p2 |
| title no. | 071292A, Commonwealth Land Title, certified 2010-10-14 | p35 |

⚠ **`signed` and `effective` are 307 days apart** and are different facts. The
r27 read recorded only the dateline. The dateline says *made **as of***, which
is an effective date the parties chose; the acknowledgment is when signatures
were taken. ACRIS `document_date` = 2010-10-14 = the effective date, which is
**defensible, not wrong** (Bootcamp D-3).

## PARTIES — as the INSTRUMENT states them

| party | role | holds | principal | anchor |
|---|---|---|---|---|
| 120-22 W 25 STREET LLC ("120 Owner"), NY LLC | sender | Lot 53 — 120-22 W 25th St | **Alfred Sabetfard**, Managing Member · c/o **The Sabet Group**, 38 W 31st St Ste 3 | p4, p23, p26 |
| 124-26 W 25 STREET LLC ("124-126 Owner"), NY LLC | sender | Lot 55 (124 W 25th) **and** Lot 56 (126 W 25th) | **Alfred Sabetfard**, Managing Member · same office | p4, p23, p26 |
| 112-118 WEST 25TH LLC ("Developer"), **Delaware** LLC | receiver | Lot 49 — 112-18 W 25th St, a through-lot to 113-17 W 24th | **Dov Hertz**, Vice President · c/o **Extell Development Company**, 805 Third Ave 7th Fl | p4, p24, p26, p34 |

**Two sending ENTITIES, three sending LOTS**, both entities signed by the same
natural person before the same notary on the same day — common control, stated
on the face of the record.

⚠ **NEITHER PRINCIPAL NOR SPONSOR APPEARS IN THE ACRIS PARTY INDEX.** The index
carries three LLC shells. The notices block (§XX, pp23–24) and the signature
page (p26) are what connect them (Bootcamp D-4).

## CONFLICTS — the index disagrees with the instrument, TWICE

ACRIS's cover states: *"The information on this page will control for indexing
purposes in the event of any conflict with the rest of the document."* Both
errors are therefore IN the index.

| field | cover page (indexed) | instrument | anchor |
|---|---|---|---|
| sender entity name | 124-**25** W 25 STREET LLC | 124-**26** W 25 STREET LLC | p2 vs p4, p26 |
| Sabet Group address | **28** West 31st Street | **38** West 31st Street | p1, p2 vs p4, p23 |

An entity-spine join on the indexed name searches for a company that does not
exist. Held open, not corrected silently.

## THE EVENT ROWS

event id `ZLDA-2010-800`

| mode | subject | function | effect | from | to | quantity | term |
|---|---|---|---|---|---|---|---|
| transacts | zoning lot: Block 800 lots 49, 53, 55, 56 | IDENTITY | creates | n/a | n/a | four tax lots combined into ONE zoning lot under ZR 12-10, by Declaration of Zoning Lot Restrictions of even date | until subdivided per §IX (p17) |
| transacts | lots 53, 55, 56 → lot 49 | ENVELOPE | **transfers** | 120-22 W 25 STREET LLC · 124-26 W 25 STREET LLC | 112-118 WEST 25TH LLC | **53,578 zsf** for **$5,000,000** = **$93.32/bsf** | perpetual — runs with the land (§XV, p22) |
| transacts | lot 53 | ENCUMBRANCE | creates | 120-22 W 25 STREET LLC | 112-118 WEST 25TH LLC | light-and-air easement over the 120 Owner Parcel — granted by 120 Owner **alone** (§II.A.2) | perpetual — runs with the land (§XV, p22) |
| transacts | lot 53 | ENCUMBRANCE | creates | 120-22 W 25 STREET LLC | 112-118 WEST 25TH LLC | **Construction Easement** — foundation and building supports, shoring, bracing, underpinning, construction fence, protective sheds and bridges (§XIII.A.2, p19) | during initial construction and any Alteration or Rebuilding (p19) |
| transacts | lots 53, 55, 56 | ENCUMBRANCE | creates | 120-22 W 25 STREET LLC · 124-26 W 25 STREET LLC | 112-118 WEST 25TH LLC | covenant not to use the transferred rights or create a Violation; advance consent to future mergers, enlargements and subdivisions (§VIII, §IX) | perpetual — binds successors and every future "party in interest" (§XV, p22) |

⚠ **`effect` BACK-FILLED 2026-08-19 under r43.** These rows were written before
`effect` existed and are re-judged here, per the standing rule that a new trap
is re-run over every earlier entry. All five resolve cleanly and none changes
meaning — the ZLDA creates and transfers, it releases nothing. **That is why
this document could not have found the gap: a corpus of grants never needs a
word for ending.**

⚠ The r27 read withheld the ENCUMBRANCE rows as `not attempted`. They are now
written because §II.A.2, §XIII.A.2 and §XV were read. **Their `term` is not in
any granting clause** — it is in §XV BINDING EFFECT, eleven pages away
(Bootcamp D-7).

### Quantities as the document gives them — Exhibit D (p38)

|  | Developer | 120 Owner | 124 Land | 126 Land | TOTAL |
|---|---|---|---|---|---|
| Lot area (sf) | 15,639 | 4,077 | 2,469 | 2,469 | 24,654 |
| DR generated | 156,390 | 40,770 | 24,690 | 24,690 | 246,540 |
| Retained | n/a | 16,906 | 9,620 | 10,046 | 36,572 |
| **Excess (moved)** | n/a | **23,864** | **15,070** | **14,644** | **53,578** |
| After transfer | 209,968 | 16,906 | 9,620 | 10,046 | 246,540 |
| Pro rata | 85.17% | 6.86% | 3.90% | 4.07% | 100% |

`246,540 / 24,654 = FAR 10.0` exactly. `156,390 + 53,578 = 209,968`. The table
closes in both directions.

⚠ **This closes the r27 finding that "the floor area is not a number in this
instrument."** That was true of the recitals, which define the quantity by
formula (p5) — and false of the document, which tabulates it at p38. The
denominator here is **recited, not derived**. The structural warning still
stands for ZLDAs that carry no Exhibit D.

### The consideration — two witnesses, cover page (p1)

    NYC Real Property Transfer Tax   $131,250.00  @ 2.625%  ->  $5,000,000
    NYS Real Estate Transfer Tax     $ 20,000.00  @ 0.400%  ->  $5,000,000

Mortgage Amount $0.00 and every mortgage-tax line $0.00. The ACRIS index carries
`document_amt = 0`, as it does for every DEVR. **The stamps are the only
witness, and there are two of them.**

### $/SF — measured at the deal, derived at the lot

| level | value | status |
|---|---|---|
| whole transfer | **$93.32 / bsf** (5,000,000 ÷ 53,578) | **measured** |
| lot 53 (120) | $2,227,033 · 23,864 sf | **derived** — pro rata |
| lot 55 (124) | $1,406,361 · 15,070 sf | **derived** |
| lot 56 (126) | $1,366,606 · 14,644 sf | **derived** |

⚠ The stamps rate ONE consideration. Exhibit D splits the SF and never the
money, and two of the three selling lots share an owner and a signature, so the
parties had no reason to split it precisely. **The derived per-lot prices must
never price a comparable** (Bootcamp D-2).

## CLAIMS (not events)

- Owner reimburses Developer up to **$10,000** for §VIII instruments (p17)
- Developer pays Owner's **Reimbursable Expenses**, uncapped (§XIII.C, p21)
- Developer carries **$5M/occurrence · $10M aggregate** GL, naming 120 Owner and
  120 Owner's lender as additional insureds (§XIII.D, pp21–22)
- Parking-lane closure consented by letter, Exhibit E (§XIII.A.6, p21)
- Liability limited to each party's interest in the Combined Zoning Lot (§XVIII, p23)

These attach as CONDITIONS to rows that already exist. None has a determinable
quantity *and* a date, so none becomes a COST row.

## PRODUCED NOTHING

§XVI–§XXVII (pp22–25) — remedies, limitation of liability, lien law, notices
mechanics, non-waiver, headings, pronouns, counterparts. §XIII.A.3–5 (pp19–21)
— engineer selection, objection notices, independent-engineer arbitration.
Real obligations, no implication for any of the eleven functions.

## THE SIBLINGS — one transaction, five recorded instruments

All four cross-referenced ids are held, all recorded 2010-11-16 15:35. CRFNs
verified on the two covers read: `...003` = 2010000384309, `...006` =
2010000384312 — consecutive within the package; the other three CRFNs were not
opened.

| id | type | ACRIS description | class | pages declared / held | RPTT / RETT |
|---|---|---|---|---|---|
| ...002 | CERT | CERTIFICATE | OTHER DOCUMENTS | — / 8 | — |
| ...003 | SAGE | SUNDRY AGREEMENT | OTHER DOCUMENTS | 16 (+2) / **18 ✓** | **$0.00 / $0.00** |
| ...004 | SAGE | SUNDRY AGREEMENT | OTHER DOCUMENTS | — / 9 | — |
| ...005 | SAGE | SUNDRY AGREEMENT | OTHER DOCUMENTS | — / 8 | — |
| **...006** | **DEVR** | DEVELOPMENT RIGHTS | **DEEDS AND OTHER CONVEYANCES** | 114 (+2) / **110 ⚠** | **$131,250 / $20,000** |

Three findings:

1. **The $5,000,000 sits on the DEVR alone.** ...003 carries $0.00 on both
   transfer-tax lines. The consideration is not split across the package.
2. **The shortfall is specific to ...006, not systemic** — ...003 declares 18
   and serves 18.
3. ⚠ **Only the DEVR carries DIRECTION.** Per `_doctype_codes.json`, `SAGE` and
   `CERT` sit in class `OTHER DOCUMENTS` with party roles `PARTY 1` / `PARTY 2`
   — **role-blind by construction**. Only `DEVR` is class `DEEDS AND OTHER
   CONVEYANCES` with `PARTY ONE` / `PARTY TWO`. Four of the five instruments
   cannot say who gave and who received. **The cross-reference block is what
   makes them one event, and the DEVR is the only member that orients it.**

## UNRESOLVED

| what | why | what would settle it |
|---|---|---|
| Exhibit F — Form of Light and Air Easement | **`unavailable`** — inside the 6 pages ACRIS does not serve | sibling instruments `...002`–`...005`, or the paper record |
| Bonus Development Rights | Exhibit D is expressly *"Excluding Bonus Development Rights"* (p38 footnote); the 59.4 / 40.6 share is stated outside this table | read the sibling declaration |

## STATE

`complete for what the source holds` — 5 events written, 2 index conflicts held
open, 3 questions named with what would settle each, 6 pages `unavailable`.
No claim above depends on an unavailable page.
