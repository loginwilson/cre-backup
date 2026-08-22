# The shared parcel ledger — schema for N parallel decoders

**Login's architecture, 2026-08-06:** many decoders, one per source, each running
its own source start-to-finish, all following the same parcel ledger. A master
ledger consolidates the timeline. The app later summarises and maps. **The
decoders' only job is collection — efficiency and accuracy.**

That works. It needs four tables, and the reason it needs exactly four is that
each answers a question the others structurally cannot.

---

## Does it require a Supabase restructure? Yes — a small, clean one.

The current store keeps decoded facts but has no **parcel ledger** and no
**per-source document ledger**, so there is nowhere to record *what exists but
has not been read*. That is the single most important thing to store, because it
is the only defence against a timeline that looks complete and is not.

---

## 1. `parcels` — the shared spine. ONE row per BBL, ever.

    bbl              text primary key      -- 10-digit, zero-padded
    borough          smallint
    block            integer
    lot              integer
    lot_kind         text                  -- ground | condo_unit | condo_billing | reuc | air
    status           text                  -- live | retired
    successors       text[]                -- lineage; a retired lot points forward
    predecessors     text[]
    first_seen       date
    last_seen        date

**858,602 live tax lots** (Queens 324,559 · Brooklyn 276,311 · Staten Island
125,692 · Bronx 89,496 · Manhattan 42,544), **plus retired BBLs**.

⚠ **Retired lots must be rows, not omissions.** A lot that merged in 2017 still
owns its pre-2017 history, and any gate keyed to *live* lots drops it silently.
Every decoder joins here, so the spine must be built once, first, before any
decoder runs.

## 2. `source_documents` — the per-source ledger. THE COVERAGE TABLE.

    source           text        -- ACRIS | DOB_BIS | DOB_NOW | BSA | LPC | DCP | DOF | HPD
    source_doc_id    text        -- ACRIS document_id, DOB job #, BSA calendar #
    bbl              text        -- FK parcels; a document may have many rows
    doc_type         text        -- DEVR, ZONE, NB, A1, BZ ...
    happened         date        -- signed / filed
    recorded         date        -- made public
    reel             text        -- microfilm citation for FT_ documents
    decode_status    text        -- unread | queued | decoding | decoded | FAILED | unreadable
    parser_version   integer
    pages_total      integer
    pages_read       integer
    primary key (source, source_doc_id, bbl)

**This is the table the whole design turns on.** It is populated from each
source's FREE index *before* any image is fetched, so **what exists is known even
when what it says is not**. Without it, "no facts in 1979" and "never looked at
1979" are indistinguishable — and on the pilot parcel that was the difference
between 3 documents and 41.

## 3. `facts` — citation-grade, exactly `facts.Fact`

    fact_id          bigserial primary key
    source           text
    source_doc_id    text
    page             text        -- REQUIRED. no page, no fact.
    bbl              text
    predicate        text        -- controlled vocabulary, never prose
    happened         date
    recorded         date
    value            numeric
    unit             text        -- USD | sf | ratio | ft
    parties          jsonb
    confidence       text        -- read | derived | inferred
    derivation       text        -- REQUIRED when confidence='derived'
    verbatim         text
    parser_version   integer
    run_id           text

Indexes on `(bbl, happened)` and `(source, source_doc_id)` — the timeline reads
the first, the ledger reconciles on the second.

## 4. `runs` — per-decoder heartbeat WITH ITS DENOMINATOR

    run_id, source, started_at, last_beat, done, total, status, note

`done` alone cannot be wrong and cannot be useful. `total` makes 40 either
"finished" or "a fifth of the way, and it stopped."

---

## Why this survives N decoders when a single pooled table would not

**Each decoder owns one `source` value and writes only its own rows.** No two
decoders ever write the same primary key, so there is no contention and no
locking — concurrency falls out of the partitioning rather than being managed.

**Coverage stays per-source and never averages.** You can say *"ACRIS 3 of 41,
DOB 12 of 12, LPC never ran."* You can never say *"the parcel is 60% done,"*
because that number would be meaningless and would be believed.

**Sources fail independently.** ACRIS was refusing service on 2026-08-05 while
DOB was fine. A pooled model cannot express "this source is stale"; a per-source
ledger states it.

---

## Priority, because 858,602 parcels is not a queue you finish

At ~12 documents per parcel that is **~10 million documents**. The ledger holds
every parcel; the WORK QUEUE is ordered. Suggested ordering, cheapest signal
first, all computable from free data:

1. parcels with any of the **1,879 rights instruments** (DEVR 1,201 · AIRRIGHT 64
   · LIC 140 · DEED,RC 474) — the highest-signal documents in ACRIS, 0.011% of it
2. parcels with a **ZONE** (46,079) — an existing zoning lot declaration
3. parcels with a live **NB or A1** DOB filing — something is being built now
4. parcels with unused FAR above a threshold — the opportunity set
5. everything else

**Never let the queue's order be mistaken for the ledger's extent.** Print both.

---

## Running it

Each chat exports the same sink and its own source:

    $env:DECODER_SINK = "C:\dev\decoder-sink"
    $env:DECODER_SOURCE = "ACRIS"        # or DOB_BIS, BSA, LPC, STREETEASY

`sink.py` pools facts lock-free (append-only JSONL, one write per line) and
`sink.report()` prints per-source coverage with `complete` / `PARTIAL` /
`UNKNOWN` — where UNKNOWN means *never ran*, which is not the same as
*found nothing* and must never be shown as zero.
