"""DEVELOPMENTS — what has physically happened on this ground, 1914 -> today.

Chat 2. Scope: DEMOLITION · NEW BUILD · CONVERSION · ENLARGEMENT.
Decodes along the parcel spine (spine/spine.jsonl, 1,175,952 parcels).

THE ARCHITECTURE, and why it is split in two
    STRUCTURED layers pull WHOLESALE and join in memory. Never per-parcel API
    calls — at 1.18M parcels that is not a slow plan, it is an impossible one.
        bty7-2jhb  historical permits  1989-2013   2,428,526 rows
        ipu4-2q9a  permits             >=1992-2022 3,989,787
        ic3t-wcy2  BIS jobs            2000-2025   2,715,848
        w9ak-ipjd  DOB NOW             2016-now      939,107
        bs8b-p36w / pkdm-hqz6  CO                  143,061 + 80,082

    DOCUMENT layers are per-parcel web lookups and are WATCHLIST ONLY:
        HPD I-cards (1914)  ·  1940s + 1980s tax photos  ·  B-Scan job folders
        (2008)  ·  DOB NOW portal Zoning Information
    Each costs one page load. They answer questions no feed can, but they do not
    scale, and pretending otherwise is how a population job silently truncates.

⚠ EVERY DATASET SPELLS THE KEY DIFFERENTLY — five conventions measured so far.
   Use dob.keyparts(); control every query before reporting an absence.

⚠ A ROW IS NOT A JOB. BIS doc 01 is the original, 02+ amendments that restate
   nothing. DOB NOW splits one job across -I/-P/-S filings. Count jobs.
"""
import json, pathlib, sys
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk, dob, keys

SPINE = pathlib.Path(__file__).with_name("spine") / "spine.jsonl"

# ── SCOPE ────────────────────────────────────────────────────────────────────
# Four event classes. DM is carried because it SEGMENTS a site's history into
# development cycles and precedes new build — it is a signal, not an output
# development type.
NEW_BUILD, CONVERSION, ENLARGEMENT, DEMOLITION = "new_build", "conversion", "enlargement", "demolition"

BIS_SCOPE = {           # ic3t-wcy2 — originals only (doc__='01')
    NEW_BUILD:   "job_type='NB'",
    CONVERSION:  "job_type='A1'",
    # ⚠ enlargement is a FIELD, not a job type, and 27% of it is filed as A2 —
    # the type documented as "no change to use, egress or occupancy". Filtering
    # A2 out as maintenance drops 25,793 real envelope events.
    ENLARGEMENT: "enlargement_sq_footage > 0",
    DEMOLITION:  "job_type='DM'",
}
NOW_SCOPE = {           # w9ak-ipjd
    NEW_BUILD:   ("job_type in('New Building',"
                  "'ALT-CO - New Building with Existing Elements to Remain')"),
    CONVERSION:  "job_type in('Alteration CO','No Work')",
    ENLARGEMENT: "upper(job_description) like '%ENLARG%'",   # ⚠ text, not a quantity
    DEMOLITION:  "job_type='Full Demolition'",
}
# permits feeds carry job_type too, but no enlargement column — so pre-2000
# enlargement is UNDETECTABLE from the permit feeds and must be marked so.
PERMIT_SCOPE = {
    NEW_BUILD:  "job_type='NB'",
    CONVERSION: "job_type='A1'",
    DEMOLITION: "job_type='DM'",
}


# ═══════════════════════════════════════════════════════════════════════════
# ★ PW1 §26 — THE CONTACT DECODE. This is the whole point of entering documents.
#
# Login, 2026-08-06: "deed tells us entity, mortgage tells us the name under the
# entity, pw1 gives us contact of the name, and research on the contact gives
# us context."
#
# A real §26 block, as printed:
#
#     Name (please print):    BRUCE WEILL
#     Relationship to Owner:  AUTH. SIGNATORY
#     Business Name/Agency:   BUD SOUTH LLC
#     Street Address:         387 PARK AVENUE SOUTH
#     City: NEW YORK   State: NY   Zip: 10016
#     Telephone Number:       (212) 672-1000
#     E-Mail Address:         BRUCE.WEILL@TFCORNERSTONE.COM
#     Signature and Date:     [signed] 11/22/21
#
# ★★ THE E-MAIL DOMAIN IS THE DECODE.
#    `BUD SOUTH LLC` is a single-purpose entity and tells you nothing.
#    `@tfcornerstone.com` tells you the developer is TF CORNERSTONE.
#    The SPE is what the deed records; the domain is what the deed conceals.
#    Nothing in any structured feed carries this — no phone column, no e-mail
#    column, and owner address populated on 25 of 318,869 BIS originals.
#
# ⚠ `Relationship to Owner` IS THE ROLE and must never be dropped. The same
#    human appears as AUTH. SIGNATORY on one filing and MEMBER or PRESIDENT on
#    another; the role is what says whether they can bind the entity.
#    Observed values: OWNER · AUTH. SIGNATORY · MEMBER · PRESIDENT · MANAGING
#    MEMBER · AGENT · OFFICER · CONDO BOARD PRESIDENT · LESSEE.
# ═══════════════════════════════════════════════════════════════════════════

