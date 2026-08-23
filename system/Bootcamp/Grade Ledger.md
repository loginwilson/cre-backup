# THE GRADE LEDGER — every graded miss, its class, and where the fix landed

Login 2026-08-22: "it's very important that graded filings are recorded
so each bootcamp is improved upon."

A grade buried in prose inside a 5,400-line file cannot improve the next
run. THIS FILE IS THE INDEX. One row per run; miss CLASSES are named so
RECURRENCE IS VISIBLE — the motive-claim defect reached its FIFTH
occurrence precisely because nothing here existed to show it was a
pattern.

**Read this file at grading time. If a miss class already has rows, the
grade is harsher: a repeat of a recorded lesson costs double.**

| run | doc | grade | miss class(es) | fix landed |
|---|---|---|---|---|
| 12 | RC_1002473 1912 | A− | held-moderate (block letter) | — |
| 13 | RC_1043006 2009 | A | held-moderate (marginalia) | — |
| 14 | RC_103895 1944 | A | unresolved stamp ("J 53") | — |
| 15 | RC_1023 1975 | A | — | — |
| 16 | FT_275…1475 1995 | A | partial read (fee ladder) | — |
| 17 | RC_2825423 2026 | A | unread annotation | — |
| 18 | BK_66…0246 1966 | A− | source-limited (cut frame; metes partial) | backer-recovery rule R18-2 |
| 19 | RC_1024032 1951 | A | near-miss: stamp almost banked unread | **CROP LAW R19-1** |
| 20 | FT_286…0086 2001 | A | ambiguity flagged (ENTIRE LOT vs P/O) | — |
| 21 | RC_1052597 2012 | A | held-moderate (handwritten tax cents) | — |
| 22 | RC_1022240 1958 | A− | **single-look misread** (liber 1483→1433, caught by rd) | unread-by-source vs by-render R22-2 |
| 23 | RC_1009281 1968 | A | liber wobble (settled by rd) | — |
| 24 | RC_1051736 1918 | A | — | — |
| 25 | RC_1010265 2018 | A | — | — |
| 26 | 2003040100272005 2004 | A | — | — |
| 27 | RC_1058987 1950 | A | faint bureau stamps | — |
| 28 | RC_1020720 2013 | A | — | — |
| 29 | RC_1046067 1972 | A | held-moderate (notary surname) | — |
| 30 | FT_295…0095 2000 | A− | inference from stamps; address discrepancy unresolved | — |
| 31 | RC_1012471 2018 | A | — | — |
| 32 | FT_285…4985 1991 | A | unresolved annotation | ⚠ `expiration` overloaded R32-3 |
| 33 | BK_66…0437 1966 | A−→**B+** | **RELATIONSHIP asserted** ("heirs") · single-look on faintest film · **vacuous ✓** | distributee≠heir · crop→names/amounts · earned-✓ rule |
| 34 | RC_1032054 1976 | A− | exec-date vs ack conflated · instrument's noun dropped ("units"→"houses") · **era context flat** | keep-the-noun rule |
| 35 | RC_1050386 1956 | **B→B−** | **MOTIVE asserted** ("how the majors did business") · person/entity conflation · non-canonical verb · **crop rule not applied → MISSED a struck term clause** · **length drift 2.4x** | **COMPOSE CARD created** · trigger list · redo practice · term-lines-get-the-crop |
| 36 | BK_67…0213 1967 | A− | **qty_role** (face reported as balance) · caveat lost between record and delivery | Card #10 (money carries its role) · Card #11 (delivery inherits caveats) |
| 37 | RC_1044085 2018 | **B+** | **narrative (5th)** — entity scale-claim slipped the word scan · **name integrity (2nd)** — rule written same day did not fire · lexicon gap (recall, not lookup) | Card #4 extended (scale/scope claims) · **Card #12 PRE-BANK PASS** · Lexicon: servicer |
| 38 | RC_1003223 1969 | A− | **keep-the-noun (2nd)** — "buildings"→"houses", same default as R34 · minor: unreadable exhibit's LEGEND unbanked | pattern named; bank-what-is-readable-about-reading-it |
| 39 | RC_1029519 1984 | **B → D on re-grade** | **keep-the-noun (3rd)** — "premises/dwelling"→"house", the WATCHED WORD, one run after watching it; possibly false, not just narrow · narrative (6th, mild) · **FABRICATED COUNT ("5th sighting" — series never existed)** · **identity asserted from a shared name, conflating a person with a P.C.** · **financial terms altered**: "a MINIMUM of 9½% CUMULATED monthly" delivered as "9.5% compounding monthly" | keep-the-noun → STRUCTURAL; **Card #13 (no count without a grep)**; R21/R23/R39 counts corrected in place |

