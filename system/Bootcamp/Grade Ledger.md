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
| **column mis-assignment (number read without its heading)** | 40 | **NEW at R40.** Cousin of qty_role but distinct: there the number lacked a role, here it had one and was attached to the WRONG PARENT. A $0.00 total under **Mortgage** was read as the NYC transfer tax and nearly delivered as "NYC collected zero on a $2.86M sale." Caught by the pre-bank crop — but only after being stated in-turn as an "open question," which is still noise. Fix: Card #12 gains COLUMN. |
| **blank read as negative** | 40 | Caught, not committed. An unchecked box is ABSENCE OF ASSERTION; `null`, never `false`. Dangerous specifically at scale, where `false` becomes a counted population. Fix: Card #12 gains BLANKS. |

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
| 40 | 2003012800054001 2003 | _awaiting login_ | **column mis-assignment** (NEW class — $0.00 mortgage-tax total read as NYC transfer tax; caught by crop before delivery, but stated in-turn as an 'open question' first) · blank-checkbox-as-negative (caught, not committed) | R40-3 · R40-4 · Compose Card #12 extended (money needs its COLUMN HEADING in the crop) |
| **record-correct / delivery-wrong** | 36, 38, 40 | **3 occurrences → MISSING STRUCTURE.** R36 lost a caveat, R38 narrowed "buildings"→"houses" in the prose only, R40 dropped the buyer's signer from the anybody test while banking him in the rows. Every existing mechanism (word scan, pre-bank checklist) fires BEFORE BANKING; the delivered verdict passes through no gate. ⚠ R40's instance is the worst: the dropped human was the ONLY reachable person on the buying side, and he lives on a supporting page past the main page count. **Cure: Card #15 THE DELIVERY PASS + derivation binding both directions** — the "summary generated from rows" fix the qty_role and keep-the-noun rows have both been queued for. |
| **deference without verification** | 40 | **NEW at R40.** A challenged finding was conceded BEFORE measuring; 700 documents then confirmed the original. Mirror image of asserting-without-checking, and more corrosive here: a reader who folds on challenge produces agreement rather than verification, which voids every ✓ and every grade. Trigger shape: a TRUE premise carrying an INFERRED conclusion. Fix: Card #16 — a challenge is a test order. |
| 41 | 2003021100046001 2003 | **B+** (self, login-prompted) | **narrative (7th)** — "the by-laws carry their community in the drafting": instance characterization, unanchored, mildest form yet but a repeat of the most-recorded class · **class-gloss-without-entry (2nd**, R37 class**)** — flagged the heter iska lexicon gap at delivery, then used the gloss anyway; flagging ≠ license · over-absolute cast ("the only person who signs" vs only party to execute the declaration) · limited-common status dropped from rows (restricted-use SF could read as fee SF) | fixes applied in the R41 entry · Lexicon: heter iska added · party-attribution ruling recorded |

