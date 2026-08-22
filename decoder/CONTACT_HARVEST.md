# Harvesting the contact record from job-folder documents

The target record, per party, per job:

    name · company · phone · email · mailing address
    + role · role-in-this-job · job · scancode · filed date · citation

Engine: `folder_contacts.js` (paste into an established BIS session).

---

## PROVEN: a whole folder parses

Job **421807520** (DM, Queens block 17 lot 1), swept 2026-08-07:

    folder documents        24
    with a text layer       24   (100% — all SC-era paper scans)
    no text layer            0
    contact records         16

Every document in the folder was fetched, inflated and parsed in memory. Nothing
written to disk. **The mechanism works end to end.**

---

## ⚠ TWO PARSER BUGS — AND THE SECOND IS THE DANGEROUS KIND

### 1. PDF string escapes break every label anchor containing a paren

PDF string literals keep their backslash escapes, so a literal `(` in the form
arrives as `\(`. The OCR text actually reads:

    Name\(pleaseprint\):PeterPapamichaelDgBusinessName/Agency:...

An anchor written `/Name\(pleaseprint\)/` matches **nothing**. Fix: unescape
`\( \) \\` when pulling the string literals.

### 2. ★ THE SWEEP REPORTED SUCCESS AND RETURNED ZERO OWNERS

With bug 1 live, the run printed:

    total 24 · read 24 · noText 0 · records 16      ← looks perfect
    owners: []                                     ← the entire point, missing

The professional blocks (§2/§3) matched fine because their labels have no
parens, so **16 records came back and the run looked healthy.** Only an
explicit `filter(role==='OWNER')` exposed it.

This is the failure mode already recorded in `feedback_bkrea_scale_failure`:
*one lot is verified by looking; population is verified by a summary line I
wrote myself.* A record count is not a coverage check. **Every sweep must
print per-role denominators — owners found / folders with a PW1 — never a
bare total.**

### 3. Despaced OCR has no word delimiters, so email matches run away

    archiprogroup.comanyissuesDEPT.BLDGS.421807520JobNumberBuildings...
    aol.cometheinfarmatlanprovidedhereinistrueandcomplete
    yahoo.comChooseone

Bound both sides and cap the TLD. Even bounded, **the local part is unreliable**
— it is preceded by ordinary prose (`...or email` + `eugene@...`). The
**domain is the trustworthy half**; the local part is a candidate to be
confirmed from the raster crop. `j.lewis@vorea.com` behaved exactly this way:
OCR yielded only `ea.com`; the crop gave the rest.

⚠ Which means the domain — the "real company" signal — survives OCR, and the
person's actual address usually does not.

---

## WHAT THE OTHER 23 DOCUMENTS ARE WORTH

Sweeping the whole folder (not just PW1) is right, but the yield is lopsided.
On job 421807520 the non-PW1 documents produced contacts for:

| document | party reached |
|---|---|
| BOROUGH INTAKE FORM ×2 | filing rep — `eugene@archiprogroup.com` · 646-616-7524 |
| SRO MD ANTI-HARASSMENT | applicant — `r.aristilde@yahoo.com`, AGE Engineering, 475 Lake Pointe Dr, Middle Island NY |
| TAP LETTER (DEP) | DEP contact + `Anastasios Gerorgelis` |
| ASBESTOS ACP5 | investigator |
| LETTERS — SUPPORTING | `allborough@aol.com` · BASMAN LEONARD |
| — | `cltgrp.com`, `megagroup.nyc` — contractor domains |

**No non-PW1 document in the folder carried the owner.** Consistent with the
17-document sweep of job 421807511. The other documents widen the *professional*
layer — contractors, expeditors, consultants, DEP — which is real value, but
**the owner is a PW1 §26 fact and nothing else reaches it.**

---

## CROSSING BY DATE — OWNER IN A GIVEN ERA

