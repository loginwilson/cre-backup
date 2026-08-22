# Full contacts across the eras — the three sources, measured

Target record, per party, per project: **name · company · phone · email · mailing.**
Not a name.

---

## THE HANDOVER IS 2021, NOT 2016

`w9ak-ipjd`'s min filing date is 2016-08-04, which is misleading — those are
pilot filings. Scope-bearing projects filed, by system:

    2016-2018   NOW   0-1%
    2019        NOW    25%
    2020        NOW    12%
    2021        NOW    68%   <- crossover
    2022        NOW    81%
    2023        NOW    95%
    2024-2026   NOW  97-98%

**BIS carries the real volume through 2021** and is a trickle by 2023 (492 →
269 → 267 projects). Any era boundary drawn at 2016 mis-assigns five years of
filings to a system that was barely in use.

---

## THE THREE SOURCES, AND WHAT EACH ACTUALLY YIELDS

| | era | name | company | phone | email | mailing |
|---|---|---|---|---|---|---|
| **1 · structured feeds** | 1989-2013 owner | ✓ | ✓ | **91.7%** | — | **93.5%** |
| | all eras contractor | ✓ | 99.6% | **99.6%** | — | — |
| | NOW applicant | ✓ | 99.6% | — | — | **97.3%** |
| | NOW filing rep | ✓ | 54% | — | — | 78% |
| **2 · BIS documents** | 1990-2021 | ✓ | ✓ | ✓ | **✓** | ✓ |
| **3 · DOB NOW** | 2021-present | **99.9%** | 93.7% | — | — | — |

**⚠ Email exists in no DOB feed, in any era.** Every email this project has
produced — `j.lewis@vorea.com`, `BSRIVASTAVA@ILARCH.COM`,
`TDIMATTEI@VITACCO.COM` — came out of a scanned PW1. Email is document-only,
permanently.

### The three sources fail in three different ways

- **Structured feeds** — complete and free, but the owner-phone column *ends
  2013-04-24* and nothing replaces it. `ipu4-2q9a` has owner address columns
  at **2.3% fill**; not a fallback.
- **BIS documents** — the only complete source, and **gated**: Akamai returns
  403 after roughly five folder requests. Hand-paced, not scriptable.
- **DOB NOW** — not gated, **absent**. Crop-proved: `Plans/Work (PW1) → Owner
  Information` carries Owner Type, First/Middle/Last Name, Title, Business
  Name — and **no address, phone or email field exists in the schema**, while
  Applicant and Filing Rep in the same panel both get full business addresses.
  `Statements & Signatures` is ten occupancy/rent questions, not a §26.

**So BIS is slow; DOB NOW is impossible from the page.** Different problems,
different remedies.

---

## ★ THE SQUEEZE, DATED

    owner phone in the feeds ends    2013-04-24
    DOB NOW takes over               2021

    1989 ─────── 2013 ─────── 2021 ─────── now
      feeds+docs    docs only    docs only, and the
                                 documents are thin

**2013-2021**: documents exist (BIS era) but no structured owner phone.
**2021+**: neither. DOB NOW filings carry few documents and they are
frequently image-only with no OCR text layer.

---

## BACK-RESOLUTION — REAL, AND PARTIAL

Take the owner **name** from the modern record (DOB NOW publishes it at 99.9%)
and look it up in the 1989-2013 contact set (91,075 people and 51,188 entities
that have a usable phone).

    era filed     projects    name hit   entity hit   either
    <=2013         191,898      80.8%        25.8%    82.2%
    2014-2020       73,598      35.1%         6.7%    37.8%
    2021+           50,894      24.5%         5.1%    27.4%

**27.4% of the modern cohort resolves.** ~37,000 projects filed since 2021
have an owner who never appears in the historical contact set at all — new
people, new entities. For those the document is the only route.

### ★ THE PERSON IS ~5× MORE DURABLE THAN THE ENTITY

24.5% name hit vs 5.1% entity hit on the 2021+ cohort. SPEs are minted fresh
per deal and never recur; the human who signs them recurs across many. This is
why matching on the **PW1 name** works and matching on the LLC does not — and
why the party registry must be keyed on people, with entities as edges.

Confirmed twice by hand in this project:

    Peter Papamichael   50TH & 5TH LIC LLC (2021)  ->  VOREA HOLDINGS (2012)
                        516-805-1584 · 184 North 8th St · j.lewis@vorea.com
    Hale Everets        TWO TREES (2026)           ->  GREEN STAR BUILDERS (pre-2013)
                        718-222-2503 · 45 Main Street, Brooklyn 11201

Both times the modern record gave the name and the historical record gave the
contact. Neither entity matched; both people did.

---

## WHAT THIS MEANS OPERATIONALLY

1. **Contractor contact is solved everywhere** — permittee phone is 99.6-100%
   across both permit feeds, all eras.
2. **Applicant and filing-rep mailing are solved for the DOB NOW era**
   (97.3% / 78%), name and company everywhere.
3. **Owner contact is solved 1989-2013**, and after that is a per-project
   document read — 27.4% of which can be shortcut by name back-resolution.
4. **Email is never solved by feeds.** If email matters, it is a document read,
   full stop.

⚠ Do not describe owner coverage as a single number. It is 91.7% before
2013-04-24 and a document-fetch problem after it.
