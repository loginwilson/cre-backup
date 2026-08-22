"""DOB — job filings, permits and certificates of occupancy, per parcel.

The complement to ACRIS, and the source that carries the STAGE TRANSITIONS the
parcel lifecycle needs:

    filing              -> pre-development
    work permit issued  -> construction   (FO/EA are irreversible starts;
                                           FN/SF/EQ/CH are only mobilisation)
    TCO                 -> temporary operation  (renewals = velocity;
                                           renewals with no sign-off = stalled)
    final CO            -> operation

⚠ THE BLOCK-FORMAT TRAP, which nearly put a false "no filing" on the record.
DOB stores `block` UNPADDED ('1446'); Socrata's PLUTO and ACRIS legals pad to
five ('01446'). A padded block returns ZERO rows and reads exactly like "this
parcel has never been filed on". Every query here therefore:
  * uses the unpadded form, and
  * runs a CONTROL query against a block known to have filings, so an empty
    result is only ever reported after the query itself has been shown to work.
Absence is a finding; an untested query is not.

⚠ And the rule that keeps the envelope honest (SOURCE_MAP_DOB.md): a recorded
instrument changes what MAY be built; a DOB filing only describes what IS being
built or CLAIMED. DOB floor area never enters `envelope_transferable`.
"""
import sys, pathlib
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk
import keys

BIS_JOBS = "ic3t-wcy2"       # 2.7M rows  — job application filings (legacy)
NOW_JOBS = "w9ak-ipjd"       # 939k rows  — DOB NOW Build filings (current)
PERMITS = "ipu4-2q9a"        # 4.0M rows  — permit issuance (BIS era)
HIST_PERMITS = "bty7-2jhb"   # 3.4M rows  — historical permits 1989-2013.
#   ★ THE ONLY DOB FEED THAT EVER PUBLISHED THE OWNER'S ADDRESS AND PHONE.
#   ipu4-2q9a has owner_s_house__/street/zip but NO owner phone column at all;
#   w9ak-ipjd has neither. So owner contact from structured data is a
#   1989-2013 capability only — after that it exists solely in PW1 §26.
NOW_PERMITS = "rbx6-tga4"    # 980k rows  — DOB NOW approved permits
CO = "bs8b-p36w"             # 143k rows  — certificates of occupancy (BIS)
CO_NOW = "pkdm-hqz6"         # 80k rows   — certificates of occupancy (NOW)
LICENCES = "t8hj-ruu2"       # 103k rows  — licensed professional register

# ⚠ THE KEY FORMAT IS A PROPERTY OF THE DATASET, NOT OF "DOB".
# Measured 2026-08-05 — four datasets, THREE different conventions:
#
#   ic3t-wcy2 BIS jobs   borough 'QUEENS'    block '01446' PADDED   lot '00009'
#   w9ak-ipjd NOW jobs   borough 'Manhattan' block '441' UNPADDED   lot '16'
#   ipu4-2q9a permits    borough 'BROOKLYN'  block '06861' PADDED   lot '00067'
#   bs8b-p36w CO         borough 'Bronx'     block '05141' PADDED   lot '00035'
#
# `block='1446'` returns ZERO rows against BIS; `block='01446'` returns five.
# A wrong format therefore reads exactly like "this parcel has never been filed
# on" — the failure this module's control query exists to prevent.
# (An earlier project note recorded the OPPOSITE rule — that DOB does not pad.
#  It was wrong for three of these four. Measure per dataset; never generalise
#  a key format from one table to an agency.)
BORO_NAME = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn",
             "4": "Queens", "5": "Staten Island"}
SPEC = {
    BIS_JOBS: {"boro": "upper", "pad_block": 5, "pad_lot": 5},
    NOW_JOBS: {"boro": "title", "pad_block": 0, "pad_lot": 0},
    PERMITS:  {"boro": "upper", "pad_block": 5, "pad_lot": 5},
    # ⚠ SIXTH CONVENTION, measured 2026-08-07. Two permit feeds from the same
    # agency disagree: ipu4-2q9a pads block/lot to 5, bty7-2jhb does NOT
    # ('BRONX', '3274', '4'). Keying the historical feed with the modern feed's
    # spec returns zero rows and looks like "this parcel has no permit history".
    HIST_PERMITS: {"boro": "upper", "pad_block": 0, "pad_lot": 0},
    CO:       {"boro": "title", "pad_block": 5, "pad_lot": 5},
    # measured 2026-08-06 — borough 'Manhattan', block '174', lot '7505'
    CO_NOW:   {"boro": "title", "pad_block": 0, "pad_lot": 0},
}

