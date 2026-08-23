---
name: project_acris_doctype_decode_rules
description: "Per-document-type decode rules with their traps — the $10 recital, the quantity that lives in an exhibit not the grant, and consideration recoverable from cover-page tax stamps when the index says zero"
metadata: 
  node_type: memory
  type: project
  originSessionId: 176544e8-656c-4540-a15c-f710beced15e
  modified: 2026-08-15T00:20:15.423Z
---

The goal (Login, 2026-08-06): **"lot 1 transferred blank sf to lot 2 through a
zlda for blank amount resulting in $/sf"** — every document type reduced to a
plain-English takeaway via *pullable rules*, because the key facts differ by
type but the method of finding them can be written down.

Code: `decoder/doctype_rules.py` (rules) · `decoder/facts.py` (citation-grade
fact rows) · `decoder/consideration.py` (price from tax stamps).

**Learned decoding 2010102601040006 — a 116-page ZLDA, MN Block 800 Lots
49/53/55/56, recorded 2010-11-16, CRFN 2010000384312.**

**⚠ TRAP 1 — THE $10 RECITAL.** The body reads *"in consideration of Ten Dollars
($10.00) and other good and valuable consideration"*. The real price was
**$5,000,000**. Reading the recital is wrong by 500,000× **and looks like a real
number**. NEVER take consideration from the recital.

**⚠⚠ CORRECTED 2026-08-06 — "the index says 0 for EVERY DEVR" IS FALSE.**
Measured citywide: of 1,201 DEVR, **605 (50.4%) are zero and 596 (49.6%) carry an
amount.** I generalised from ONE document (2010102601040006) to the whole
population and wrote it as a law. Found when lot 1008000049's own DEVRs
—2012122701550003 at $4,614,690 and 2013052101674004 at $1,450,000— contradicted
my own rule on the same parcel I had been reading all day.
**Practical effect is the good direction: ~596 DEVRs can be priced from the free
index; only ~605 need the tax-stamp derivation.** But ALWAYS check which case you
are in — never assume zero, and never assume the index figure is absent.
**The general lesson: n=1 is not a rate.** Any claim of the form "always" or
"every" that came from a single document is a hypothesis wearing a law's clothes.

**★ WHERE THE INDEX IS SILENT, THE PRICE IS STILL ON THE COVER PAGE.** For the
605 zero-amount DEVRs: But the cover-page tax stamps are
two independent witnesses: NYC RPTT $131,250 ÷ 2.625% = $5,000,000 AND NYS RETT
$20,000 ÷ 0.400% = $5,000,000. **Exactly agreeing.** One stamp alone is
ambiguous ($131,250 is also 1.425% of ~$9.2M), so `consideration.py` returns
*confirmed / single / ambiguous / CONFLICT* and never reconciles a conflict by
picking a side. **This is the concrete answer to "why bother with images": the
index is not wrong, it is SILENT on the number that matters.**

**⚠ TRAP 2 — THE QUANTITY IS NOT IN THE GRANT.** The granting clause says *"Owner
hereby conveys to Developer the Subject Development Rights"* — no number. It is
a defined term: *"as shown on **Exhibit D**"*. The SF lives in an exhibit tens of
pages later. A decoder stopping at the grant records a transfer with no quantity
**and does not know it is missing one**.

**★ RESOLVED 2026-08-06 — THE QUANTITY IS IN THE *AIR RIGHTS SURVEY*.** Chasing
"Exhibit D" was chasing the wrong tab. The 116-page recording is a **bundle of
three instruments**, each with its own control number and its own exhibit series:
a Purchase & Sale Agreement (1809348.1), a Declaration of Zoning Lot Restrictions
(KL3 2641879.1), and the ZLDA (KL3 2754660.2). The PSA's exhibit list reads
**A Seller's Land · B Purchaser's Land · C AIR RIGHTS SURVEY · D Declaration ·
E ZLDA · F–I forms** — so "Exhibit D" is the *Declaration*, and the square
footage lives in **EXHIBIT C**, a sealed survey (Earl B. Lovell–S.P. Belcher,
surveyed 2007-08-16, Thomas Piciocco lic. 049688-1).