## RECURRENCE — the reason this file exists

| class | runs | status |
|---|---|---|
| **narrative: motive / relationship / era / SCALE asserted as fact** | 10, 33, 34, 35, 37 | **5 occurrences.** Rule existed from R10; failed twice more. Fixed structurally at R35 with the Compose Card TRIGGER LIST, not another rule. CLEAN at R36; FAILED AGAIN at R37 — but differently: the claim used ORDINARY WORDS, so the phrase-scan could not see it. The trigger list works for its shape and is blind to others. Card #4 extended; the general fix is the PRE-BANK PASS (#12). |
| **single-look value on degraded film** | 22, 33, 35 | Crop law written at R19, violated at R33 and R35. R35's violation HID AN EVENT-SHAPING DELETION. Card #9 now names term lines and identity strings explicitly. CLEAN at R36 (crop run before composing). |
| **qty_role: face vs unpaid vs consideration** | 11, 33, 36 | **3 occurrences → MISSING STRUCTURE.** Row schema must REQUIRE a qty_role so a bare amount is UNREPRESENTABLE. **Converges with keep-the-noun on the SAME cure: generate the summary from row values.** Queued for the extraction spec. |
| **name integrity (principal misspelled / unverified)** | 21, 37 | **CLEAN at R38** — the pre-bank pass verified Kozial at 450dpi and held the notary at moderate. Found on backward re-check, not at grading. Worst class for a stakeholder product: the join breaks silently while the row looks complete. Principal names get a second look before banking — **written after R21 and did NOT fire at R37 the same day**, because it is a WORKFLOW step and the card only scanned phrases. Now Card #12. |
| **class label applied to an instance** | 25 | The lexicon DEFINES a class; only the document places an instance in it — else a definition becomes a diagnosis. |
| **keep-the-instrument's-noun** | 34, 38, 39 | **3 occurrences → MISSING STRUCTURE.** Same substitution every time: a broad noun ("residential units", "buildings", "premises/dwelling") → "houses". Word-scan added at R38 FAILED at R39 because the card was not re-read at compose time — mechanism 1's reliability equals its loading step's. **Structural cure: summary GENERATED FROM ROW VALUES prints the row's own noun.** Same cure as qty_role. |
| **⚠ FABRICATED SERIES / COUNT** | 21, 23, 39 | **The worst class: it manufactures corroboration.** "Notary-is-counsel, third sighting" was written with ZERO prior sightings recorded, then incremented twice. Defeats the word-scan (ordinals are ordinary words), the pre-bank checklist (it checks names/sources/slots, not arithmetic about the file), and the assumption law (a count feels like a record-fact). Needs its own mechanism: **Card #13, grep before any count.** |
| **person / entity conflation** | 35, 39 | An officer is not his corporation; a person is not a P.C. of the same name (R39 "William W. Mizrahi" vs "William W. Mizrahi, P.C."). |
| **vacuous reconciliation ✓** | 33 | Rule added same run; correctly applied at 34, 35, 36. |
| **length drift** | 35 | Measured 2.4x growth in one day. Card #8. R36 came in ~50% shorter. |
| **non-canonical vocabulary** | 35 | If no canonical verb fits, it is a RULING to queue, never a verb to coin. |

## HOW TO USE THIS FILE

1. **At grading:** name the miss CLASS, not just the instance. Check this
   table — if the class has prior rows, say so and grade harder.
2. **After grading:** add the row. If the fix is a compose-time behaviour,
   it goes in `Compose Card.md`; if it is a reading/structural law, it
   goes in `Bootcamp.md`. Record WHICH in the fix column — a fix with no
   home is a fix that will not fire.
3. **A class with 3+ rows is not a discipline problem — it is a MISSING
   STRUCTURE.** Stop writing rules and change the shape (that is what the
   trigger list did).