# ⚠ AND THE `bbl` COLUMN IS NOT A BBL ON BIS. Measured 2026-08-06 over all
# 2,715,848 rows of ic3t-wcy2:
#     exactly 10 chars (a real BBL)   1,802,213   66.4%
#     exactly  7 chars (a BIN)          884,315   32.6%
#     NULL                               29,320    1.1%
#     equal to bin__                    841,577   31.0%
# w9ak-ipjd, pkdm-hqz6 and bs8b-p36w all carry a real BBL (bbl = bin on 0 rows).
# So a decoder joining ic3t-wcy2 on `bbl` loses a third of the corpus WITHOUT
# ERROR — the rows do not fail to parse, they simply never match. Always build
# the key from borough/block/lot via keyparts(), never from the bbl column.
BIS_BBL_IS_UNRELIABLE = True

# job types that mark a real development, vs maintenance
DEV_JOB_TYPES = {"NB": "new building", "A1": "major alteration (use/egress/bulk)",
                 "DM": "demolition", "A2": "alteration", "A3": "minor alteration",
                 "SI": "subdivision improved", "SC": "subdivision condominium"}
# SI/SC are LINEAGE events — the DOB side of what DOF's alteration book records


# ═══════════════════════════════════════════════════════════════════════════
# ⚠ A ROW IS NOT A JOB. Measured 2026-08-06 — this invalidates every universe
# figure quoted from the workbooks, which are all row counts.
#
#   BIS  doc__ '01' is the original; '02'+ are amendments filed under the SAME
#        job number, and they RESTATE NOTHING: on NB amendment rows,
#        zoning_dist1 is present on 0 of 63,293 and proposed_zoning_sqft on
#        0 of 63,293. Counting fill over rows therefore manufactures a gap that
#        does not exist — see ENVELOPE_FILL below.
#          NB  199,888 rows -> 136,595 originals
#          A1  220,051 rows -> 182,274 originals
#        (job__, doc__) is NOT unique — 63,064 NB pairs repeat. `job_s1_no` is
#        the row key; `job__` is the job.
#
#   NOW  the suffix on job_filing_number is the FILING SEQUENCE, not noise:
#          -I  initial          555,340
#          -P  post-approval amendment (PAA)  256,369
#          -S  subsequent       119,719
#          -A/-Z/-B/-C/-Y/-D/-F  7,679      — 72 distinct suffixes in all
#        939,107 rows are 555,652 JOBS. The known trap said "strip -I1", but
#        -I1 is only 59.1% of rows; stripping that literal leaves 40.9%
#        unjoined. Split on the first '-' instead.
#
#   ★ AND THE PAA IS THE POINT, not an inconvenience: 48.2% of NOW New Building
#     jobs (4,548 of 9,432) carry at least one -P filing. On nearly half of all
#     new buildings the approved scope was amended afterwards, so the initial
#     filing's floor area is stale. A job read at -I1 only is wrong half the
#     time on exactly the cohort we care about.
# ═══════════════════════════════════════════════════════════════════════════

def now_base(job_filing_number):
    """'M00855935-P3' -> ('M00855935', 'P', 3). Splits on the FIRST dash."""
    base, _, suf = (job_filing_number or "").partition("-")
    letter = suf[:1].upper() if suf else ""
    try:
        seq = int(suf[1:]) if suf[1:] else 0
    except ValueError:
        seq = 0
    return base, letter, seq


