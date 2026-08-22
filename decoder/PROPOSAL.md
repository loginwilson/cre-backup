# Proposal — what to change, and in what order

Six changes. Ordered by dependency, not importance: the schema has to move
first because the function edits and the invariants both reference fields it
does not yet have.

---

## 1 · Widen `claim` — the term-heavy shape

Keep four tables. The contract is right; the claim row is too narrow.

```sql
alter table claim add column kind text not null default 'QUANTITY';
  -- QUANTITY | IDENTIFIER | PARTY | TERM_REF | ASSERTION
  -- ⚠ THE ONE TO FIGHT FOR. $39,229,334 in a mortgage schedule is a
  -- POINTER to an earlier lien, not this instrument's amount. Without
  -- kind, no resolver can separate new money from a recital of old money,
  -- and that separation IS the CAPITAL function.

alter table claim add column assertion_type text not null default 'PRIMARY';
  -- PRIMARY  the instrument doing the thing
  -- RECITAL  a later document describing it
  -- ⚠ PRIMARY OUTRANKS RECITAL, ALWAYS, REGARDLESS OF COUNT. A 1990
  -- mortgage records $22,500 of tax paid, in a margin note and a machine
  -- stamp. A 2003 affidavit says $27,500 and a 2014 affidavit says
  -- $28,000. Majority vote returns the wrong answer 2-1. Each affidavit
  -- supported a tax exemption.

-- deontic shape, for terms
alter table claim add column modality   text;   -- MUST | MUST NOT | MAY
alter table claim add column actor      text;   -- who is bound
alter table claim add column condition  text;   -- the predicate that must hold
alter table claim add column exception  text;   -- the carve-out
alter table claim add column consent_of text;   -- who can release it

-- lifecycle
alter table claim add column status  text not null default 'EXECUTED';
  -- EXECUTED | CONTINGENT | EXPIRED | SUPERSEDED
alter table claim add column trigger text;
  -- ⚠ what makes a CONTINGENT term live. Five burdens were recorded off
  -- an annexed blank form and had to be retracted; it bound only if later
  -- requested and signed.

-- geometry, for volumetric terms
alter table claim add column v_from   numeric;  -- feet above datum
alter table claim add column v_to     numeric;
alter table claim add column v_datum  text;     -- verbatim, never normalised
alter table claim add column h_extent text;
alter table claim add column duration text;     -- perpetual | term | until X

alter table claim add column supersedes text references claim(claim_id);
```

**Why not a fifth `term` table.** A term and a value are the same assertion
at different densities — the 2019 upzoning clause is *both* a term (a
formula) and a value (45.48%). Splitting them forces every resolver to read
two tables and reunite them, and the reunification logic is where the loss
happens. One row, more columns, `kind` discriminating.

**The failure this prevents is silent, not loud.** `term = "light and air
easement", value = 130` is queryable, plausible, and drops four things: the
word **view** (a third right the operative grant includes and the annexed
form omits), which side of the plane was conveyed, who is burdened vs
benefited, and the carve-out preserving the servient owner's building. A
schema that rejects bad input is safe. One that accepts a lossy version is
not.

**Validate `kind` against the predicate at write time.** A TERM_REF row
carrying a number should raise, not warn. That check caught a real error
here within minutes of existing.

---

## 2 · Declare the resolver DAG

