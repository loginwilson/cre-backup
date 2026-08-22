# Running the decoders in parallel — one chat per source

**Login is right: one chat cannot be all the decoders.** Not because of speed —
because a chat that decodes everything holds no source long enough to learn its
traps, and the traps are the whole value. ACRIS took a full day to yield nine of
them.

Each chat below owns ONE source, learns it deeply, and writes to the shared sink.
None of them needs to know the others exist.

---

## Shared setup — identical in every chat

    $env:DECODER_SINK   = "C:\dev\decoder-sink"
    $env:DECODER_SPINE  = "C:\Users\smile\Downloads\Source Folder (Real Estate Data)\Decoder Prompt\decoder\spine"
    $env:ACRIS_CORPUS   = "D:\acris"          # wherever the images live
    $env:DECODER_SOURCE = "ACRIS"             # <- the ONLY line that differs

Every chat: `cd` to the decoder folder, `python spine.py --walk <bbl>` to get the
parcel family, decode, `sink.emit(fact, run_id)` per fact, `sink.heartbeat(...)`
with a **denominator** every N documents.

**The rules that make parallel work safe** (they are not optional):

* one chat writes one `source` value — never another's
* every fact carries `document_id` + `page`, or it is not a fact
* `heartbeat` always carries `total`, not just `done`
* a source that finds nothing reports `complete` with 0 facts; a source that
  never ran reports nothing. **These must never look alike.**

---

## Chat 1 — ACRIS  *(the one already running; hardest, keep it here)*

**Universe** 17,036,716 documents · 95 types · 1,278,242 envelope/encumbrance
**Modules** `fetch_pages` · `fetch_document` · `consideration` · `metes` ·
`doctype_rules` · `facts`
**Learned so far** the $10 recital trap · price from cover-page tax stamps ·
floor area lives in a sealed SURVEY · one recording bundles several instruments ·
`FT_` microfilm is 35.8% and 79% lack `document_date` · catch-alls hide tax
foreclosures
**Still to learn** DEED, MTGE, SAT, ASST at depth (74.8% of the corpus)
**⚠ Rate** 25s between requests, hard stop on refusal. Never re-run range scans.

## Chat 2 — DEVELOPMENTS  *(was "DOB (BIS + NOW)"; renamed 2026-08-06)*

**The question, not the source:** *what has physically happened on this ground,
from the earliest public record to today* — built, demolished, converted,
enlarged, occupied. Whatever source answers that belongs here.

**Owns** DOB BIS · DOB NOW · B-Scan job documents · permits (`ipu4-2q9a`) ·
**historical permits (`bty7-2jhb`, 1989)** · CO · **HPD** · **DORIS tax photos**

**★ HPD IS ASSIGNED HERE (2026-08-06).** It was unowned. Two reasons it lands
here rather than with Entitlements:
* **I-cards ("Historical Image Cards") reach 1914** — HPD inherited the Tenement
  House Department's records, so it holds a pre-1938 *development* archive that
  has nothing to do with its modern housing function. One card carries the new
  building plan (filed / approved / certificate issued), alteration plans,
  legal occupancy, lot size, unit mix and rents, and runs to ~1985.
* **CONH blocks DOB permits** — a hard per-parcel development gate that appears
  in no recorded instrument.
Its housing-condition side (violations, litigation, charges, LL44 rents) is
lower priority here but is NOT another chat's; take it or leave it explicitly,
never silently. Registration contacts feed the contact layer and are one of the
only public routes to co-op ownership, which records no deed.

**Reach — measured, not assumed** (see `DEVELOPMENT_SOURCES.md`)

    1914 ──────────────────────────► ~1985   HPD I-card (residential only)
            1939-41 ●                        1940s tax photos (every building)
                        1982-87 ●            1980s tax photos (every building)
                            1989 ──► 2013    bty7-2jhb historical permits
                              ≥1992 ───► 2022  ipu4-2q9a permits
                                  2000 ────►  BIS jobs
                                    2008 ──►  B-Scan DOCUMENTS + DOF lineage
                                      2016 ►  DOB NOW

