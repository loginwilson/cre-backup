# Function register — what each resolver settles

A resolver takes claims from many documents and settles them into one coherent
answer for its function. What makes it a resolver and not a collector is the
**conflict it has to adjudicate**.

★ **Each entry declares what it DEPENDS ON.** Resolvers are a DAG. A resolver
may read another resolver's *output* where declared here — never its internals,
never a document.

★ **Resolvers output timelines, not scalars.** TITLE is not "the owner" — it is the
ownership chain, from which a deriver asks "owner as of date X". Same for ENVELOPE,
CAPITAL, OCCUPY, ASBUILT. Derivers collapse a timeline to a point; resolvers must
never do that collapse themselves.

---

## SPINE

### IDENTIFY — which parcel is this, over time
**Settles:** a dated identity chain. BBL ↔ BIN ↔ zoning lot ↔ condo unit/billing
lot, and the lineage graph: what this lot was made from, what it became, when.
**Adjudicates:** lineage breaks. A job filed 2014 keys to a lot that no longer
exists (280 Kent, lot 1 → lot 3, reapportioned 7/17). Tax lot ≠ zoning lot; zoning
lot composition is itself declared in ACRIS (ZR 12-10 statements,
CRFN 2014000427044/427045 on that same parcel).
⚠ Must run first. Every other function loses records at a lineage boundary and the
loss is invisible because filters return clean-looking output.

### PARTY — who the humans and entities are
**Settles:** one id per real person/company, with aliases, the entities they sign
for, the real company behind the SPE, and contact.
**Adjudicates:** identity. `DONNAMLLER` vs `donnamiller` on the same form. Two Hale
Everets, one a managing director and one an NCAA hockey player. `DOMINO A PARTNERS
LLC` and Two Trees as the same interest.
⚠ People-primary, entities as edges — person matches 24.5%, entity 5.1% on the
2021+ cohort. Anchor on the email domain: it is the only field that unmasks the SPE.

---

## RECORD FUNCTIONS

### TITLE — who holds an interest, and in what priority
**Settles:** the ownership chain over time — grantor/grantee, interest type,
priority, current holder, tenure.
**Adjudicates:** arm's-length vs internal transfer. The 2026 Two Trees deed is
Two Trees → Two Trees with no mortgage; it changes nothing about who owns it, but
its `c/o` line is what identifies the real company. Exclude as an ownership event,
read for the c/o and the signature.

### ENCUMBER — what restricts this land regardless of who owns it
**Depends on:** IDENTIFY · PARTY
**Settles:** active encumbrances at a date — easements, restrictive declarations,
ZLDAs, development rights transferred OUT, deed restrictions. Binding vs released.
**Adjudicates:** dangling references. A dev-rights table citing a prior ZLDA
without a number is a claim of a *reference*, not an absence. Resolve across the
whole function; a later document often names what an earlier one implied.
⚠ This is the function that makes remaining-rights true or false.

### ENVELOPE — what may be built here as of right
**Depends on:** ENCUMBER (rights transferred in/out) · PARCEL (lot area)
⚠ **This is the dependency that makes the resolver set a DAG.** Buildable area is
`zoning FAR × lot area + rights in − rights out`, and transferred rights are
ENCUMBER's domain. One parcel here resolves to 141,929 sf of which most arrived
from seven neighbouring lots across nine years; ENVELOPE computed alone returns
as-of-right FAR on the tax lot and is wrong by a factor of sixteen.
**Settles:** buildable area by use, height and setback controls, at a date.
**Adjudicates:** district composition. Split-district lots need ZR 77-22 — computed
per district portion, not averaged. FAR is per-use (residential ≠ commercial ≠
community facility) in the same district.
★ **Canary at scale:** the ZD1 is the developer's own computation of this number,
signed by an RA and accepted by DOB. 280 Kent: 611,305 zoning floor area, FAR 1.69.
Compare on every job that filed one.