# ═══════════════════════════════════════════════════════════════════════════
# SCOPE — Login 2026-08-06: "new build, conversion, and enlargement".
# Repairs are out. Every count below is JOBS, measured 2026-08-06.
# ═══════════════════════════════════════════════════════════════════════════
SCOPE_BIS = {
    "new_build":   "job_type='NB'",                       # 136,595 originals
    "conversion":  "job_type='A1'",                       # 182,274 originals
    # ⚠ ENLARGEMENT IS A FIELD, NOT A JOB TYPE, and it does NOT live where the
    # job-type vocabulary suggests. Of 95,630 originals with
    # enlargement_sq_footage > 0:  A1 68,915 · A2 25,793 · A3 918 · DM 2 · NB 2.
    # A2 is described as "no change to use, egress or occupancy" and reads like
    # maintenance — yet it carries 27% of all enlargements. Excluding A2 as
    # "small repairs" silently drops 25,793 envelope events.
    "enlargement": "enlargement_sq_footage > 0",          # 95,630 originals
}
SCOPE_NOW = {
    "new_build":  ("job_type in('New Building',"
                   "'ALT-CO - New Building with Existing Elements to Remain')"),
    "conversion":  "job_type in('Alteration CO','No Work')",
    # ⚠ NOW publishes NO enlargement column. The only signal is the free-text
    # job_description, which is a claim, not a quantity.
    "enlargement": "upper(job_description) like '%ENLARG%'",
}
# jobs: new_build 12,212 · conversion 29,267 · enlargement ~7,063 (text match)
# 44,589 scoped jobs of 555,652 — 8.0% of DOB NOW is in scope.


def keyparts(bbl, dataset):
    """(borough, block, lot) in the exact spelling THIS dataset uses."""
    boro, block, lot = keys.parts(bbl)
    sp = SPEC[dataset]
    name = BORO_NAME[str(boro)]
    return (name.upper() if sp["boro"] == "upper" else name,
            f"{block:0{sp['pad_block']}d}" if sp["pad_block"] else str(block),
            f"{lot:0{sp['pad_lot']}d}" if sp["pad_lot"] else str(lot))


def control_query_ok(dataset=BIS_JOBS):
    """SELF-CALIBRATING control: take a real row FROM THIS DATASET, rebuild its
    key with our own SPEC, and prove we can find it again.

    The first version used a fixed block (MN 1446) and reported FAIL for the CO
    dataset — but that only meant "no CO on that block", not "wrong format". A
    control must test the QUERY SHAPE, not the presence of a particular parcel,
    or it manufactures failures exactly where it is supposed to prevent them.

    Absence is a finding; an untested query is not.
    """
    sample = bulk.socrata(dataset, limit=1)
    if not sample:
        return False, f"{dataset}: dataset returned nothing at all"
    row = sample[0]
    boro, blk, lot = row.get("borough"), row.get("block"), row.get("lot")
    if not (boro and blk):
        return False, f"{dataset}: sample row has no borough/block ({list(row)[:6]})"
    found = bulk.socrata(dataset, where=f"borough='{boro}' and block='{blk}'", limit=5)
    # and check our SPEC reproduces that spelling from a canonical BBL
    inv = {v.upper(): k for k, v in BORO_NAME.items()}
    bnum = inv.get(str(boro).upper())
    spec_ok = None
    if bnum and str(blk).isdigit() and str(lot or "0").isdigit():
        bbl = keys.bbl(bnum, int(blk), int(lot or 0))
        spec_ok = keyparts(bbl, dataset) == (boro, blk, lot)
    return bool(found), (f"{dataset}: sample borough={boro!r} block={blk!r} lot={lot!r} "
                         f"-> {len(found)} rows; SPEC reproduces the spelling: {spec_ok}")


def jobs_for(bbls, dataset=BIS_JOBS, by_lot=True):
    """Filings for a set of BBLs, in the dataset's own key spelling."""
    from collections import defaultdict
    groups = defaultdict(set)
    for b in bbls:
        boro, blk, lot = keyparts(b, dataset)
        groups[boro].add((blk, lot))
    out = []
    for boro, pairs in groups.items():
        blocks = sorted({blk for blk, _ in pairs})
        for i in range(0, len(blocks), bulk.IN_CLAUSE_MAX):
            part = blocks[i:i + bulk.IN_CLAUSE_MAX]
            joined = ",".join(f"'{x}'" for x in part)
            got = bulk.socrata(dataset, where=f"borough='{boro}' and block in({joined})")
            out.extend(got)
    if by_lot:
        wanted = {(bo, bl, lo) for b in bbls for bo, bl, lo in [keyparts(b, dataset)]}
        out = [r for r in out
               if (r.get("borough"), r.get("block"), r.get("lot")) in wanted]
    return out