**★ 2008 is the digital horizon** — scanned documents, the keyed zoning figure
and published lot lineage all begin there. Below it: index only.

**⚠ CORRECTIONS to the original brief, all measured**
* *"proposed_zoning_sqft non-zero on only 32.9%, zoning_dist1 missing on 24%"* —
  both reproduce and both are artefacts of counting amendment rows. On
  ORIGINALS (`doc 01`) the district is **100%**. The one real gap is an ERA:
  the field is 1.9% before 2008 and 100% from 2009.
* *"Access UNKNOWN — ask, do not probe"* — **resolved. It is open.** The 403 is
  an Akamai visitor queue: **wait, never refresh.** Full path proven to the
  scanned PDF. DOB NOW's portal publishes a per-filing Zoning Information
  section that the Socrata extract does not have columns for.
* *"DOB does not pad block numbers"* — wrong for most. **Five key conventions**
  measured across six datasets.

**⚠ Owns the SEAMS.** No layer is a superset of the one below: on Queens 17/1
the permits feed held five jobs the jobs feed did not, and the jobs feed held
one the permits feed did not. Resolve the site identity set (every BBL ∪ every
BIN), fire all layers in parallel, merge on date, segment at the demolitions.

**Consumes, does not decode:** Entitlements (BSA/LPC/DCP) and ACRIS facts, read
from the sink to place a variance or a ZLDA on the same timeline.

## Chat 3 — BSA + LPC + DCP  *(start here — the only fully open documents)*

**Universe** BSA 10,805 applications, **100% with a decision PDF**; LPC 39,363
designated/calendared; DCP ULURP + ZAP
**Why start here** these PDFs sit on `www1.nyc.gov`, whose published
`robots.txt` disallows only `/html/misc/`. **Retrievable under a stated
permissive policy** — no access question to resolve.
**What they yield** BZ variances (1,859) modify the envelope directly: FAR,
height, setback, use. Conditions bind the site permanently.
**Proven** a 13-page §72-21 variance decoded end to end 2026-08-06.

## Chat 4 — NY DOS entities  *(`dos.py` — built, tested)*

**Universe** 4,259,924 entities · 20,832,961 filings — on **data.ny.gov**, NOT
the NYC portal (the city domain 404s)
**Why it matters** ACRIS names an SPE; DOS gives the service-of-process address —
the principal or their attorney. Proven: `120-22 W 25 STREET LLC` →
`c/o SABET GROUP, 38 West 31st St`.
**⚠ Two traps already found**
  1. `n9v6-gdp6` is **ACTIVE** corporations. A dissolved SPE returns *none* —
     that means **dissolved**, not mismatched, and is itself a deal signal.
  2. `63wc-4exh` publishes **no entity name or dos_id**, only `film_num`, so
     filings cannot yet be joined to an entity. Treat as UNJOINED.
**★ SPE names encode addresses** — "120-22 W 25 STREET LLC" is named for its
building. Use it to CONFIRM a match, never to make one.

## Chat 5 — StreetEasy / comparables

**Why separate** least dependent on public sources, so it is not blocked by any
of the above. Condos still come from DOF.
**Known** api-v6 not api-internal · alias-batch 12/request, do not pace ·
PLUTO placement test (`unitsres`) stops ledgers landing on schools · paginate
every Supabase read (silent 1,000-row cap).

---

## Sequencing

**Chat 3 first.** It is the only source with no access question, so it proves the
parallel architecture end to end while ACRIS keeps learning types here.

Then Chat 4 (DOS is free, unmetered, already built), then Chat 2 once DOB's
policy question is answered, then Chat 5.

**Do not start any decoder before the spine finishes.** Every decoder joins on
it, and a parcel missing from the spine is a parcel no decoder ever visits.