CONTACT_FIELDS = (
    "name",              # BRUCE WEILL — the HUMAN
    "role",              # AUTH. SIGNATORY — Relationship to Owner
    "entity",            # BUD SOUTH LLC — Business Name/Agency (the SPE)
    "street", "city", "state", "zip",
    "phone", "fax", "email",
    "signed_date",       # the jurat date; proves who was authorised WHEN
    "owner_type",        # Individual / Partnership / Corporation / NYCHA-HHC /
                         # Other Government / NYC Agency / Condo unit owner
)

# Free-mail domains reveal nothing about the operating company — never promote
# these to `real_company`.
GENERIC_MAIL = {"gmail.com", "yahoo.com", "aol.com", "hotmail.com", "outlook.com",
                "msn.com", "icloud.com", "me.com", "verizon.net", "att.net",
                "optonline.net", "earthlink.net", "comcast.net", "live.com",
                "mac.com", "protonmail.com", "mail.com", "nyc.rr.com"}


def real_company(email):
    """The operating company behind an SPE, from the e-mail domain.

    BRUCE.WEILL@TFCORNERSTONE.COM -> 'tfcornerstone.com'  (TF Cornerstone)
    Returns None for free mail, where the domain says nothing.
    """
    if not email or "@" not in str(email):
        return None
    dom = str(email).strip().lower().rsplit("@", 1)[-1]
    return None if dom in GENERIC_MAIL else dom


def contact_from_pw1(block):
    """Normalise one decoded §26 block. Every value keeps its page citation at
    the call site — this only shapes it.

    ⚠ A §26 with a name and no phone/e-mail is a PARTIAL, not a failure, and
    must be recorded as partial. On job 421843884 the rendering carried the name
    and dropped street/phone/e-mail entirely — which is exactly why the
    document, not the details page, is the source.
    """
    out = {k: (block.get(k) or None) for k in CONTACT_FIELDS}
    out["real_company"] = real_company(out.get("email"))
    out["reachable"] = bool(out.get("phone") or out.get("email"))
    out["complete"] = all(out.get(k) for k in
                          ("name", "role", "entity", "street", "phone", "email"))
    return out


def load_spine(path=SPINE, kinds=None):
    """The universe. Returns {bbl: row}. 1,175,952 parcels as built 2026-08-06."""
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if kinds and r.get("kind") not in kinds:
                continue
            out[r["bbl"]] = r
    return out


def _bbl_from(row, dataset):
    """Build the BBL from borough/block/lot in THIS dataset's spelling.

    ⚠ Never from a `bbl` column — ic3t-wcy2's holds a BIN on 32.6% of rows and
    fails to match without erroring.
    """
    boro, blk, lot = row.get("borough"), row.get("block"), row.get("lot")
    if not (boro and blk and lot):
        return None
    inv = {v.upper(): k for k, v in dob.BORO_NAME.items()}
    b = inv.get(str(boro).upper())
    if not b:
        return None
    try:
        return keys.bbl(b, int(blk), int(lot))
    except (ValueError, TypeError):
        return None


def pull(dataset, where, select, label):
    """One wholesale pull, reported with its denominator. Three outcomes."""
    try:
        rows = bulk.socrata(dataset, where=where, select=select)
        return {"status": "ok", "rows": rows, "n": len(rows), "label": label}
    except Exception as e:
        return {"status": "FAILED", "rows": [], "n": 0, "label": label,
                "error": f"{type(e).__name__}: {str(e)[:160]}"}