def stage_of(job):
    """Map a filing to a lifecycle stage.

    Statuses are matched MOST SPECIFIC FIRST, because DOB's vocabulary overlaps:
    "PERMIT ENTIRE" and "PERMIT ISSUED" are both construction, but "SIGNED OFF"
    outranks either. An unrecognised status is returned AS-IS with an `unmapped:`
    prefix rather than forced into a bucket — a mis-bucketed stage is invisible,
    an unmapped one shows up in the counts and gets fixed.

    Mapped from the statuses actually observed on our parcels 2026-08-05.
    """
    st = (job.get("job_status_descrp") or job.get("filing_status") or "").upper()
    if not st:
        return "unknown"
    # ⚠ CLEARED comes FIRST, because "FULL DEMOLITION SIGNED-OFF" contains
    # "SIGNED-OFF" and would otherwise read as `operation`. The work finished,
    # but what finished was REMOVAL: the improvement is gone and the site is land
    # again. In the parcel lifecycle that is the loop CLOSING — an operating
    # building returning to pre-development — not a site entering operation.
    # Bucketing it as `operation` would make a cleared site look occupied.
    if "DEMOLITION" in st and ("SIGNED" in st or "COMPLETE" in st):
        return "cleared"
    # operation — the work is finished and legal occupancy exists.
    # PA/TA Certificate of Operation is a Place of Assembly certificate: an
    # OCCUPANCY permission, so it belongs here.
    for k in ("SIGNED OFF", "COMPLETE", "LOC ISSUED", "C OF O ISSUED",
              "CERTIFICATE OF OPERATION"):
        if k in st:
            return "operation"
    # construction — a permit exists, so work may lawfully proceed
    for k in ("PERMIT ENTIRE", "PERMIT ISSUED", "PARTIAL PERMIT", "IN PROCESS"):
        if k in st:
            return "construction"
    # pre-development — filed, under review, or approved but not yet permitted
    for k in ("APPLICATION PROCESSED", "PLAN EXAM", "APPROVED", "FILED",
              "PENDING", "OBJECTIONS", "PRE-FILING", "ASSIGNED"):
        if k in st:
            return "pre_development"
    for k in ("WITHDRAWN", "DISAPPROVED", "REVOKED", "SUSPENDED"):
        if k in st:
            return "abandoned"
    return f"unmapped:{st[:40]}"


# ═══════════════════════════════════════════════════════════════════════════
# ENVELOPE_FILL — where the structured feed states an envelope, and where only
# the document does. Measured 2026-08-06 on ORIGINALS (doc__='01').
#
# The brief this decoder started from said "on NB+A1, proposed_zoning_sqft is
# non-zero on only 32.9% and zoning_dist1 is missing on 24%". Both numbers
# reproduce exactly — and both are artefacts of counting amendment rows.
# On originals:
#
#     zoning_dist1                    136,592 / 136,595   100.0%
#     proposed_height                 136,595 / 136,595   100.0%
#     total_construction_floor_area   136,587 / 136,595   100.0%
#     proposed_zoning_sqft             48,754 / 136,595    35.7%   <- the real gap
#
# And that one real gap is an ERA, not a field. proposed_zoning_sqft by filing
# year on NB originals:
#     2000-2007    1,706 / 88,892    1.9%   <- the field was not captured
#     2008         4,241 /  4,895   86.6%   <- it switches on mid-year
#     2009-2023   42,807 / 42,808  100.0%   <- always present thereafter
#
# So the BIS document requirement is a single dated block: NB originals filed
# 2000-2007. Everything from 2009 states its own zoning floor area.
#
# ⚠ street_frontage is effectively dead — 48 of 199,888 NB rows (0.02%);
#   6.2% across all BIS. The wide-street FAR condition in ZR 23-22 footnote 1
#   turns on frontage within 100 feet of a wide street, so DOB cannot supply
#   the input that footnote needs. That stays a ZD1/tax-map question.
#
# ⚠ AND DOB NOW HAS NO ZONING COLUMNS AT ALL — not sparse, ABSENT from the
#   schema. All 95 columns of w9ak-ipjd were checked against the dataset's own
#   metadata: no zoning_dist1, no proposed_zoning_sqft, no lot area, no FAR.
#   NOW carries total_construction_floor_area (100% on the scoped cohort), and
#   CONSTRUCTION floor area is not ZONING floor area — it does not net out the
#   exclusions the envelope turns on. It is not a substitute.
#
#   NOW is the current system: it passed BIS around 2021 and BIS NB collapses to
#   757 originals in 2021, 16 in 2022, 5 in 2023. So for every new building
#   filed since roughly 2021, the structured envelope gap is 100%.
ENVELOPE_FILL = {
    "bis_nb_originals": 136_595,
    "bis_nb_zoning_sqft_pre2008": (1_706, 88_892),
    "bis_nb_zoning_sqft_2009on": (42_807, 42_808),
    "now_zoning_columns": None,          # None = the columns do not exist
}