| 42 | 2003030301266001 2003 | **B−** (self, login-prompted) | **unverified count** (Card #13 class, members 21/23/39 — "second sighting" without the grep; count proved right, which is irrelevant) · **narrative (8th)** — "Williamsburg" imported onto the instance one run after "Boro Park" was deleted for the same move · **recitals flattened in delivery** (mode-watch, the session's own assignment; delivery-wrong class) · **pre-bank crop skipped** (name-integrity 3rd: 21/37/42 = MISSING STRUCTURE) | grep run + count earned · banked text fixed · Card #15 gains MODES line · **Card #12 NAMES now requires crop FILES on disk** |

⚠ narrative class members updated: 10, 33, 34, 35, 37, 39, 41, 42 — eight.
⚠ name-integrity members: 21, 37, 42 — three → structure changed (crop
artifacts mandatory, Card #12).
⚠ count-class members: 21, 23, 39, 42 — four; 42's variant is UNVERIFIED
rather than fabricated (the grep would have confirmed it; it wasn't run).
The grep is the license, not the truth of the number.

| 43 | 2003031700843002 2003 | **B+** (self, login-prompted) | **class-on-instance ("ground leases") — reached the DATA TABLE** (R25 class) · relationship-implying coinage ("couple-addressed") while the documented basis (shared address READ + relatives checkbox) went unused · **lexicon-recall 3rd (37, 41, 43) = MISSING STRUCTURE** — merger-of-estates glossed with no entry · "by mistake" cause-claim on a process defect (narrative, mild) | fixes in the R43 entry · Lexicon: merger of estates added · **Card #12 SOURCES sweep now runs over the DELIVERED text** · ruling queued: declared-historical mode |

⚠ lexicon-recall members: 37, 41, 43 — three → structure changed (the
SOURCES sweep covers the verdict's own prose, Card #12).
⚠ HELD-pattern worth keeping: r43 ran the crop pass proactively under
the new artifact rule and it settled a cite; the foreign-page defect
was caught by COUNT ARITHMETIC (11+1+1≠14) — arithmetic as tripwire.

| 44 | 2003030601377001 2003 | **B+** (self, login-prompted) | **numeric overstatement in prose** ("months" for a ~5-week derived interval — altered-value genus, low stakes) · **recital flattened in delivery, Card #15 MODES repeat ONE RUN after minting** (r42, r44 — double) | fixes in the R44 entry · two-source draw ruling · IDENTITY/ASBUILT boundary note |

⚠ MODES-flattening members: 42 (×2), 44 — the delivery layer keeps
stating declarant recitals as fact while the record holds them as
observes. Card #15 MODES exists; it did not fire at compose. If a
third run repeats it, the structural cure is the derivation-binding
check (prose sentence sources to an observes row ⇒ the sentence must
carry attribution) — flag it then, not another rule.
⚠ Numeric/derived-value precision: first prose instance at 44 (r39's
altered terms were in the table). Watch as a class: derived intervals
and multiples get re-computed at compose, not recalled.

| 45 | FT_1000000284200 1989 | **B** (self, login-prompted) | **unverified counts ("21 entries", "six tax figures") — COUNT CLASS 5th MEMBER (21, 23, 39, 42, 45)**, both wrong; honest form was the enumeration ("A–O plus related documents") · **single-look misread, 4th member (22, 33, 35, 45)**: $165M/$175M uttered in-turn from one 120dpi look at HANDWRITTEN fills; crops + Exhibit B's own arithmetic corrected to $163M/$173M pre-bank · Anderson handwritten name banked without a crop file (against the r42 structure; crop taken at fix, name confirmed) · control-as-ownership ("owned by … the Taubman organization") + gloss past the entity name | fixes in the R45 entry · crop_anderson on disk · Card #13 extended: counts of document contents need the count run, else write the enumeration |

⚠ COUNT CLASS AT FIVE (21, 23, 39, 42, 45) — Card #13 exists and did
not fire because these counts came from a mental tally of a LIST I was
reading, not a corpus query; the rule's word-scan shape ("N of X")
matches, so the failure is at compose. STRUCTURE PER THE FIRING LAW:
the honest default is now the ENUMERATION FORM — name the range or the
members, never a cardinal, unless a run-in-action produced the number.
A cardinal in delivered prose without a logged count command is a
defect per se, right or wrong.
⚠ single-look members: 22, 33, 35, 45 — the 45 form is new: HANDWRITTEN
fills on film. Rule sharpened in the entry: handwritten dollar figures
get the 400dpi crop BEFORE being uttered anywhere, in-turn speech
included (R40-3: in-turn statements are deliveries).
⚠ name-artifact (r42 structure) first REPEAT: the structure held for
r43/r44 and lapsed on a 65-page read. Watch: long reads erode
checklist passes — the crop pass belongs to the PAGE visit, not the
end-of-read sweep.
HELD at 45: value-crop pass caught the $2M misread pre-bank and settled
it by TWO routes (crops + schedule arithmetic); lot-merger stayed
labeled INFERRED with three named witnesses; L-3 held at chain scale
(no phantom 1919 event in chronology); G-022 to the dollar.

| 46 | 2003041400735009 2003 | **B−** (self, login-prompted) | **narrative import 9th (10,33,34,35,37,39,41,42) — EXACT r42 SHAPE REPEATED**: "Prospect Heights" + "landlord ... family firm" in the anybody test · **tier flattened at delivery — the PRE-NAMED derivation-binding case fired**: Canyon-Johnson notice-party (event test, correct) delivered as "money partner" fact (anybody test) · **count-per-se broken ONE RUN after minting, count class 6th (21,23,39,42,45)**: "six-course" for a five-course exhibit, uncounted and wrong · **validation claimed never run**: "courses close" asserted under self-validations; closure not computable from text · mild characterization residue | fixes in the R46 entry · Card #15 derivation binding ENACTED (all layers incl. anybody test) · format ruling recorded (grade-and-why two-block shape) |

⚠ STRUCTURE ENACTED at 46 (the pre-named cure): Card #15 now runs a
DERIVATION-BINDING sweep over EVERY delivery layer — each prose
sentence that sources to an observes/INFERRED row must carry its
attribution IN THAT SENTENCE, the anybody test explicitly included.
The r42/r44/r46 flattenings all died at the last-written, plainest
layer; the sweep runs there LAST, not first.
⚠ NARRATIVE CLASS AT NINE and repeating its own FIXED instances
(Williamsburg→Prospect Heights is the same import, same slot in the
same sentence shape: locating the deal for the reader). Structural
observation: the anybody test's OPENING SENTENCE is the recurring
host — it wants geography and cast color. Cure candidate if it
recurs: the opening sentence may name only borough + streets READ
from the record; neighborhood names are banned tokens at compose.
⚠ Count class at SIX — the per-se rule (r45) did not survive its
first run. The rule fired at BANK time but the defect happened
IN-TURN. Extension: the enumeration-not-cardinal default applies to
in-turn speech; saying a number aloud mid-read requires the same
license as banking it.
HELD at 46: crop-before-utter clean first outing (four crops, no
handwritten value/name uttered pre-crop); three record defects
caught (blank ack, Worth/North, wrong-county recital); the sealed
two-source draw exercised ENVELOPE-as-drawn-event on the first try;
RETT and page arithmetic run and exact.

| 47 | 2003020600526003 2002/03 | **C+** (self B → B− user-caught → C+ LOGIN-AMENDED same day) | **DELIVERED DATA TABLE HELD NO ACTOR-CLAIMS — party ruling violated at the table** (officers/incorporator/specimen-signatures lived only in prose + WHY; login: "details in the why completely skipped in the tests") · **WHY asserted claims the table never banked** (join keys, DOB bridge, denominator — the last also wrong-tier) · **self-grade audited words, never layer-consistency** · "wanted to" card-listed trigger in anybody opening · "its bank" relationship flat — derivation-binding lapse one run after enactment · hybrid mode label improvised instead of queued (P-3; ruling now queued: mode of certification instruments, r37+r47) · USER-CAUGHT "divides into 15,000 shares" for an authorized-ceiling fact | corrected entry carries roster in row 1 + authorized-vs-issued tier · **STRUCTURE: Card #15 WHY-BINDING enacted + DOWNWARD extended to ALL prose layers** |

⚠ NEW CLASS OPENED at 47: LAYER-CONSISTENCY (the delivery layers
disagree about what the extraction contains). Distinct from
MODES-flattening (a tier dropped) — here whole FACTS existed in
commentary layers while the evidence layer was empty. The enacted
cure is mechanical (WHY-BIND walk-back); watch whether it fires.
⚠ Tier-failure cluster in ONE run: "its bank" · "wanted to" ·
"divides into 15,000" — three small-word failures, all in plain
prose. The pattern across 42/44/45/46/47: precision dies at the
LAST-WRITTEN, PLAINEST layer. Every enacted sweep now runs on the
anybody test + WHY LAST, after they are drafted, not before.
⚠ GRADE-PROCESS note: the self-grade has now been amended upward in
severity twice by the login in two runs (r46 format, r47 substance).
The checklist audits sentences; the login audits the DELIVERABLE.
Add to the grading checklist: (5) layer-consistency walk (table ⊇
prose ⊇ WHY), run BEFORE grading the words.
HELD at 47: the reading itself was clean (13/13, no imports, counts
enumerated, Basch double-role caught, Kanemiller unresolved, no-human-
for-lender stated, taxes-zero earned); first Bronx run; CERTIFICATE
shelf opened and decoded as the authority layer.
The trigger list + Card #4 catch its phrase-shaped and scale-shaped
forms; R41's form was a CHARACTERIZATION OF THE DRAFTING ("their
community") — ordinary words again. Watch the shape: any sentence that
says what kind of people/party produced the document, rather than what
the document says. Structural cure remains the generated summary.
⚠ lexicon-recall class members: 37, 41 — two. Second shape differs:
R37 recalled with no entry; R41 flagged the gap and used the gloss
anyway. The pre-bank SOURCES check must fire on the DELIVERY too
(Card #15 pass), not only the record.
