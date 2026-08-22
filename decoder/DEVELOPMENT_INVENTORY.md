# The development inventory — located and sized

Measured 2026-08-06 over the full spine (1,175,952 parcels). Deduped.

## THE POPULATION

    parcels with >=1 in-scope development event   226,685 / 1,175,952  (19.28%)
        conversion   128,934      new_build    91,793
        enlargement   58,757      demolition   36,502
        more than one event type                 76,478

Four parcels in five have never had a development event. **That is the document
budget: 80.7% of the city never earns a fetch.**

## THE 2008 WALL — where the documents stop

    has a 2008+ event  -> DOCUMENTS AVAILABLE     120,192   53.0%
    1989-2007 only     -> index only, no scan     106,229   46.9%
    undated                                           264    0.1%

    by event type, bucketed on the LATEST event of that type
                        2008+     1989-2007    pre-1989
    new_build          41,612        49,857         199
    conversion         71,711        57,072          32
    enlargement        31,975        26,709          23
    demolition         20,453        16,018          18

★ **More new buildings are pre-2008 than post** (49,857 vs 41,612). The era with
no openable document holds the larger share of the city's ground-up development.

## THE PW1-REACHABLE JOB INVENTORY

    BIS scoped originals, all years                422,294
      filed 2000-2007   NO scanned document        230,542   54.6%
      filed 2008+       B-Scan era                 191,748   45.4%
    DOB NOW scoped jobs (all 2016+, portal)         49,616
    ------------------------------------------------------------
    PW1-REACHABLE JOBS                             241,364

BIS by filing year (scoped originals) — note the collapse as work moves to NOW:

    2000 26,413  2001 29,866  2002 28,357  2003 29,206  2004 31,992
    2005 32,191  2006 29,771  2007 22,746 | 2008 17,876  2009 14,497
    2010 12,328  2011 11,795  2012 12,372  2013 13,719  2014 14,773
    2015 14,081  2016 15,743  2017 15,127  2018 14,679  2019 13,052
    2020 12,270  2021  5,578  2022  2,692  2023 492  2024 269  2025 267

---

# ★★ THE CONTACT LAYER IS NOT DOCUMENT-ONLY — A CORRECTION

Earlier in this decoder I recorded that "the developer's address is published
NOWHERE in DOB structured data." That was measured on `ic3t-wcy2`
(`owner_s_house_number`: 25 rows of 318,869), `w9ak-ipjd` (no column) and
`rbx6-tga4` (0 of 979,705). **It is false for `bty7-2jhb`, which nobody was
reading.**

Scoped cohort (DM/NB/A1), **719,368 rows, 1989-2013**:

    owner_s_last_name                694,461   96.5%
    owner_s_house (number)           694,421   96.5%
    owner street name                694,421   96.5%
    owner zip                        692,863   96.3%
    FULL OWNER POSTAL                692,863   96.3%
    OWNER PHONE                      680,472   94.6%
    owner_s_business_name            645,381   89.7%
    permittee phone                  719,237  100.0%

**Verified it is genuinely the owner, not a copy of the permittee:** owner phone
equals permittee phone on only **113,897 of 680,472 (16.7%)** — and those are
owner-builders, where the permittee field reads "N/A". The other 83.3% are
distinct parties with distinct numbers. Sampled rows carry real names with full
mailing addresses and phones.

## So the contact layer by era

| era | developer name | mailing address | phone | source | document? |
|---|---|---|---|---|---|
| pre-1989 | on the I-card | — | — | HPD I-card | **yes** (residential only) |
| **1989-2013** | **96.5%** | **96.3%** | **94.6%** | **`bty7-2jhb`** | **NO — free feed** |
| 2013-2016 | name only | — | — | `ipu4-2q9a` | PW1 needed |
| 2008+ | PW1 §26 | PW1 §26 | PW1 §26 | B-Scan | yes |
| 2016+ | PW1 §26 | PW1 §26 | PW1 §26 | NOW portal | yes |

★ **The 46.9% of parcels that are "index only" for DOCUMENTS are the BEST
covered for CONTACT** — 1989-2013 is exactly the window `bty7-2jhb` spans, at
~95%. The two gaps invert. The genuinely thin window for contact is **2013-2016**,
where the historical feed has ended and only the PW1 answers.

This is the chain Login stated: *deed -> entity · mortgage -> the name under the
entity · PW1 -> contact of the name · research -> context.* For 1989-2013 the
third rung is already a free feed. For everything after, it is the document.

---

# WHAT REMAINS TO DO

1. **Resolve the off-spine rows** — permit 60,341 · BIS 26,780 · NOW 1,727.
   Retired BBLs; run them through the DOF alteration book before anything is
   called complete.
2. **Harvest `bty7-2jhb` owner contacts** for the 1989-2013 cohort. Free, no
   document, ~95% fill, 719,368 rows. This is the largest single contact
   acquisition available and it needs no permission from anyone.
3. **Then open PW1s**, ranked, for the 241,364-job reachable inventory —
   originals only, latest scanned round only, last page first (§26 is page 5
   of 5). Prioritise 2013+ where no feed carries the contact.
4. ⚠ **Nothing above is a fact yet.** 0 `facts.Fact` rows written. Every number
   here is an index measurement, which under `RULE_DOCUMENTS_NOT_INDEXES` is a
   finding aid. Facts begin when the PW1s are read.