HIST = "bty7-2jhb"


# ── DEDUPE ───────────────────────────────────────────────────────────────────
# ⚠ TWO SEPARATE DOUBLE-COUNTS, BOTH MEASURED 2026-08-06 ON Queens 52/1.
#
# 1. WITHIN ipu4-2q9a. Job 400353620 appears TWICE — identical job, sequence,
#    type, subtype, status and BIN — differing ONLY in the date format
#    ('1993-03-03' vs '03/03/1993'). Citywide 88,238 rows (2.21%) are ISO-dated.
#    The published 3,989,787 is inflated by whatever share of those are dupes.
#
# 2. ACROSS bty7-2jhb AND ipu4-2q9a. The ladder reads as a handoff — historical
#    permits 1989-2013, then permits 1992-2022 — but they OVERLAP: both return
#    the same permits for the shared years. Summing the feeds double-counts
#    every permit issued in ~1992-2013.
#
# One identity serves both: a permit is (job, permit_type, permit_subtype,
# permit_sequence). Date is deliberately NOT in the key — it is the field that
# varies between the duplicates.

def norm_date(s):
    """Every date format DOB uses, to ISO. Returns '' when it cannot be parsed —
    never a half-parsed string.

    ⚠ THREE FORMATS, and the third broke the first version of this:
        '1993-03-03'              ISO
        '03/03/1993'              MM/DD/YYYY
        '07/09/25  9:41:42 AM'    MM/DD/YY + TIME   <- pkdm-hqz6 certificates
    Truncating to 10 chars and splitting on '/' turned the third into
    year='25  9:41' and rendered as '25  -07-09'. A date that is wrong but
    printable is worse than one that is absent, because it still sorts.
    """
    s = str(s or "").strip()
    if not s:
        return ""
    if "/" in s:
        head = s.split()[0]                      # drop any trailing time
        p = head.split("/")
        if len(p) != 3:
            return ""
        m, d, y = (x.strip() for x in p)
        if not (m.isdigit() and d.isdigit() and y.isdigit()):
            return ""
        if len(y) == 2:                          # 2-digit year: DOB's CO feed
            y = f"20{y}" if int(y) < 70 else f"19{y}"
        if len(y) != 4:
            return ""
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    s = s[:10]
    return s if len(s) == 10 and s[:4].isdigit() and s[4] == "-" else ""


def permit_key(r):
    """Cross-feed permit identity. Works on both permit datasets.

    ⚠ A SIXTH KEY CONVENTION, and it silently defeated the de-overlap on the
    first attempt. The two permit feeds pad the sequence differently:

        bty7-2jhb.permit_sequence     '1'  '2'        UNPADDED
        ipu4-2q9a.permit_sequence__   '01' '02' '03'  ZERO-PADDED

    So ('400353620','EW','FP','1') and ('400353620','EW','FP','01') are the SAME
    permit and did not match. On Queens 52/1 — 25 historical rows, 45 permit
    rows, visibly the same jobs — the key intersection was ZERO, and the merge
    reported a 2,077-row citywide overlap that was pure noise.

    Nothing errored. The dedupe ran, reported a plausible number, and removed
    almost nothing. Normalising the sequence is the whole fix.
    """
    job = r.get("job__") or r.get("job")
    seq = r.get("permit_sequence__") or r.get("permit_sequence")
    if not job:
        return None
    seq = str(seq or "").strip().lstrip("0") or "0"
    return (str(job).strip(), str(r.get("permit_type") or "").strip(),
            str(r.get("permit_subtype") or "").strip(), seq)