### ENTITLE — permission to change the rules, and its conditions
**Settles:** variances, special permits, ULURP actions, LPC approvals — granted,
conditions attached, expiry, current status.
**Adjudicates:** whether an entitlement is still live. An expiry is a dated
opportunity. 280 Kent carries CPC approvals C 140132–140135 ZSK, N140136–140141
ZAK/ZCK — recorded in §9F of the PW1 and in All Comments, nowhere in a feed.

### PERMIT — permission to do the work
**Settles:** the filing chain per job — what was authorised, when, by whom, current
status, and the work-start date.
**Adjudicates:** amendment order. Doc numbers do not sort by date; the same doc
number is scanned repeatedly; §4A states which document a PAA amends.
⚠ Work start is the first permit for the SCOPE WORK, not mobilisation. A fence or
sidewalk shed is pulled while still in pre-development. "Broke ground" is the wrong
test for 215,062 of 316,585 projects — conversions and enlargements never touch soil.

### ASBUILT — what legally exists here now
**Settles:** certificated use and occupancy by floor, unit count, area, and the
certificate history.
**Adjudicates:** temporary vs final, in two vocabularies —
`bs8b-p36w.issue_type` Temporary/Final, `pkdm-hqz6.c_of_o_filing_type`
Final/Initial/Renewal. Anything not Final is a TCO.
⚠ Only ~19% of scope-bearing jobs ever produce a certificate. Sign-off is the
terminal state for most conversions, enlargements and every demolition.

### PARCEL — the physical lot, its ground and surroundings
**Settles:** area, frontage, shape, corner/through-lot status, topography,
adjacency, flood and wetlands exposure.
**Adjudicates:** geometry source. MapPLUTO polygons can be fragments — use the DOF
Digital Tax Map.

### OCCUPY — who is in it, and on what terms
**Settles:** the tenancy stack — spaces/units, tenants, terms, expiries, regulated
status, vacancy.
**Adjudicates:** legal vs actual use (CO says one thing, operation is another), and
which registration/lease is current.

### CAPITAL — financing, its terms, and its stress
**Settles:** the debt stack over time — loans, amounts, lenders, dates, maturity,
consolidations (CEMA), assignments, satisfactions, current outstanding.
**Adjudicates:** new money vs rolled-in. 280 Kent's $450M JPMorgan facility is
$350M new plus $100M consolidated — treating the face amount as new money
overstates it by 22%.
⚠ Borrower is the SPE, and on a condo the debt sits on the development lot, not the
billing lot.

### DISTRESS — arrears, liens, litigation, enforcement
**Settles:** the distress ledger — what is owed, to whom, since when, and every
dated movement in the balance.
⚠ **Trajectory is derived.** Direction is one step from "is this an opportunity?",
which is a product question.
**Adjudicates:** open vs cured, and whose distress it is (owner vs tenant vs
contractor).

### OBLIGATION — what the owner owes, as distinct from what the land carries
**Depends on:** IDENTIFY · PARTY
**Settles:** covenants personal to a party — reporting, maintenance, operating,
non-compete, completion and payment guaranties. Live vs discharged.
**Adjudicates:** *does it run with the land?* If it binds whoever owns the parcel,
it is ENCUMBER. If it dies when the loan is repaid or the party changes, it is
OBLIGATION.
⚠ A mortgage's monthly construction-progress covenant, its financial reporting and
its junior-financing bar are obligations; the easement recorded the same day is an
encumbrance. Same document, different function, different lifespan.
⚠ A guaranty referenced but never recorded is an obligation whose SIZE the record
cannot give you — record its existence, not a number.