The folder gives contacts; the *job* gives the date; the pairing gives the era.

    for each parcel:
      for each SCOPE-BEARING job folder (BIS doc 01 NB/A1/A2/A3/DM, NOW New Building):
        owner_record  <- PW1 §26 of the INITIAL filing (PAA = No)
        re-read §26   <- on any PAA whose "Description of Amendment" names
                         §26 or "OWNER SIGNATORY"   (see NARRATIVE_280KENT.md)
        professionals <- sweep ALL documents in the folder
        stamp every record with the filing date -> owner-at-date
      segment on normalised entity -> ownership spells

Filters that are not optional (`JOB_OWNER_MODEL.md`):
trade and tenant filings put **themselves** in the owner field; entity spelling
fragments one owner into several; `"Not Applicable"` is a literal string on
4.8% of DOB NOW rows.

---

## REACH, BY ERA — MEASURED

| era | owner name | owner phone | owner mailing |
|---|---|---|---|
| **1989 – 2013-04** | yes | **91.3%** (`bty7-2jhb`, 2.43M rows) | 93.5% |
| **2013 – ~2022** | yes | feed: **no column exists**; document: PW1 §26 if the scan is `SC` | same |
| **DOB NOW era** | 99.9% (`owner_first_name`) | **nowhere** — the fields are not in the schema | **nowhere** |

`ipu4-2q9a` has owner house/street/zip columns but they are **2.3% filled**
(90,427 of 3,989,822) — not a fallback.

⚠ **The unmeasured number that decides everything post-2013 is the `SC` vs `ES`
mix.** `SC` scans carry a full OCR layer and yield §26; `ES` scans carry only a
typed overlay and usually do not.

## ⚠⚠ THE MEASUREMENT WAS ATTEMPTED AND IS BLOCKED

2026-08-07. Stratified sample of 78 scope-bearing jobs, 3 per year 2000-2025,
folder listings fetched at 350 ms spacing from an established session.

**BIS returns `403 Access Denied` from the Akamai edge after roughly five
folder requests.** 76 of 78 came back blocked:

    HTTP 403 · "You don't have permission to access
    /bisweb/JobsQueryByNumberServlet" · errors.edgesuite.net

Folder enumeration is a **hand-paced, one-job-at-a-time** capability. It is not
scriptable across a sample, and I am not going to defeat the edge control to
make it one. **This ratio has to come from another route** — a bulk/records
channel, or accumulating folders as a by-product of normal per-parcel work.

### ★ AND THE FAILURE LOOKED LIKE DATA

The sweep classified every 403 as "job has no Virtual Job Folder", because the
`Access Denied` page simply has no such link. Mid-run it read:

    54 processed · 49 "nofolder" · 0 errors · 0 queued

**A clean-looking 91% "no folder" rate that was entirely edge blocks.** Had I
reported it, it would have said "B-Scan coverage collapses before ~2015" — a
confident, specific, completely fabricated finding. The check that caught it
was fetching one "nofolder" job by hand and reading the HTTP status.

⚠ **Any fetch loop must record the HTTP status and treat non-200 as a distinct
outcome from an empty result.** A parser that only asks "did I find the thing"
converts every block into a negative observation.

### AND THE ONE DATA POINT CONTRADICTS THE SC/ES THEORY

Two folders survived, both filed **2001**:

    2001  401378004  docs=3  PW1: SC 0 / ES 0   all 3 scans ES
    2001  401292061  docs=2  PW1: SC 0 / ES 1   both scans ES

`ES` on a 2001 filing. eFiling did not exist in 2001, so **`ES` cannot mean
"e-filed submission"** — it more likely denotes the ingest/scanning system,
and a 2001 job can be scanned into it decades later (the folder's `DATE
SCANNED` is independent of the filing date).

n=2, so this is a flag not a finding — but it is evidence against the clean
"`SC` = paper era / `ES` = eFiling era" story asserted in `PW1_SECTION26.md`.
**Treat that framing as an untested hypothesis.** What is directly observed and
still holds: *some* scans carry a full OCR text layer and some carry only a
typed overlay; the prefix correlated with it on the handful examined; the
causal story does not survive n=2.