def merge_permits(hist_rows, perm_rows):
    """Dedupe within each feed AND across the two. Reports what it removed.

    Preference on collision: keep the row that carries the most non-empty
    fields, so a merge never loses a phone or an owner name that only one copy
    had. Ties keep the historical feed, which carries owner address/phone that
    ipu4-2q9a does not have at all.
    """
    def score(r):
        return sum(1 for v in r.values() if v not in (None, "", "N/A"))

    keep, prov = {}, {}
    stats = {"hist_rows": len(hist_rows), "perm_rows": len(perm_rows),
             "hist_dupes": 0, "perm_dupes": 0, "cross_overlap": 0, "unkeyed": 0}
    for src, rows, dk in (("hist", hist_rows, "hist_dupes"),
                          ("perm", perm_rows, "perm_dupes")):
        for r in rows:
            k = permit_key(r)
            if k is None:
                stats["unkeyed"] += 1
                continue
            r["_date"] = norm_date(r.get("issuance_date"))
            if k not in keep:
                keep[k], prov[k] = r, {src}
            else:
                if src in prov[k]:
                    stats[dk] += 1
                else:
                    stats["cross_overlap"] += 1
                    prov[k].add(src)
                if score(r) > score(keep[k]):
                    merged = dict(keep[k])
                    merged.update({a: b for a, b in r.items()
                                   if b not in (None, "", "N/A")})
                    keep[k] = merged
    stats["unique_permits"] = len(keep)
    stats["naive_sum"] = len(hist_rows) + len(perm_rows)
    stats["inflation"] = stats["naive_sum"] - len(keep)
    return list(keep.values()), stats

LAYERS = [
    # (dataset, era label, scope map, extra where, select, job key field)
    (HIST, "1989-2013 historical permits", PERMIT_SCOPE, None,
     "job,job_type,block,lot,borough,issuance_date,permit_type,permit_subtype,"
     "owner_s_business_name,permittee_s_business_name,permittee_s_phone,bin", "job"),
    (dob.PERMITS, ">=1992-2022 permits", PERMIT_SCOPE, None,
     "job__,job_type,block,lot,borough,issuance_date,permit_type,permit_subtype,"
     "owner_s_business_name,permittee_s_business_name,permittee_s_phone__,bin__", "job__"),
    (dob.BIS_JOBS, "2000-2025 BIS jobs", BIS_SCOPE, "doc__='01'",
     "job__,job_type,block,lot,borough,pre__filing_date,job_status_descrp,"
     "zoning_dist1,proposed_zoning_sqft,enlargement_sq_footage,"
     "proposed_dwelling_units,existing_dwelling_units,proposed_height,"
     "owner_s_business_name,applicant_s_last_name,bin__,job_description", "job__"),
    (dob.NOW_JOBS, "2016-now DOB NOW", NOW_SCOPE, None,
     "job_filing_number,job_type,block,lot,borough,filing_date,filing_status,"
     "total_construction_floor_area,proposed_dwelling_units,existing_dwelling_units,"
     "owner_s_business_name,applicant_last_name,applicant_business_name,"
     "filing_representative_business_name,bin,job_description", "job_filing_number"),
]


def size(spine=None):
    """How big is the scoped job actually? Measure before emitting anything."""
    spine = spine if spine is not None else load_spine()
    print(f"spine parcels: {len(spine):,}\n")
    grand = {}
    for ds, era, scope, extra, select, jobkey in LAYERS:
        print("=" * 78)
        print(f"{era}   [{ds}]")
        for event, w in scope.items():
            where = f"({w})" + (f" and {extra}" if extra else "")
            got = pull(ds, where, select, f"{era}/{event}")
            if got["status"] != "ok":
                print(f"   {event:<12} FAILED {got['error']}")
                continue
            rows = got["rows"]
            jobs, on_spine, off_spine = set(), set(), 0
            for r in rows:
                j = r.get(jobkey)
                if ds == dob.NOW_JOBS and j:
                    j = dob.now_base(j)[0]
                if j:
                    jobs.add(j)
                b = _bbl_from(r, ds)
                if b is None:
                    continue
                if b in spine:
                    on_spine.add(b)
                else:
                    off_spine += 1
            print(f"   {event:<12} rows {len(rows):>9,}   jobs {len(jobs):>9,}   "
                  f"parcels on spine {len(on_spine):>8,}   rows off spine {off_spine:>8,}")
            grand[(era, event)] = {"rows": len(rows), "jobs": len(jobs),
                                   "parcels": len(on_spine), "off_spine": off_spine}
    return grand


if __name__ == "__main__":
    import pprint
    g = size()
    print("\n" + "=" * 78)
    print("TOTALS")
    print(f"  scoped rows   {sum(v['rows'] for v in g.values()):>12,}")
    print(f"  scoped jobs   {sum(v['jobs'] for v in g.values()):>12,}")
    print(f"  off-spine rows{sum(v['off_spine'] for v in g.values()):>12,}"
          f"   <- parcels the spine does not contain; investigate, never ignore")