The architecture implies a flat set with one exception ("IDENTIFY must run
first"). It is not flat.

```
IDENTIFY
   └─ PARTY
        ├─ TITLE
        ├─ ENCUMBER ──┐
        ├─ PARCEL ────┤
        │             └─→ ENVELOPE      needs rights transferred in/out
        ├─ CAPITAL         (ENCUMBER)   and lot area (PARCEL)
        ├─ PERMIT ───→ ASBUILT
        ├─ ENTITLE
        ├─ OCCUPY
        ├─ OBLIGATION
        ├─ DISTRESS
        ├─ INTEGRITY
        └─ VALUE
```

⚠ **ENVELOPE cannot resolve without ENCUMBER's output.** You define ENVELOPE
as "what may be built as of right" and put "development rights transferred
OUT" under ENCUMBER — so the buildable number is
`zoning FAR × lot area + rights in − rights out`. Either resolvers may read
other resolvers' timelines, or ENVELOPE re-derives transfer logic and you
have duplicated the hardest code in the system.

**Recommendation: resolvers may read other resolvers' OUTPUT, never their
internals, and the dependency is declared.** That keeps re-runnability (the
DAG is a topological sort, still zero network calls) and kills the
duplication. Add to the register: each function names what it depends on.

**Worked example.** Lot 49's envelope is 141,929 sf. That number is
`209,968 + 22,845 + 10,726 + 10,722 + 14,703 = 268,964`, split in 2019 into
`141,929 / 127,035`. Every addend is a recorded transfer — ENCUMBER's
domain. ENVELOPE without ENCUMBER returns the as-of-right FAR on 8,527 sf
and is wrong by a factor of sixteen.

---

## 3 · Function register — four edits

**DEFINE OBLIGATION.** It is listed in the architecture and absent from the
register: 16 named, 15 defined.

> **OBLIGATION — what the owner owes, as distinct from what the land carries**
> **Settles:** covenants personal to a party — reporting, maintenance,
> operating, non-compete, guaranty. Live vs discharged.
> **Adjudicates:** *does it run with the land?* If yes it is ENCUMBER. If it
> dies when the loan is repaid or the party changes, it is OBLIGATION.
> ⚠ A mortgage's monthly construction-progress covenant and its
> junior-financing bar are obligations. The easement recorded the same day
> is an encumbrance. Same document, different function, different lifespan.

**ADD INTEGRITY.**

> **INTEGRITY — where the record contradicts itself**
> **Settles:** defects in the record as recorded — wrong cover-page party,
> acknowledgment predating its own instrument, words disagreeing with
> numerals, uncured schedule notes, page counts that do not reconcile.
> **Adjudicates:** whether a defect was cured, and when.
> ⚠ This is PRODUCT, not exhaust. A 27-year uncured *"NOTE: Recites
> incorrect legal description"* consolidated forward into the current lien
> is a title-grade finding. So is a splitter indexed to the wrong lot — and
> so is the 2020 remark that *cured* it, which is the difference between a
> live defect and history.

**ADD CONSENT.**

> **CONSENT — who agreed, and who was bound without signing**
> **Settles:** consents, waivers, subordinations and their conditions; who
> executed; who is bound by prior consent or by a successor clause.
> **Adjudicates:** authority, and whether a subordination is still in force.
> ⚠ A subordination reading *"only if and for so long as"* is REVERSIBLE.
> ⚠ Two lenders here bound their liens to a ZLDA neither ever signed. Seven
> co-ops pre-consented to mergers they would never see, on ten business
> days' notice. Do not infer who agreed from who signed.

**DESCOPE two leaks.**

- VALUE settles *transactions* — price, arm's-length or nominal, interest
  conveyed, which normalizations are computable. **"The comparable set" is a
  deriver.** Comps for a valuation are not comps for an air-rights listing;
  the latter needs $/buildable-SF, which only that product wants.
- DISTRESS settles the *ledger with dates*. **Trajectory is derived** —
  direction is one step from "is this an opportunity?"

Also move **cap rate from COST to CONTEXT**. It is a market observation, not
a construction input.

---

## 4 · Two invariants, enforced in the database

```sql
-- ⚠ EVERY DOCUMENT DID SOMETHING.
alter table source_document add column barren_reason text;
create or replace view document_without_claim as
select d.* from source_document d
where d.barren_reason is null
  and not exists (select 1 from claim c where c.document_id = d.document_id);
```

Nobody pays to record a document that says nothing. Twenty-five documents
here were logged as "opened, yielded nothing" — seven assignments moving the
lien between named holders, five certifications recording who signed and who
waived, and the **Marriott Amended & Restated Right of First Refusal**, read
in full and never recorded. Without this, *"we read it"* and *"we got
nothing from it"* are the same row and coverage is unmeasurable.

```sql
-- ⚠ A READ CLAIM CARRIES ITS PROOF, AND THE PROOF CARRIES ITS REGION.
alter table proof add column y0 numeric;
alter table proof add column y1 numeric;
create or replace view claim_without_proof as
select c.* from claim c
where c.evidence = 'read'
  and not exists (select 1 from claim_proof p where p.claim_id = c.claim_id);
```

Capture the region **at read time**. It is unrecoverable later without
re-fetching. 132 crops here are whole-page at ~69 KB because nothing
required it; the readers knew where each fact sat and were never asked. A
clause crop is ~7 KB. That is 10× storage forever on a field the schema
could have demanded — and across 1.16M parcels it is the difference between
~2.4 TB and ~300 GB.

---

## 5 · What the extractor must emit, restated

Not "term, value, subject, as_of" but:

    subject_raw · as_of · kind · assertion_type · predicate
    value_num | value_text · unit
    modality · actor · condition · exception · consent_of · status · trigger
    geometry (v_from · v_to · v_datum · h_extent · duration)
    page · region (y0,y1) · verbatim

**`verbatim` is not optional.** 31% of claims here are paraphrase with a page
cite — an assertion wearing evidence's clothes. The words *are* the fact;
"upper" versus "lower" limiting plane is one word and it reverses which
volume was bought.

---

## 6 · Order of work

1. **Schema** (§1) — everything else references these fields.
2. **Invariants** (§4) — cheap, and they make step 3 measurable.
3. **Register edits** (§3) — OBLIGATION, INTEGRITY, CONSENT, the two descopes.
4. **DAG** (§2) — declare dependencies, topologically sort resolvers.
5. **Re-run one parcel end to end** and diff against the hand decode.

⚠ Step 5 is the only real test. Everything above is a hypothesis until a
cold run reproduces a known answer. Pick a parcel that is *not* lot 49 — I
have over-fitted to it, and a system that only works on the parcel it was
designed against has not been tested.

---

## What I would not change

The extractor/resolver/deriver split is right. `subject_raw → subject_id` is
right and survived a real test: a 2018 instrument indexed to the wrong lot,
cured by a 2020 ACRIS remark the extractor could not possibly have known —
the extractor stayed dumb, IDENTIFY fixed it. The four-table interface is
right. "If a resolver knows which product is asking, it has leaked" is right
and catches real leaks; it caught two in your own register.

The design is sound where it describes **flow** and thin where it describes
**evidence**. Every failure worth fixing lives in the thin part.