**GENERAL RULE: in a rights transfer, floor area comes from the SEALED SURVEY,
not from any agreement clause.** Seller parcel MN Blk 800 lots 53/55/56 =
**9,015 sf lot area, 36,572 sf existing floor area** (per-floor schedule; every
stated total equals the sum of its floors — the survey self-checks). At the
PLUTO-current 12.0 FAR that implies ≤71,608 sf unused → **≥$69.82/sf**, a FLOOR
on price-per-sf because "all unused transferred" is a CEILING on square feet.
⚠ FAR read from PLUTO 2026 for a 2010 transfer — unverified.

**⚠ TRAP 4 — TYPED EXHIBIT LISTS UNDER-REPORT.** The Declaration's typed list
says A, B, C; handwritten tabs run to E. And **Exhibit B of the Declaration is
BLANK** — the metes-and-bounds header with no description beneath it, a recorded
defect visible only in the image.

**BUG #9 (metes parser), found in a real Exhibit B:** "about 82 feet 8 3/4
inches" → 82.0, dropping 8.75in. The HYPHENATED form (`4-3/8`) and the BARE
fraction (`1/2`) each had an earlier fix; the **SPACE-separated mixed number fell
in the gap between them**. Caught because closure error (0.667 ft) matched the
dropped inches — **CLOSURE IS A PARSER TEST**. After fix: 0.062 ft. 51/51
assertions; backfill over 20 stored descriptions found 0 affected.

---

**★ DEED — TESTED 2026-08-06: THE INDEX PRICE IS TRUTHFUL, SO IT COSTS NOTHING.**
Deed 2009122400274001, index `document_amt` $5,242,000. Predicted RPTT
$137,602.50 (2.625%) and RETT $20,968.00 (0.400%) *before* fetching; the cover
page showed **both to the cent**. So for DEEDs the index is the answer —
**the exact opposite of DEVR**, where document_amt is 0 and the price exists only
on the image.
Citywide: DEED 3,640,429 — microfilm `FT_` 1,367,900 of which **100.0% carry
amt=0** (image is the ONLY source for the whole pre-2000 sales record); modern
2,272,529 with 59.0% at zero. **932,424 deeds priced with zero requests.**
Also: an out-of-state grantor address is a long-hold signal (this one sold from
Hurst, Texas to an SPE formed eight days earlier).

**★ MTGE — index also truthful, and the ERA ASYMMETRY IS THE OPPOSITE OF DEED.**
Mortgage 2020081400407001: cover page `Mortgage Amount` $5,000,000.00 = index
`document_amt` exactly. Citywide MTGE 4,216,266 — microfilm amt=0 only **3.3%**
vs **100%** for microfilm deeds. Likely because mortgage recording tax is
computed on the mortgage amount so it had to be captured to collect the tax,
while deed consideration never made the index migration. **⇒ the pre-2000
FINANCING record is free; the pre-2000 SALES record is not.** 3,610,056
mortgages (85.6%) priced with no image.

**⚠ THE CEMA TRAP (open question, not yet resolved).** The cover page carries
BOTH `Mortgage Amount` and `Taxable Mortgage Amount`. Equal on this document,
but a Consolidation/Extension/Modification pays tax only on NEW money so taxable
falls far below face. **Which one `document_amt` reports is UNTESTED** — on a
CEMA that is "borrowed $50M" vs "borrowed $5M and rolled $45M". `consideration.
check_mortgage()` flags it; decode a real CEMA to settle it.

**⚠ MRT RATES — I GOT THEM WRONG FROM MEMORY.** Predicted City Additional at
1.25% and **omitted NYCTA entirely**, giving 2.30%, while having written "2.80%"
one step earlier and never checking components against my own total. Measured
(commercial >$500k): basic 0.500 · city additional **1.125** · spec additional
0.250 · TASF 0 · MTA 0.300 · **NYCTA 0.625** · addl 0 = **2.800%**. Now in
`consideration.MRT_COMMERCIAL_OVER_500K`, transcribed not recalled.

---

**★ SAT + ASST — 4,834,531 docs (28.4% of ACRIS), ALL DECODABLE WITH NO IMAGES.**
**100% of both types carry document_amt = 0.** They hold no money — a SAT
discharges some other document, an ASST moves it to a new lender. So the only
question is WHICH ONE, and that is pure linkage. `decoder/chain.py`.

