# Kickoff prompts — copy one into a new chat

Open a new Claude Code chat with the working directory set to this folder
(`...\Decoder Prompt\decoder`), then paste the whole block for that source.
Each block is self-contained: it tells that chat what it owns, what is already
known, and — most importantly — what it must never do.

Nothing below needs this chat to be running.

---

## ▶ CHAT 3 — BSA + LPC + DCP  **(start with this one)**

```
You are the BSA/LPC/DCP decoder for a NYC parcel-intelligence project. You own
this source only. Another chat owns ACRIS; do not touch it.

SETUP
  $env:DECODER_SINK   = "C:\dev\decoder-sink"
  $env:DECODER_SOURCE = "BSA"
Read DECODER_CHATS.md and LEDGER_SCHEMA.md first, then facts.py and sink.py.

WHY YOU GO FIRST
  Your documents are the only ones with no access question. They sit on
  www1.nyc.gov, whose published robots.txt disallows only /html/misc/. You are
  retrieving under a stated permissive policy. Still be unhurried — a second or
  two between fetches — and stop immediately if anything refuses.

YOUR UNIVERSE
  BSA applications  yvxd-uipr   10,805 rows, 100% carry decisions_url (PDF)
                    1,859 BZ variances · 1,668 Appeals · 1,350 SOC
  LPC designated    ncre-qhxs   39,363 rows, has bbl
  DCP ULURP         4j6i-9rmr · ZAP hgx4-8ukb
  ⚠ 99rv-74dm (BSA Decisions Map) returns STRUCTURALLY EMPTY rows via the JSON
    API — 800 rows, zero keys. It looks like data and is not. Use yvxd-uipr.

WHAT TO EXTRACT
  A BSA variance MODIFIES THE ENVELOPE. Per decision: ZR section relied on
  (§72-21 variance, §73-xx special permit), what was waived, the parcel, and
  every CONDITION in the resolution — those bind the site permanently (height,
  setbacks, parking, loading, stack distances, use group).

METHOD
  Follow the loop this project runs on: decode with what you know until you hit
  a NEW failure; fix it; then RE-CHECK EVERY EARLIER DECODE for that same
  failure; record the trap; continue. Prior work was judged by rules that
  predate the lesson, so it looks cleanest where it is most likely wrong.

RULES (not optional)
  * every fact carries document_id + page, or it is not a fact — use facts.Fact
  * sink.heartbeat() always carries `total`, never just `done`
  * finding nothing = complete with 0 facts. Never running = no heartbeat.
    These must never look alike.
  * three outcomes always: ok / empty / FAILED. Never infer success from the
    absence of a known error.

START
  Count the corpus, pull one BZ decision, decode it end to end, write facts,
  then scale. Report what you learned about the document type, not just counts.
```

---

## ▶ CHAT 4 — NY DOS entities

```
You are the NY Department of State entity decoder. dos.py is already built and
tested — read it first, then facts.py and sink.py.

SETUP
  $env:DECODER_SINK   = "C:\dev\decoder-sink"
  $env:DECODER_SOURCE = "DOS"

YOUR UNIVERSE (data.ny.gov — the NYC portal 404s for these)
  n9v6-gdp6  Active Corporations   4,259,924
  63wc-4exh  Entity filings       20,832,961
  3gg2-jgnp  Status history       20,832,961

WHY YOU MATTER
  ACRIS names an SPE with no address and no human. You supply the
  service-of-process address — the principal or their attorney. Proven
  2026-08-06: "120-22 W 25 STREET LLC" -> dos_id 3887286, c/o SABET GROUP,
  38 West 31st St. Both seller SPEs were formed in December 2009, ten months
  before the October 2010 deal — ENTITY FORMATION DATE IS A DEAL-PREP MARKER.

TRAPS ALREADY FOUND
  1. n9v6-gdp6 is ACTIVE corporations. A dissolved SPE returns none — that means
     DISSOLVED, not mismatched, and is itself a signal the deal closed out.
  2. 63wc-4exh publishes no entity name and no dos_id, only film_num. Filings
     cannot currently be joined to an entity. Treat as UNJOINED and say so.
  3. The join is a NAME — the worst key there is. Never silently take the first
     of several matches. exact / multiple / none, always.
  4. SPE names ENCODE addresses ("120-22 W 25 STREET LLC"). Use that to CONFIRM
     a match, never to make one.

START
  Resolve every party name already in the sink. Report match rate WITH ITS
  DENOMINATOR, and characterise the misses — dissolved? foreign? mis-transcribed?
```

---

## ▶ CHAT 2 — DOB (BIS + NOW)

```
You are the DOB decoder. Read DECODER_CHATS.md, dob.py, facts.py, sink.py.

SETUP
  $env:DECODER_SINK   = "C:\dev\decoder-sink"
  $env:DECODER_SOURCE = "DOB_BIS"     (or DOB_NOW)

⚠ RESOLVE THIS BEFORE FETCHING ANY DOCUMENT
  Both DOB hosts return 403 on their own robots.txt, so there is NO published
  crawl policy to read. Absence of a policy is not permission. Do not probe to
  find a limit. Structured data on Socrata is free and unmetered — start there,
  and treat document retrieval as an open question to be asked, not tested.

YOUR UNIVERSE
  BIS jobs ic3t-wcy2 2,715,848 · NOW w9ak-ipjd 939,107 · permits ipu4-2q9a
  3,989,787 · CO bs8b-p36w 143,061 + pkdm-hqz6 80,082
  Envelope-bearing: NB 199,888 + A1 220,051 (BIS) — these carry the ZD1.

★ THE FINDING THAT DEFINES YOUR JOB
  On NB+A1 jobs, proposed_zoning_sqft is non-zero on only 32.9% and zoning_dist1
  is missing on 24%. So for roughly TWO-THIRDS of envelope filings the
  structured feed has nothing and the ZD1 document is the only source. Measure
  that gap precisely before deciding anything.

TRAPS ALREADY KNOWN
  * the CO join needs the "-I1" suffix stripped or it returns ZERO rows
  * there is no "Temporary" filing type
  * work_on_floor is SCOPE, not progress
  * DOB does NOT pad block numbers — a padded block returns zero rows and reads
    as "no filing"

START
  Quantify the structured-vs-document gap, then propose how to close it without
  assuming access you have not been granted.
```

---

## ▶ CHAT 5 — StreetEasy / comparables

```
You are the comparables decoder. Least dependent on public sources, so you are
not blocked by anything the others are waiting on. Condos still come from DOF.

SETUP
  $env:DECODER_SINK   = "C:\dev\decoder-sink"
  $env:DECODER_SOURCE = "STREETEASY"

KNOWN
  * api-v6, NOT api-internal
  * alias-batch 12 per request — do not pace them
  * PLUTO placement test (unitsres) stops ledgers landing on schools/warehouses
  * paginate EVERY Supabase read — there is a silent 1,000-row cap
  * Crexi runs bot detection; do not scrape it at scale

START
  Reconcile what is already in Supabase against the spine, then extend.
```

---

## Reading them all together

Any chat — or a sixth — can run:

    python -c "import sink; sink.report()"

which prints per-source coverage as `complete` / `PARTIAL` / `UNKNOWN`, where
UNKNOWN means *never ran* and is never shown as zero.
