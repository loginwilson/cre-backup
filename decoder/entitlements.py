"""One row per parcel per entitlement. What happened, on which lot, when.

LOGIN, 2026-08-06:

    "this job is as easy as accessing every application/document, decoding what
     happened, and recording it into the entitlements data table for that parcel
     on the spine"

That is the job, and this file is the third step. `facts` holds the citation-
grade detail — every condition, every figure, every page. Nobody reads a parcel
by scanning 324 fact rows. This is the answer to the only question that gets
asked first:

    what entitlements does this lot have, and what happened with each?

ONE ROW PER (bbl, source, document). Joins to the spine on bbl.

WHAT GOES IN AND WHAT STAYS OUT

    IN   the body, the instrument, the section relied on, the outcome, both
         dates, a plain sentence, how many conditions bind it, and a URL that
         walks back to the document.
    OUT  every number. Floor area, FAR, height and the relief they imply live
         in `facts`, where each carries its own page and derivation. Summarising
         them here would create a second, un-citable copy that drifts.

⚠ CONDITIONS ARE COUNTED, NOT COPIED. A parcel with 20 binding conditions and
  one with none are different propositions, and the count says so at a glance.
  The text of each stays in `facts` with its page.
"""
import json, os, pathlib, re, sys, urllib.error, urllib.request
from collections import defaultdict, Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sink

ENV = r"C:/dev/acris-decoder.env"

DDL = """
-- run once in the Supabase SQL editor. Safe to re-run.
create table if not exists decoder_entitlements (
  bbl           text not null,
  source        text not null,          -- BSA | DCP | LPC
  document_id   text not null,          -- calendar no | COFA no | ZAP project id
  primary key (bbl, source, document_id)
);

-- ⚠ ONE ALTER PER COLUMN, and every column named EXACTLY ONCE. A create-table
-- column list that grew by patching ended up declaring `expires` as both text
-- and date and `cb_recommendation` twice — Postgres rejects the whole
-- statement with "column specified more than once". Additive ALTERs cannot
-- develop that problem, and they work whether or not the table already exists.
alter table decoder_entitlements add column if not exists body          text;
alter table decoder_entitlements add column if not exists instrument    text;
alter table decoder_entitlements add column if not exists zr_section    text;
alter table decoder_entitlements add column if not exists outcome       text;
alter table decoder_entitlements add column if not exists happened      date;
alter table decoder_entitlements add column if not exists recorded      date;
alter table decoder_entitlements add column if not exists what          text;
alter table decoder_entitlements add column if not exists conditions    int;
alter table decoder_entitlements add column if not exists enlargement   boolean;
alter table decoder_entitlements add column if not exists url           text;
alter table decoder_entitlements add column if not exists basis         text;
alter table decoder_entitlements add column if not exists applicant     text;
alter table decoder_entitlements add column if not exists ulurp         text;
alter table decoder_entitlements add column if not exists in_flight     boolean;
alter table decoder_entitlements add column if not exists motivator     boolean;
alter table decoder_entitlements add column if not exists restrictor    boolean;
alter table decoder_entitlements add column if not exists signal        boolean;
alter table decoder_entitlements add column if not exists effect_why    text;
alter table decoder_entitlements add column if not exists expires       date;
alter table decoder_entitlements add column if not exists lapsed        boolean;
alter table decoder_entitlements add column if not exists cb            text;
alter table decoder_entitlements add column if not exists cb_recommendation text;
alter table decoder_entitlements add column if not exists vote_affirmative int;
alter table decoder_entitlements add column if not exists vote_negative  int;
alter table decoder_entitlements add column if not exists vote_unanimous boolean;
alter table decoder_entitlements add column if not exists hearing_first  date;
alter table decoder_entitlements add column if not exists e_designation  text;
alter table decoder_entitlements add column if not exists ceqr           text;
alter table decoder_entitlements add column if not exists dob_job        text;
alter table decoder_entitlements add column if not exists enforcement_status text;
alter table decoder_entitlements add column if not exists notice_of_violation text;
alter table decoder_entitlements add column if not exists work_without_permit boolean;
alter table decoder_entitlements add column if not exists updated_at timestamptz default now();

create index if not exists decoder_entitlements_bbl on decoder_entitlements(bbl);
create index if not exists decoder_entitlements_inst
  on decoder_entitlements(instrument, outcome);
create index if not exists decoder_entitlements_when on decoder_entitlements(happened);
create index if not exists decoder_entitlements_effect
  on decoder_entitlements(motivator, restrictor, signal);
create index if not exists decoder_entitlements_lapsed
  on decoder_entitlements(lapsed);

-- ⚠ DROP BEFORE CREATE. `create or replace view` can only replace a view whose
-- column NAMES and ORDER are unchanged; adding one mid-list raises 42P16.
drop view if exists decoder_parcel_entitlements;
create view decoder_parcel_entitlements as
select p.bbl, p.boro, p.block, p.lot, p.address,
       e.source, e.body, e.instrument, e.zr_section, e.outcome,
       e.happened, e.recorded, e.what, e.conditions, e.enlargement,
       e.applicant, e.ulurp, e.in_flight,
       e.motivator, e.restrictor, e.signal, e.effect_why,
       e.expires, e.lapsed, e.cb, e.cb_recommendation, e.vote_unanimous,
       e.e_designation, e.ceqr, e.dob_job,
       e.enforcement_status, e.notice_of_violation, e.work_without_permit,
       e.basis, e.url
from decoder_parcels p
join decoder_entitlements e on e.bbl = p.bbl
order by p.bbl, e.happened desc nulls last;
"""