**The references table `pwkr-dpni` (8,677,012 rows, free) is the answer**, and it
has the SAME ERA SPLIT as dates and amounts:
  * `reference_by_crfn_` — modern — **resolves 100%** (746/747 on Block 800)
  * `reference_by_reel_year/borough/nbr/page` — microfilm — **resolves 80%**
  A decoder reading only the CRFN column silently drops every pre-electronic
  link — 487 of 1,567 references on one block, **31%**.

**★ THE CHAIN IS MULTI-HOP.** A SAT/ASST does NOT reliably point at a MTGE. The
747 modern references resolved to MTGE 545, **AGMT 112, ASST 64**, M&CON 9. An
assignment assigned onward points at the PRIOR ASSIGNMENT. `root_of()` walks
transitively with cycle/depth/ambiguity verdicts; stopping at one hop reports the
wrong lender and the wrong date.

**★ ZERO SATISFACTIONS IS A CEMA SIGNATURE.** Lot 1008000049: 11 MTGE, **15 ASST,
0 SAT**. I suspected a bug in my own discharge logic; the code was right and the
suspicion was wrong. Debt assigned repeatedly and never discharged = consolidation
(CEMA) refinancing, done to avoid paying mortgage recording tax twice.
**AND THE CEMAs ARE FILED AS `AGMT`, NOT `M&CON`** — lot 49 has zero M&CON and 11
AGMT, and the assignments resolve to those AGMTs. That is a large part of why
AGMT is 920,875 documents. One mortgage (FT_1980000345898) is carried forward by
four separate assignments spanning 2007–2023.
Connects to the open CEMA question under MTGE above.

---

**★★ AGMT — 920,875 docs, the largest catch-all, and MAJORITY FINANCIAL.**
**58.4% carry a dollar amount** (537,677). The amount is the CLASSIFIER: with one
it is a financing instrument, without one it could be a ZLDA or an easement
agreement. Median $1,000,000; max seen **$410,000,000**. 320 AGMTs on one
Manhattan block are *pointed at* by other documents — they sit in reference
chains. (AL&R, pointed at 342 times, is the same financing family.)

**⚠⚠ THE BIGGEST MONEY TRAP IN THE PROJECT — TWO ERRORS THAT COMPOUND.**
Verified on 2014040900899002 (2014-04-04, 212 Fifth Ave / Deutsche Bank):

1. **FACE ≠ NEW MONEY.** Cover page: `Mortgage Amount $410,000,000.00`,
   **`Taxable Mortgage Amount $0.00`, `Exemption 255`, every tax $0.00.** It is a
   consolidation/spreader — tax was already paid on the underlying loan, so **no
   new money moved.** `document_amt` reports FACE, never new money. Read TAXABLE.
2. **THE SAME AMOUNT APPEARS ON EVERY PARCEL.** That one instrument touches
   **THIRTEEN parcels across five blocks**, each showing $410,000,000. A naive
   parcel-level sum reports **$5,330,000,000** of debt where the truth is **$0**.
   **NEVER aggregate document_amt across parcels without de-duplicating by
   document_id first.**

This is the definitive answer to the CEMA question left open under MTGE, and it
matters far beyond M&CON because **CEMAs are filed as AGMT** — lot 1008000049 has
zero M&CON and eleven AGMT, and its assignments resolve into them.

---

**★★ THE CEMA PAIR — both halves proven on one parcel, one day (lot 1008000049,
2023-10-16). This is the worked example to reason from.**

| instrument | face | tax paid | what it IS |
|---|---|---|---|
| DEED ...486001 | $0 | — | entity reorg (LAM GEN 25 → CHELSEA 25 HOTEL, **same address both sides**) |
| MTGE ...486009 | $25,490,000 | **$713,720** | taxable IN FULL = **the new money** |
| AGMT ...486010 | $120,000,000 | $0, **exemption 255** | consolidation, **no new money** |

**Naive index read: "$145,490,000 borrowed." Truth: $25,490,000 new, consolidated
to a $120,000,000 position.** The AGMT cross-references **MANHATTAN Year 1990
Reel 1707 Page 1285** — 33 years of CEMAs, which is why this lot has 15 ASST and
0 SAT. ⇒ **the reel/page reference form is NOT legacy; 2023 instruments still
point into it.**

**MRT TABLE INDEPENDENTLY VALIDATED.** `consideration.MRT_COMMERCIAL_OVER_500K`,
measured off a $5M 2020 mortgage, reproduces the $25.49M 2023 mortgage's tax to
the cent on **all seven components** (2.800%). Not curve-fitted.

