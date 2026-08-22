# Getting the owner's full contact when the PW1 is unavailable

Measured 2026-08-06.

## THE PROBLEM, STATED EXACTLY

DOB NOW (2016 →) publishes the owner's **name, title and entity** and withholds
**street, phone and e-mail**. Three surfaces tested, all agree:

    Filing Details -> Plans/Work (PW1)   name + Title (MEMBER) + entity. No reach.
    Filing Details -> Documents          empty, and fires NO network request
    Job Summary manifest                 ZD1 / SSP / Work Permit / CO / LOC / TPP
                                         as STATUS TEXT, not links:
                                         <div>ZD1: DOB Zoning Diagram - Accepted</div>

★ And only ONE filing of 39 carries the project documents: **`-I1`, the initial.**
Every other filing (Z1-Z5, S1-S9, P1-P9, A/B/C series) carries just its own trade
permit or LOC. So the NOW inventory is **one filing per job to open, not 39** —
but there is nothing to open, because the manifest is status only.

**Likely cause, and it matters for the fix:** there is no scanned PW1 in the NOW
era because **there is no paper PW1**. The form became the online filing. DOB
still collects owner phone and e-mail — it renders the rest of the block — and
simply does not expose those two fields publicly. That is a policy choice about
a field that was public on the paper form for decades, not a technical barrier.

---

# THE ANSWER: CONTACT IS A PROPERTY OF THE PERSON, NOT THE FILING

You do not need *this job's* PW1. You need **any document, from any era, that
names the same party with full contact.** The NOW portal gives you the identity
— `PETER PAPAMICHAEL · MEMBER · 50TH & 5TH LIC LLC` — which is the join key.
Reach comes from elsewhere.

    deed        -> the ENTITY            (holding company, tells you nothing)
    mortgage    -> the NAME under it     (a member, sometimes the real company)
    NOW portal  -> the NAME + ROLE + entity, per job          <- identity
    ???         -> phone · e-mail · mailing address           <- reach
                   ^ resolved from the PARTY REGISTRY below

## THE PARTY REGISTRY — every source that carries full contact

| source | era | gives | fill (measured) |
|---|---|---|---|
| **`bty7-2jhb` permits** | 1989-2013 | owner name · **full mailing address** · **phone** | **96.5% / 96.3% / 94.6%** of 719,368 scoped rows |
| **BIS PW1 §26** (B-Scan) | 2008-2016 | name · **role** · entity · address · **phone** · **e-mail** · signature date | document read |
| **ACRIS Notices block** | 2004 → | named human behind an SPE, **with phone**, plus attention-party and entity linkage | per `EXTRACTION_CONTRACT.md` — "the richest contact source in ACRIS" |
| **ACRIS acknowledgments** | — | the human who **signed for** the entity, plus a/k/a name variants | Chat 1 |
| **HPD registration** `feu5-w2e2` | annual | head officer · officer · corporation · managing agent, each with mailing address | residential only |
| **DOS** `n9v6-gdp6` | — | service-of-process address for the SPE | Chat 4 |
| **DOB licence register** `t8hj-ruu2` | — | business phone 75.8% · e-mail 40.3% | **trades only** — no PE/RA |
| **NOW portal** | 2016 → | applicant + filing rep **business addresses** | 100% / 79% |

## THE JOIN, AND WHY IT WORKS

**A developer who filed a DOB NOW job in 2022 almost certainly filed BIS jobs
before 2016.** The same principal, the same entity family, the same firm. So:

1. Take the NOW owner identity (name + title + entity).
2. Look that person and that entity up in the registry built from the sources
   above — especially BIS-era §26 and `bty7-2jhb`, which carry phone and address.
3. If any hit, you have reach for a person the NOW filing would only have named.

★ **And one hit unlocks the rest.** Once ANY filing gives you
`BRUCE.WEILL@TFCORNERSTONE.COM`, you have the real company behind BUD SOUTH LLC
— and the domain generalises: every other SPE that firm uses resolves to the
same operating company, and the e-mail pattern (`first.last@domain`) is
inferable for colleagues named on other filings.

## ⚠ THE TRAP THIS MUST NOT WALK INTO

The join key is a **NAME**, which `DECODER_CHATS.md` already records as the worst
key there is. Same lesson as DOS: **exact / multiple / none, always** — never
silently take the first match. And names are dirty in these very feeds:
`BANBI REALTY CORP` and `BAMBI REALTY CORP` are one owner in one dataset.

So every registry hit carries: the source, the document_id + page it came from,
the match quality, and the date. A 2011 phone number for a person is a lead, not
a fact about today.

## INDIRECT ROUTES — reachable people who know the principal

When the owner cannot be resolved, these are named with full business addresses
on the NOW filing itself:

* **Filing representative** — 79% have full postal. They are paid to be reachable
  and they act for the owner.
* **Applicant of record (architect/engineer)** — 100% named, 99.9% business
  street, and their licence joins nothing at DOB (they are State-licensed), but
  the firm is public.
* **Permittee/contractor** — `permittee_s_phone__` on **99.6% of 3,989,787**
  BIS permits. A direct phone, always.

These are not the owner. They are one call from the owner, and they are free.

## ORDER OF WORK

1. **Harvest `bty7-2jhb`** — 719,368 scoped rows, owner name + address + phone at
   ~95%. Free, no document, no permission. Largest single contact acquisition
   available and currently untouched.
2. **Build the party registry** keyed on normalised person and entity, with
   provenance and match quality on every row.
3. **Decode BIS-era PW1 §26** for the 2008-2016 window — the only source that
   carries role AND reach AND the e-mail domain in one block.
4. **Resolve NOW owners against the registry**; report exact / multiple / none.
5. **Ask DOB** why owner phone and e-mail are suppressed in the public payload
   when the same fields were public on the paper PW1. That is the real fix for
   2016+, and it is a question, not a workaround.