BODY = {"BSA": "Board of Standards and Appeals",
        "DCP": "City Planning Commission",
        "LPC": "Landmarks Preservation Commission"}

BSA_URL = "https://www.nyc.gov/assets/bsa/downloads/pdf/decisions/{}.pdf"
LPC_URL = "https://s-media.nyc.gov/agencies/lpc/Permits/PermitFiles/{}.pdf"
DCP_URL = "https://zap.planning.nyc.gov/projects/{}"

DCP_INSTRUMENT = {"ZM": "rezoning", "ZR": "text_amendment", "ZS": "special_permit",
                  "ZA": "authorization", "ZC": "certification",
                  "ZJ": "special_permit", "LD": "large_scale",
                  "PP": "disposition", "HD": "housing", "HK": "housing"}


def bsa_instrument(calendar, section):
    """What kind of BSA action this is — from the calendar suffix, which is the
    Board's own type code, and the section it relied on."""
    suffix = (calendar or "").rsplit("-", 1)[-1].upper()
    sec = (section or "").strip()
    if suffix.startswith("BZY"):
        return "vested_rights"
    if suffix.startswith("A"):
        return "appeal"
    if re.match(r"BZ[IVX]+$", suffix):          # BZII, BZIII = later amendment
        return "amendment"
    if sec.startswith("72-21"):
        return "variance"
    if sec.startswith("73-"):
        return "special_permit"
    if sec.startswith("11-3"):
        return "vested_rights"
    return "variance" if suffix.startswith("BZ") else "other"