### CONSENT — who agreed, and who was bound without signing
**Depends on:** IDENTIFY · PARTY
**Settles:** consents, waivers and subordinations; their conditions; who executed;
and who is bound by prior consent, by a successor clause, or by a deemed waiver.
**Adjudicates:** authority to bind, and whether a subordination is still in force.
⚠ **A subordination reading "only if and for so long as" is REVERSIBLE.** One here
holds only while the lender is not a competitor, the mortgage stays validly
recorded, AND the debt complies with a section of an unrecorded agreement — so its
rank is not determinable from the register, and saying so IS the answer.
⚠ **Do not infer who agreed from who signed.** Two lenders bound their liens to an
agreement neither ever executed, by recording their own waivers. Seven co-ops
pre-consented to mergers they would never see, on ten business days' notice.

### INTEGRITY — where the record contradicts itself
**Depends on:** IDENTIFY
**Settles:** defects in the record as recorded — wrong cover-page party, an
acknowledgment predating its own instrument, words disagreeing with numerals,
uncured schedule notes, page counts that do not reconcile, a folder holding another
document's body.
**Adjudicates:** whether a defect was **cured**, and when. A live defect and a
cured one are different products.
⚠ **This is product, not exhaust.** A 27-year uncured "NOTE: Recites incorrect
legal description" consolidated forward into the current lien is a title-grade
finding. So is a splitter indexed to the wrong lot — and so is the correction
recorded two years later, without which the defect reads as still open.
⚠ Every material error on the pilot parcel was in HANDWRITING: prior-tax figures,
new-money splits, a $1,000 discrepancy between two copies of one schedule. No text
layer reaches them.

### VALUE — what it is worth, to the city or the market
**Settles:** assessed value history and transaction history — price, arm's-length
vs nominal, what interest was conveyed, and which normalisations are computable
($/SF, $/unit, $/buildable SF).
⚠ **The comparable SET is a deriver, not this resolver.** Comps for a valuation
are not comps for an air-rights listing — the latter wants $/buildable-SF, which
only that product asks for. A resolver that selects a set knows who is asking, and
has leaked.
**Adjudicates:** whether a recorded price is real. The $10 recital is a 500,000×
trap; price comes from the RPTT/RETT stamps. Nominal and partial-interest deeds
must be flagged, not averaged.

---

## EXTERNAL FUNCTIONS

⚠ No document to crop. Confidence comes from **source + vintage**, not a citation.
These need a different evidence model from day one — do not force them into the
claim schema built for record functions.

### COST — inputs a model needs that no property record holds
Construction $/SF, soft costs, carry, absorption.
⚠ Cap rate moved to CONTEXT — it is a market observation, not a construction input.

### CONTEXT — market, demographic and policy background
Submarket rents, cap rates, pipeline, demographics, policy changes.

---

## HOW PRODUCTS SIT ON TOP

A product is a large deriver. It never gets its own resolver.

    Card / parcel timeline   every function, ordered by as-of date
                             ⚠ including INTEGRITY — a reader must see what the
                             record gets wrong, not a cleaned version of it
    Opportunity              ENVELOPE − ASBUILT − ENCUMBER · ENTITLE · DISTRESS
                             · CAPITAL · OBLIGATION · TITLE tenure
    Development              PERMIT · ASBUILT · CAPITAL · PARTY over time
    Comparables              VALUE · OCCUPY · ENVELOPE
    Contacts                 PARTY  ← keyed by person, not parcel
    Air rights market        ENVELOPE · ENCUMBER · TITLE · ENTITLE · CONSENT
                             ★ entirely record-derived — every number crop-provable
                             ⚠ CONSENT is load-bearing here: a transfer needs every
                             party in interest to have signed or waived, and the
                             title certification naming them is its own document
    Valuation                VALUE · OCCUPY · ENVELOPE · CAPITAL · DISTRESS
                             + COST · CONTEXT
                             ⚠ crosses into external — must show the seam between
                             the provable half and the assumed half

★ **Design rule: if a resolver knows which product is asking, it has leaked.**
ENVELOPE resolves the envelope, identically, whether it feeds a valuation, an
air-rights listing or a development card. Resolvers hold the domain; derivers hold
the business.