**⚠ AND THE §255-a AFFIDAVIT CONTRADICTS THE INDEX.** Reading all 38 pages of
MTGE 2020081400407001 (I had read only page 1 and called it decoded): **page 37**
is the §255-a affidavit with box 1 checked — *"not more than six residential
dwelling units"* — while the cover page says COMMERCIAL REAL ESTATE and PLUTO
says building class **H2, a 40-storey hotel with `unitsres = 0`**. "Not more than
six" is literally satisfied by zero, so it is defensible, but a reader takes it
for a small residential building. **Page 37 also yields the signer — Jeffrey Lam,
Manager — a contact-ladder rung obtained with no DOS lookup at all.**

**⚠ TRAP 3 — SHARES HIDE IN DEFINITIONS.** *"Developer's Owner Parcel Bonus
Development Rights shall mean 59.4% of any Owner Parcel Bonus Development
Rights"* — a materially important percentage sitting in a definitions list, in no
operative clause.

**Also:** cover-page PROPERTY DATA shows only the first two lots with the rest
behind *"Additional Properties on Continuation Page"* (the legals index DID have
all four — checked, no discrepancy). Document Date (signed) vs Recorded/Filed
(public) are two dates and must never be conflated.

---

**★★ THE COVER PAGE IS THE DENSEST FIELD SOURCE IN ACRIS — `decoder/cover_read.py`
(built 2026-08-14). It reads at ~11,000 pg/hr and grades itself.** Found by
`decoder/completeness.py`, which MASKS every character any owned pattern claims
and ranks what survives by document frequency — the only audit that can surface a
field nobody modelled. Coverage metrics are structurally blind to those.

On 25 DEVR covers: both BBLs 21/25 · any BBL 25/25 · party one+two 25/25 ·
presenter/return-to 24/25 · doc type + both dates 25/25 · own CRFN 19/25 ·
stamp 9/25. Grades: printed Document ID == directory name **25/25**; page count +
cover == pages on disk 23/25.

**⚠ FOUR BINDING TRAPS, ALL MEASURED, ALL SILENT:**
1. **`Real Property Transfer Tax` MATCHES INSIDE `…Transfer Tax Filing Fee`** —
   binds the **$25 filing fee** as the tax. $25/2.625% = a $952 "sale". The old
   `cover_fields.py` reported 33/150 stamps bound this way.
2. **A VALUE MUST BE AT OR BELOW ITS LABEL, NEVER ABOVE.** The filing-fee figure
   sits ~36px above the RETT label; allowing `dy >= -h` made RETT reach up and
   grab it — three false stamps that looked like successful binds.
3. **OCR EATS THE DECIMAL POINT: `6,26200`.** Requiring `\.\d\d` lost 3 of the 8
   non-zero DEVR stamps. Repair is legitimate ONLY when the comma survives (a
   comma group is 3 digits, so 5 following digits put the point back
   deterministically). Bare `626200` is UNRECOVERABLE — never guess it.
4. **PARTY ONE / PARTY TWO / PRESENTER / RETURN TO ARE COLUMN HEADS.**
   Linearised, the page reads `PARTY ONE: PARTYTWO: 691EIGHTHAVENUE…` — both
   labels before either name, so `PARTY ONE:(.*?)PARTY TWO` captures **empty**.
   Flat 1/25 → spatial 25/25. Column split = the widest x-gutter, MEASURED per
   band; the midpoint of the two labels cuts through the left column's own text.

**★ party_type CONVENTION CONFIRMED** (the one defect transcription scoring
cannot see): cover PARTY ONE == index `party_type` 1 on **13/13 testable, 0
inverted** (636b-3b5g).

**⚠ TESSERACT BEATS PADDLEOCR ON THE COVER, AND THEY FAIL ON DIFFERENT
CHARACTERS.** Document ID off Paddle's flat text 18/25 vs Tesseract word boxes
25/25; but Tesseract dropped the comma in `626200` where Paddle kept `6,26200`.
Two channels, same argument as the body text — consult the second only when the
first yields no parseable token, never to override it.