def from_facts():
    """Roll the sink's live facts up to one row per (bbl, source, document)."""
    rows = {}
    conds = Counter()
    for f in sink.facts():
        src, doc = f.get("source"), f.get("document_id")
        if src not in BODY or not doc:
            continue
        for b in (f.get("bbls") or []):
            if not b:
                continue
            k = (b, src, doc)
            if f["predicate"] == "condition_imposed":
                conds[k] += 1
                continue
            r = rows.setdefault(k, {"bbl": b, "source": src, "document_id": doc,
                                    "body": BODY[src], "basis": "document"})
            r.setdefault("happened", f.get("happened"))
            r.setdefault("recorded", f.get("recorded"))
            if f.get("zr_section"):
                r.setdefault("zr_section", f["zr_section"])
            if f["predicate"] == "variance_granted":
                r["outcome"] = f.get("outcome") or "granted"
                r["what"] = _tidy(f.get("verbatim"))
                for k in ("expires", "cb", "cb_recommendation", "e_designation",
                          "ceqr", "dob_job", "vote_affirmative",
                          "vote_negative", "vote_unanimous", "hearing_first"):
                    if f.get(k) is not None:
                        r[k] = f[k]
                for k in ("expires", "expires_basis", "cb", "cb_recommendation",
                          "vote_affirmative", "vote_negative", "vote_unanimous",
                          "hearing_first", "applicant", "e_designation", "ceqr"):
                    if f.get(k) is not None:
                        r[k] = f[k]
            elif f["predicate"] == "filed":
                r.setdefault("outcome", f.get("outcome") or "filed")
                r.setdefault("what", _tidy(f.get("verbatim")))
            elif f["predicate"] == "condition_imposed" and f.get("work_without_permit"):
                r["enforcement_status"] = f.get("enforcement_status")
                r["notice_of_violation"] = f.get("notice_of_violation")
                r["work_without_permit"] = True
            elif f["predicate"] == "permit_issued":
                r["outcome"] = "granted"
                r["instrument"] = "cofa"
                r["enlargement"] = bool(f.get("is_enlargement"))
                r.setdefault("what", _tidy(f.get("verbatim"), 300))
    out = []
    for k, r in rows.items():
        r["conditions"] = conds.get(k, 0)
        if r["source"] == "BSA":
            r["instrument"] = bsa_instrument(r["document_id"], r.get("zr_section"))
            r["url"] = BSA_URL.format(r["document_id"])
        elif r["source"] == "LPC":
            r.setdefault("instrument", "cofa")
            r["url"] = LPC_URL.format(r["document_id"])
        r.setdefault("what", f"{r.get('instrument','')} — {r['document_id']}")
        out.append(r)
    return out


def from_dcp_register(path="dcp_ledger.jsonl"):
    """DCP rows come from the ZAP REGISTER, not from a document.

    ⚠ Marked basis='register' and it matters. DCP's filed documents are behind
    an authentication wall, so nothing here was read off a page. What the
    register DOES state first-hand — which parcels, which action, what status,
    who applied — is DCP asserting it directly, and a rezoning in public review
    is the earliest development signal in the city. It is recorded, and it is
    labelled so nobody mistakes it for a decoded document.
    """
    p = pathlib.Path(path)
    if not p.exists():
        return []
    # status, dates and applicant come from the ZAP index — which IS DCP's
    # register in Socrata form, the same register the project record serves. Not
    # a document, and the row says so via basis='register'.
    idx = {}
    try:
        import dcp
        for r in dcp.index():
            idx[r.get("project_id")] = r
    except Exception:
        pass
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("status") != "resolved":
                continue
            codes = [c for c in (r.get("actions") or []) if c]
            inst = next((DCP_INSTRUMENT[c] for c in codes if c in DCP_INSTRUMENT),
                        "other")
            ix = idx.get(r["project_id"], {})
            pub = (ix.get("public_status") or "").strip()
            prj = (ix.get("project_status") or "").strip()
            # ⚠ TWO STATUS FIELDS THAT MEAN DIFFERENT THINGS. public_status is
            # where the application is in ULURP (Filed / Noticed / In Public
            # Review / Completed); project_status is how it ENDED (Complete,
            # Withdrawn-Other, Terminated). "Completed" review of a withdrawn
            # application is not an approval, and collapsing them would turn
            # 2,516 withdrawals into entitlements.
            outcome = {"Complete": "approved", "Withdrawn-Other": "withdrawn",
                       "Terminated": "terminated",
                       "Terminated-Applicant Unresponsive": "terminated",
                       "Active": "in_review", "On-Hold": "on_hold",
                       "Record Closed": "closed"}.get(prj)
            if not outcome:
                outcome = pub.lower().replace(" ", "_") or None
            what = _tidy(ix.get("project_brief")) or _tidy(r.get("project_name")) \
                or r["project_id"]
            for b in (r.get("bbls") or []):
                out.append({
                    "bbl": str(b), "source": "DCP",
                    "document_id": r["project_id"], "body": BODY["DCP"],
                    "instrument": inst, "zr_section": None,
                    "outcome": outcome,
                    "happened": (ix.get("approval_date") or
                                 ix.get("completed_date") or "")[:10] or None,
                    "recorded": (ix.get("certified_referred") or
                                 ix.get("app_filed_date") or "")[:10] or None,
                    "what": what, "conditions": 0, "enlargement": None,
                    "url": DCP_URL.format(r["project_id"]),
                    "basis": "register",
                    "applicant": _tidy(ix.get("primary_applicant"), 120),
                    "ulurp": _tidy(ix.get("ulurp_numbers"), 80),
                    "in_flight": pub in ("Filed", "Noticed", "In Public Review")})
    return out


