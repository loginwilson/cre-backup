# PW1 §26 — the only place the owner's contact exists

Measured 2026-08-06 on Queens block 17 lot 1 (2-29 50 Avenue, LIC),
BIS job **421807511** (DM, filed 2021-10-07, owner PETER PAPAMICHAEL /
50TH & 5TH LIC LLC).

---

## THE FINDING

**Owner contact is carried by exactly one form: PW1 §26. Nothing else on the
job holds it — not the HTML page, not the other 16 documents in the folder.**

The whole folder was swept (16 documents + the PW1, every scan inflated and
its text layer read). Contacts found:

| document | who it gives you | contact |
|---|---|---|
| PW1 §26 | **OWNER** | **the only owner contact anywhere** |
| BIF1 borough intake (×2) | filing rep | eugene@archiprogroup.com · 646-616-7524 |
| HPD3 anti-harassment | applicant | r.aristilde@yahoo.com · 917-656-4312 · 631-485-9661 |
| TR1 technical report | applicant | 917-656-4312 · 631-485-9661 |
| 5-day notice, PW2 ×2 | contractor | Celtic Services 718-717-2721 |
| ACP5 asbestos | DEP investigator | (not the owner) |
| letters, cut-offs, tap letter, PGL1 | — | nothing |

Every non-PW1 document routes to the **applicant, filing representative or
contractor** — the people who are paid to be reachable. The owner appears in
one box on one form.

⚠ **So a scaled contact pull is a PW1 §26 pull.** Reading "all documents" is
wasted effort for the party layer; it is still how you get job description
and details (see below).

---

## ⚠ THE HTML PAGE DROPS THE FIELDS THAT MATTER

`JobsQueryByNumberServlet` §26 for job 421807511 renders:

    26  Owner's Information
    Name:                  PETER PAPAMICHAEL
    Relationship to Owner: MEMBER
    Business Name:         50TH & 5TH LIC LLC     Business Phone:  (blank)
    Business Address:      (blank)                Business Fax:    (blank)
    E-Mail:                (blank)                Owner Type:      CORPORATION

The same §26 **on the scan**:

    Name (please print):   Peter Papamichael
    Relationship to Owner: Member
    Business Name/Agency:  50th & 5th LIC LLC
    Street Address:        184 North 8th Street
    City: Brooklyn   State: NY   Zip: 11211
    Telephone Number:      516-805-1584
    E-Mail Address:        …ea.com          ← domain only; local part lost

**The address and phone exist only in the document.** Confirmed by searching
the whole structured corpus: no owner phone matching `516%1584` belongs to any
Papamichael or Vorea entity (`bty7-2jhb`, 2026-08-06). The page publishes the
name and throws the contact away.

`184 North 8th Street, Brooklyn 11211` is the address `bty7-2jhb` carries for
**VOREA HOLDINGS LLC** in 2012–2013 (phone 914-393-3653). The document ties
`50th & 5th LIC LLC` to Vorea a decade later. The `…ea.com` email tail is
consistent with `@vorea.com`; **the local part was not recovered and must not
be guessed.**

---

## ★ THE METHOD — VOTE ACROSS SIBLING SCANS

A single OCR pass cannot be trusted on digits, but the same §26 is usually
typed onto **several PW1s**: co-filed sibling jobs, and re-scans within one
folder. Each is an independent OCR pass over the same characters, so they can
be voted.

Three DM jobs were filed on this lot on 2021-10-07 — 421807511, 421807502,
421807520 — each with its own PW1 carrying the identical §26:

    job/scancode                 read of the telephone field
    421807511 / SC181108039      "(516) ans1584"
    421807502 / SC181108039      "(516) 805-1591"
    421807520 / SC181108036      "516-805,71584"      ← cleanest scan
    421807520 / SC181108009      "(514) 805" + E-Mail

    area code   516 ×3, 514 ×1        -> 516
    exchange    805 ×3, (lost) ×1     -> 805
    last four   1584 ×2, 1591 ×1      -> 1584

**→ 516-805-1584.** No single scan produced it.

Scan quality is not uniform even within one filing round. `SC181108036`
returned proper mixed case throughout — `Peter Papamichael`, `Member`,
`50th & 5th LIC LLC`, `184 North 8th Street`, `Brooklyn` — while
`SC181108039` on the same §26 gave `50THsSTHLICLLC` and `21[211`.
**Rank the scans and read the cleanest first**; only fall back to voting for
fields that still disagree.

---

## ⚠ SCANCODES ARE UNIQUE ONLY WITHIN A JOB

`SC181108039` is the PW1 in **both** 421807511 and 421807502. The same code
in 421807520 is a different document entirely, and `SC181108036` /
`SC181108009` — the PW1s of 421807520 — are the *letters* and *borough intake
form* of 421807511.

**Always key a document as `(job, scancode)`.** A scancode alone silently
retrieves the wrong document from a neighbouring job, and it will still parse,
still contain a §26, and still look right.