**⚠⚠ THE COVER PAGE UNDER-REPORTS PARCELS BY 35% AND WARNS ON LESS THAN HALF.**
Measured 2026-08-14: 71 parcels in the LEGALS index (`8h5j-fqxa`) against 46 read
off 25 covers. The page was short on **13 of 25** documents but printed
"Additional Properties on Continuation Page" on only **5** of them. ⇒ **legals is
the parcel POPULATION; the cover page is the better PROVENANCE** (it has a span
into a page a human can look at). Use both, record which.

**★ PARCEL SIDES — `decoder/parcel_sides.py`. Nothing states which lot sends and
which receives.** The cover lists both and never says; PARTIES gives each PARTY a
side and never mentions a lot. Answered by WITNESSES, never by one:
  * **ownership** (primary) — the prior DEED's grantee (`party_type` 2) on the
    document date; the owning party's side transfers to the lot. 25/31 resolved.
  * **address** — lot street address vs party name, because these are SPEs named
    after their buildings ("691 EIGHTH AVENUE CORPORATION" owns 691 8 AVENUE).
    Only 6/76 parties — corroborates, cannot lead. Co-fired with ownership 3×,
    agreed 3/3.
  * **air_rights='Y'** in legals — a hint at the sending side; 3/25 docs, and on
    735009 it marks 4 of 5 lots, so never decisive alone.
Result 31/71 parcels sided, **0 conflicts**, 5/25 documents balanceable.
**⚠ Body role words are useless on DEVR** ("granting/sending/receiving parcel"
fired on 1 of 6 documents) — the ZLDA defines its parties in a DEFINITIONS
section instead.
**⚠ THE BLOCKER IS ENTITY AMBIGUITY, NOT MISSING DATA:** 20 ambiguous vs 20
unresolved. Ambiguous = a witness fired and both parties matched ("31 COOPER
INC." vs "29-31 COOPER SQUARE ASSOCIATES LLC" share {31, COOPER}). Those need
better entity resolution; unresolved needs another witness. **Never collapse the
two — they have opposite fixes.**

**⚠⚠ doc_type IS WHAT THE PRESENTER FILED IT AS, NOT WHAT THE INSTRUMENT IS.**
Measured 2026-08-14 (`decoder/exhibit_read.py`): **12 of 25 documents filed as
`DEC OF DEVELOPMENT RIGHTS` are actually `PARTY WALL DECLARATION OF
RESTRICTIONS`** — party-wall agreements between adjoining townhouses. No right
moves, so no square footage exists, so "no quantity" was the CORRECT refusal and
the extractor was missing nothing. Read the instrument's own title off its first
body page and carry `filed_as` vs `is_a` separately; every statistic keyed on
doc_type inherits the filing error silently. ⇒ of the 25-document sample only
**13 are genuine DEVRs** (12/13 establish, 5/13 conservable, 1 real gap).
**The lesson generalises: before building an extractor for a field that is
missing, check the document is the type you think it is.**

**⚠ "the word EXHIBIT appears on this page" IS NOT AN EXHIBIT** — it counts
"as shown on Exhibit D" inside a recital. Anchor the label to the HEAD of the
page and carry it forward (continuations have no header): real exhibit blocks
23/25 vs lexicon's 13/25. And `square\s+feet` misses `8248squarefeet` — OCR
removes the space inside the unit too, not just around it.

**★ ESTABLISHED ≠ CONSERVABLE.** An event is ESTABLISHED when it names what
changed, for whom, in which direction (parties carry the sign). It is
CONSERVABLE only when PARCEL sides are known, because "SF leaving == SF
arriving" is a test on lots. Collapsing them made all 25 documents refuse.

**Fact-row schema** (`facts.py`): every fact REFUSES to exist without
`document_id` + `page`. Typed `predicate` vocabulary (not prose) so a lifecycle
is assembled by filtering. `confidence` = read | derived | inferred, and a
*derived* value must record its derivation or it is indistinguishable from one
read off the page. `parser` version stamped so "re-decode everything read by
parser < N" is a query.

**Store-vs-delete, settled:** the IMAGE is replaceable (re-fetchable by doc id +
page — which is what the citation encodes); the FACT is not. Citations are the
durable asset; stored images are a *cache* worth keeping because they make parser
fixes retroactive (~$400 for the whole corpus).

Related: [[project_acris_document_inventory]], [[project_acris_decoder]],
[[feedback_bkrea_document_over_page]], [[project_bkrea_comparable_property]].