# ═══════════════════════════════════════════════════════════════════════════
# CONTACT LAYER — per ROLE, and per ERA. A name is not a contact, so each entry
# records what you can actually reach the party with. Measured 2026-08-06 on
# the scoped cohort.
#
#   ARCHITECT / ENGINEER (applicant of record)
#     NOW jobs   name 100% · business name 100% · street 99.9% · licence 100%
#     BIS jobs   name 100% · licence 100% · NO address
#     phone/email: NOT AVAILABLE from DOB at any fill rate. ⚠ The DOB licence
#     register t8hj-ruu2 has 20 licence types and NONE of them is architect or
#     engineer ("STATIONARY / PORTABLE ENGINEER" is a boiler operator). The
#     applicant is PE (50.5%) or RA (49.4%) — licensed by NY STATE. Joining
#     applicant_license to the register "resolves" 37.0% and every one of those
#     is a collision: 23.9% of register licence numbers are reused across types,
#     and the join returns a real phone belonging to a different person.
#     ⇒ architect phone/email is a DOCUMENT question (PW1) or a NYS Office of
#       the Professions question. Never the DOB register.
#
#   FILING REPRESENTATIVE (expeditor)
#     NOW jobs   name 79.2% · business 79.5% · FULL POSTAL 79.0%
#     BIS        no column at all — the role is invisible before DOB NOW
#     phone/email: FILING REPRESENTATIVE *is* a register type (7,863), but the
#     jobs feed publishes no filing-rep licence number, so the join is by NAME.
#
#   CONTRACTOR (permittee)
#     BIS permits  business name 99.6% · DIRECT PHONE 99.6% (3,972,960 of
#                  3,989,787) · licence 93.5%; 62.3% of NB permittee licences
#                  resolve as GENERAL CONTRACTOR in the register.
#     ⚠ NOW permits rbx6-tga4 DOES NOT NAME THE PERMITTEE. Its 46 columns carry
#       permittee_s_license_type and nothing else about them — no name, no
#       licence number, no phone. The contractor is identifiable in the BIS era
#       and anonymous in the NOW era. That is a regression, not an oversight to
#       code around.
#
#   OWNER / DEVELOPER
#     BIS jobs     business name 93.0% · address 25 rows of 318,869 (0.0%)
#     NOW jobs     owner_last_name 99.9% · business 86.3% · NO address column
#     NOW permits  owner_name 98.9% · business 95.9% · the owner_street_address,
#                  owner_city, owner_zip_code columns EXIST and are populated on
#                  0 of 979,705 rows.
#     ⇒ the developer's address is published NOWHERE in DOB structured data.
#       PW1 §26 is the only source, and the BIS web page truncates before it.
#       This is the one role for which the document is genuinely unavoidable.
CONTACT_SOURCES = {
    "architect":   {"name": NOW_JOBS, "postal": NOW_JOBS, "phone": None},
    "filing_rep":  {"name": NOW_JOBS, "postal": NOW_JOBS, "phone": LICENCES},
    "contractor":  {"name": PERMITS, "postal": None, "phone": PERMITS},
    "developer":   {"name": NOW_JOBS, "postal": None, "phone": None},
}