---

## THE SCAN IS READABLE WITHOUT DOWNLOADING IT

`BSCANJobDocumentContentServlet?passjobnumber=&scancode=` returns
`application/pdf`. Fetched **in-page** and parsed in memory — nothing written
to disk, no save dialog:

1. `fetch(url, {credentials:'include'})` → `ArrayBuffer`
2. for each `stream`, read the **declared `/Length`** and slice exactly that
   many bytes
3. inflate with `DecompressionStream('deflate')`, fed by
   `writable.getWriter()` — **not** `new Response(blob.stream())`, which the
   page CSP rejects with `TypeError: Failed to fetch`
4. keep streams containing `Tj`/`TJ`, pull the `( … )` literals

⚠ Two traps that each cost a cycle:

- **Slicing to `endstream` overruns.** DecompressionStream is strict and
  fails with *"Junk found after end of compressed data"*. Use `/Length`.
  Match `/\/Length\s+(\d+)/` so it can't match `/Length1` (the FontFile2 key).
- **`/Filter [/JBIG2Decode]` streams are the raster page images** and will
  never inflate. 18 of 30 streams failed on this document; that is correct,
  not an error.

On job 421807511: 30 streams → 12 inflated → 6 text layers → ~50k chars.

---

## WHICH SCAN — AND HOW MANY THERE ARE

The folder listed **one** PW1: `PW1 | doc 01 | PAA No | SC181108039`. That is
the initial, and the initial is the one the owner signs. Consistent with the
rule already recorded in `DOB_FOLDER_READING.md`: later PAAs leave §26 blank
unless the signatory changed.

But folders are not usually this small. Job **420665275** (NB, VOREA JACKSON
LLC, 2019) holds **38 PW1 scans** — doc numbers 01 through 22, several docs
re-scanned. The four rows carrying `PAA = No` are the candidate initials.
Selecting "the PW1" by form name returns the wrong scan almost every time.

---

## ⚠ TWO SCAN ERAS, DIFFERENT TEXT

| scancode prefix | text layer |
|---|---|
| `SC…` | **full-page LEAD OCR** — whole form readable, digits unreliable |
| `ES…` | **only the typed overlay** — the raster has no OCR at all |

⚠ **The "era" column that used to sit in this table was wrong.** It read
`SC = paper, B-scanned` / `ES = eFiling submission`. Two folders filed in
**2001** carry `ES` scancodes (jobs 401378004 and 401292061, observed
2026-08-07) — and eFiling did not exist in 2001. The prefix more likely names
the **ingest system**, and the folder's `DATE SCANNED` is independent of the
filing date, so an old job can be scanned into the newer system at any time.

What survives: the two prefixes really do differ in whether a full OCR layer is
present, on every document examined so far. **Why** they differ is untested —
see `CONTACT_HARVEST.md`. Do not build date logic on this prefix.

`ES` documents are not born-digital text. Measured on job 440704356 PW1 docs
02/03/04 (2024-12 → 2025-05): 3 streams, **52 characters** — the scancode
banner and nothing else.

Where the overlay *is* populated it is clean, exact text — no OCR risk:

- job 420665275 `ES856156634` → the ACRIS join, as typed:
  `2019000142394, 2019000142393, 2019000123500, 2019000123504, 2019000123501`
- job 420665275 `ES868590818` → §3 filing rep:
  `William Dailey, Building & Zoning Consultant · New York 10036 · 212 586-2114`

So: **`SC` gives you the whole form at OCR quality; `ES` gives you a few
fields at perfect quality or nothing at all.** Neither alone is sufficient.

---

## ⚠ OCR EATS DIGITS — DO NOT TRUST A PHONE FROM A SCAN ALONE

Same page, same OCR pass, job 421807511:

    text                      OCR read
    (516) ***-1584            "(516) ans1584"     ← 3 digits destroyed
    11211                     "21[211"
    50TH & 5TH LIC LLC        "50THsSTHLICLLC"
    184 NORTH 8TH STREET      184 NORTH 8TH STREET   ← clean

Letters and street addresses survive; digit runs do not. Phone numbers read
off an `SC` scan need a second witness before they are treated as a fact.

The document **states its own citation** — every scan's OCR contains its own
job number and scancode (`DEPT. BLDGS. 421807511 … SC181108039 SCAN CODE`),
so a decoded field can be tied back without trusting the URL it came from.

---

## SESSION

A cold hit on any deep servlet returns **Access Denied**. Load
`https://a810-bisweb.nyc.gov/bisweb/bispi00.jsp` first; every servlet and
every `fetch(…, {credentials:'include'})` then works for the session.

Folder discovery needs no navigation — fetch
`JobsQueryByNumberServlet?passjobnumber=…&passdocnumber=01`, parse out the
`Virtual Job Folder` href (it carries the required `allisn`), fetch that, and
read the `FORM NAME · Form ID · Doc No · PAA · DATE SCANNED · SCAN CODE`
table.