# ── how an entitlement SWINGS a site ─────────────────────────────────────────
#
# LOGIN, 2026-08-06: "this is where we have entitlements play a factor on the
# site and swing it with motivators, restrictors, signals"
#
# Three INDEPENDENT flags, not one label, because the same instrument is
# routinely two things at once. A granted §72-21 variance adds floor area the
# district would never allow (motivator) AND lands twenty conditions that run
# with the land forever (restrictor). Forcing a single verdict would throw away
# whichever half you did not pick.
#
#   motivator   adds development capacity, or preserves rules better than
#               today's — the reason a site is worth more than its zoning says
#   restrictor  binds, limits or forecloses — the reason a site is worth less,
#               or cannot do what the FAR implies
#   signal      evidence of activity now or imminent — somebody is moving
#
# Every row records `effect_why`, the rule that produced its flags, so a reader
# can disagree with the classification without having to reverse-engineer it.

import datetime
TODAY = datetime.date.today().isoformat()

MONTHS = {m: i for i, m in enumerate(
    ["january","february","march","april","may","june","july","august",
     "september","october","november","december"], 1)}


def _iso_date(s, note=None):
    """'April 25, 2026' -> '2026-04-25'. Anything else -> None, never a guess.

    ⚠ AND THE DATE MUST EXIST. BSA 324-05-BZY reads "to expire on April 31,
    2006". April has thirty days. The parse is correct and the Board is wrong,
    which Postgres rejects outright ("date/time field value out of range") and
    killed a 113,746-row push at row 13,000.

    An impossible date is NOT coerced. Nudging it to April 30 or May 1 would be
    inventing a legal deadline by one day, and a term that expires is exactly
    the field where one day matters. It is dropped to NULL — so `lapsed` becomes
    unknown rather than computed off a fiction — and the raw string is carried
    into the note so the impossibility stays visible instead of being tidied
    away.
    """
    if not s:
        return None
    s = str(s).strip()
    if re.match(r"\d{4}-\d{2}-\d{2}$", s):
        # ⚠ ISO-SHAPED IS NOT THE SAME AS VALID, and this branch trusted the
        # shape. '2006-04-31' matches the pattern perfectly. The value arrives
        # already formatted from bsa.py, which built it from "April 31, 2006"
        # without checking that April has a 31st — so the guard added below was
        # never reached and the bad date sailed through to Postgres.
        try:
            datetime.date.fromisoformat(s)
            return s
        except ValueError:
            if note is not None:
                note.append(f"the document states an impossible date, '{s}' — "
                            f"recorded as unknown rather than nudged to a real "
                            f"one, because a term that expires is exactly the "
                            f"field where one day matters")
            return None
    m = re.match(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", s)
    if m and m.group(1).lower() in MONTHS:
        iso = (f"{int(m.group(3)):04d}-{MONTHS[m.group(1).lower()]:02d}"
               f"-{int(m.group(2)):02d}")
        try:
            datetime.date.fromisoformat(iso)
            return iso
        except ValueError:
            if note is not None:
                note.append(f"the document states an impossible date, '{s}' — "
                            f"kept as stated, not corrected")
            return None
    return None


ADDITIVE_WORK = {"new_building", "rooftop_addition", "rear_addition", "enlargement"}
_TODAY = __import__("datetime").date.today().isoformat()


def classify_effect(r):
    """Explicit rules, applied in the open. Returns (motivator, restrictor,
    signal, why)."""
    mot = res = sig = False
    why = []
    inst = r.get("instrument")
    out = (r.get("outcome") or "").lower()

    # ── restrictors ──────────────────────────────────────────────────────
    # ★ AN OPEN LPC VIOLATION IS A HARD RESTRICTOR. Work was done to a
    # landmarked building without a permit and the notice says it REMAINS IN
    # EFFECT — the owner has an unresolved obligation to the Commission, and
    # nothing else in this project records it. A rescinded one is history and
    # is recorded as such rather than dropped, because "was cited and cleared"
    # is different from "never cited".
    if r.get("enforcement_status") == "open":
        res = True
        sig = True
        why.append(f"LPC violation REMAINS IN EFFECT — work was done at this "
                   f"landmarked property without a permit and the notice has "
                   f"not been rescinded"
                   + (f" (NOV {r['notice_of_violation']})"
                      if r.get("notice_of_violation") else ""))
    elif r.get("enforcement_status") == "rescinded":
        sig = True
        why.append("LPC cited work done without a permit here and later "
                   "rescinded the notice — resolved, but the property has an "
                   "enforcement history")
    elif r.get("work_without_permit"):
        res = True
        why.append("LPC recorded work done without a permit at this landmarked "
                   "property")
    if inst == "designation":
        res = True
        why.append("landmark designation — exterior work needs LPC approval "
                   "and an as-of-right building can be refused outright")
    if (r.get("conditions") or 0) > 0:
        res = True
        why.append(f"{r['conditions']} conditions bind the lot and must appear "
                   f"on the certificate of occupancy")
    if out in ("denied", "dismissed"):
        res = True
        why.append("relief was refused — the underlying constraint stands, and "
                   "the Board has already considered this site")
    if r.get("e_designation"):
        res = True
        why.append(f"(E) designation {r['e_designation']} on the zoning map — "
                   f"testing and remediation required before any soil "
                   f"disturbance, and it binds independently of this grant")
    if (r.get("cb_recommendation") or "") == "denial":
        why.append("the Community Board recommended denial — the Board granted "
                   "it anyway, but local opposition is on the record")
    if inst == "cofa" and r.get("enlargement") is False:
        res = True
        why.append("landmark permit for non-additive work — form is controlled")

    # ── motivators ───────────────────────────────────────────────────────
    if r.get("lapsed"):
        res = True
        why.append(f"the grant's deadline ({r['expires']}) has PASSED — the "
                   f"certificate of occupancy was to be obtained by then, so "
                   f"this is not a live entitlement without a reinstatement")
    if out in ("granted", "approved") and not r.get("lapsed"):
        if inst in ("variance", "special_permit"):
            mot = True
            why.append(f"{inst} granted — the site holds use or bulk the "
                       f"district does not otherwise allow, and it runs with "
                       f"the land")
        elif inst == "rezoning":
            mot = True
            why.append("zoning map amendment approved — the district itself "
                       "changed here")
        elif inst == "text_amendment":
            mot = True
            why.append("zoning text amendment approved — the rule that governs "
                       "this site changed")
        elif inst == "vested_rights":
            mot = True
            why.append("vested rights — prior regulations still apply, which "
                       "are often more permissive than current ones")
        elif inst in ("authorization", "large_scale"):
            mot = True
            why.append(f"{inst} approved — discretionary relief in place")
    if inst == "cofa" and r.get("enlargement"):
        mot = True
        why.append("landmark permit approved ADDITIVE work — the Commission "
                   "has already accepted an enlargement on this building")

    # ── signals ──────────────────────────────────────────────────────────
    if r.get("in_flight"):
        sig = True
        why.append("live land-use application, no decision yet — upstream of "
                   "any DOB filing")
    if out in ("in_review", "filed", "noticed", "on_hold"):
        sig = True
        why.append(f"application {out} — the owner is actively seeking relief")
    if r.get("cb_recommendation") == "denial":
        why.append("the Community Board recommended DENIAL and the Board granted "
                   "it anyway — local opposition is on the record")
    if r.get("vote_unanimous") is False:
        why.append(f"the Board itself split "
                   f"{r.get('vote_affirmative')}-{r.get('vote_negative')}")
    if r.get("e_designation"):
        res = True
        why.append(f"(E) designation {r['e_designation']} on the Zoning Map — "
                   f"hazmat/air/noise obligations bind independently of the grant")
    if out in ("withdrawn", "terminated"):
        sig = True
        why.append("an application was started and abandoned — somebody wanted "
                   "to develop here and stopped")
    return mot, res, sig, "; ".join(why) or None


def from_lpc_designations():
    """⚠ THE BIGGEST RESTRICTOR IN THE CITY, AND I HAD LEFT IT OUT.

    39,363 designated BBLs, already per-parcel in ncre-qhxs, needing no document
    at all. A landmark designation can stop an as-of-right building outright —
    it is the one entitlement fact that changes what a site can do without
    anybody applying for anything. Basis is `register`: LPC states it directly.
    """
    import bulk
    out = []
    for r in bulk.socrata("ncre-qhxs"):
        b = str(r.get("bbl") or "").strip()
        if not b or not b.isdigit():
            continue
        lp = r.get("lp_number") or "LP-?"
        out.append({
            "bbl": b, "source": "LPC", "document_id": lp,
            "body": BODY["LPC"], "instrument": "designation",
            "zr_section": None, "outcome": "designated",
            "happened": _date(r.get("desdate")),
            "recorded": _date(r.get("public_hea")),
            "what": _tidy(f"{r.get('lm_type') or 'Landmark'}: "
                          f"{r.get('lm_name') or r.get('desig_addr') or ''}"),
            "conditions": 0, "enlargement": None,
            "url": "https://www.nyc.gov/site/lpc/designations/designation-reports.page",
            "basis": "register"})
    return out


def _date(s):
    if not s:
        return None
    s = str(s).strip()
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return s[:10] if re.match(r"\d{4}-\d{2}-\d{2}", s) else None


def _tidy(s, n=400):
    return re.sub(r"\s+", " ", s or "").strip()[:n] or None


def _env():
    v = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip()
    return v["ACRIS_SUPABASE_URL"], v["ACRIS_SUPABASE_SERVICE_KEY"]


COLUMNS = ("bbl", "source", "document_id", "body", "instrument", "zr_section",
           "outcome", "happened", "recorded", "what", "conditions",
           "enlargement", "url", "basis", "applicant", "ulurp", "in_flight",
           "motivator", "restrictor", "signal", "effect_why",
           "expires", "expires_basis", "lapsed", "cb", "cb_recommendation",
           "vote_affirmative", "vote_negative", "vote_unanimous",
           "hearing_first", "e_designation", "ceqr")


def push(rows, batch=500):
    """⚠ EVERY ROW IN A BATCH MUST CARRY THE SAME KEYS. PostgREST rejects a
    bulk insert whose objects differ in shape ("All object keys must match"),
    and my BSA/LPC rows have no applicant/ulurp/in_flight while DCP rows do.
    Normalising to the full column set with explicit nulls is the difference
    between a 29,840-row push and a 400."""
    base, key = _env()
    rows = [{c: r.get(c) for c in COLUMNS} for r in rows]
    # ⚠ LAST LINE OF DEFENCE. One bad date in 113,746 rows aborted the push at
    # row 13,000. Validating here means a source that invents February 30th
    # costs that row's date, not the whole load.
    for r in rows:
        for c in ("happened", "recorded", "expires", "hearing_first"):
            v = r.get(c)
            if not v:
                continue
            try:
                datetime.date.fromisoformat(str(v)[:10])
            except Exception:
                r[c] = None
    sent = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        body = json.dumps(chunk, default=str).encode("utf-8")
        for a in range(4):
            try:
                req = urllib.request.Request(
                    f"{base}/rest/v1/decoder_entitlements"
                    f"?on_conflict=bbl,source,document_id", data=body,
                    headers={"apikey": key, "Authorization": "Bearer " + key,
                             "Content-Type": "application/json",
                             "Prefer": "resolution=merge-duplicates,return=minimal"},
                    method="POST")
                with urllib.request.urlopen(req, timeout=180):
                    pass
                sent += len(chunk)
                break
            except urllib.error.HTTPError as e:
                if e.code < 500:
                    return sent, f"{e.code} {e.read().decode('utf-8','ignore')[:250]}"
            except Exception:
                pass
            import time
            time.sleep(2 ** a)
    return sent, None


def build():
    rows = from_facts() + from_dcp_register() + from_lpc_designations()
    seen, out = set(), []
    for r in rows:
        k = (r["bbl"], r["source"], r["document_id"])
        if k in seen:
            continue
        seen.add(k)
        # ⚠ LAPSED IS COMPUTED HERE, NOT READ. A grant whose CO deadline has
        # passed may still have been exercised — the deadline is when it had to
        # be, not proof it wasn't. So `lapsed` says "the deadline is behind us",
        # and confirming whether a CO actually issued is a DOB question. Stated
        # that way in effect_why so nobody reads it as "this variance is dead".
        exp = r.get("expires")
        if exp:
            r["lapsed"] = str(exp)[:10] < _TODAY
        # ⚠ AN EXPIRED GRANT IS NOT AN ENTITLEMENT, and reporting one as live
        # is the worst error this table can make. `expires` is the date the
        # resolution itself sets for obtaining the certificate of occupancy.
        bad = []
        r["expires"] = _iso_date(r.get("expires"), bad)
        r["hearing_first"] = _iso_date(r.get("hearing_first"), bad)
        r["_date_note"] = "; ".join(bad) or None
        if r.get("expires"):
            r["lapsed"] = r["expires"] < TODAY
        r["motivator"], r["restrictor"], r["signal"], r["effect_why"] =             classify_effect(r)
        if r.pop("_date_note", None):
            r["effect_why"] = "; ".join(x for x in (r.get("effect_why"),
                                                    bad and bad[0]) if x)
        if r.get("lapsed"):
            r["effect_why"] = ((r.get("effect_why") or "") +
                               f"; ⚠ the grant's deadline ({exp}) has passed — "
                               f"whether a CO issued in time is a DOB question, "
                               f"not answered here")
        out.append(r)
    return out


if __name__ == "__main__":
    if "--ddl" in sys.argv:
        print(DDL)
        raise SystemExit(0)
    rows = build()
    print(f"entitlement rows: {len(rows):,}")
    print("  by source:    ", Counter(r["source"] for r in rows).most_common())
    print("  by instrument:", Counter(r.get("instrument") for r in rows).most_common())
    print("  by outcome:   ", Counter(r.get("outcome") for r in rows).most_common(8))
    print(f"  distinct parcels: {len({r['bbl'] for r in rows}):,}")
    print(f"  carrying conditions: {sum(1 for r in rows if r['conditions']):,}")
    print()
    print(f"  MOTIVATOR  {sum(1 for r in rows if r['motivator']):>7,}")
    print(f"  RESTRICTOR {sum(1 for r in rows if r['restrictor']):>7,}")
    print(f"  SIGNAL     {sum(1 for r in rows if r['signal']):>7,}")
    print(f"  both mot+res {sum(1 for r in rows if r['motivator'] and r['restrictor']):>5,}"
          f"   (a grant that also binds — the common case)")
    if "--push" in sys.argv:
        sent, err = push(rows)
        print(f"\npushed {sent:,}/{len(rows):,}" + (f"  ERROR {err}" if err else "  OK"))
        if err and "PGRST205" in str(err):
            print("\nTable missing — run this first:\n")
            print(DDL)
