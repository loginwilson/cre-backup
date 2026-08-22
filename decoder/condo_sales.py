"""CONDO SALES — the public twin of the StreetEasy rental decoder.

Same decode contract, sales instead of leases:

    date · unit · beds · SF · price · $/USF

Login, 2026-08-06: *"this is the same process, but public instead since every
condo sale and sf is recorded publicly, rather than streeteasy using rental
listing services."*

Half of that is right, and the half that is not decides the whole design.

★ THE SF IS IN THE ASSESSMENT ROLL, AND THAT IS THE WHOLE MODULE.

   `8y4t-faws` — DOF Property Valuation and Assessment Data, Tax Classes 1,2,3,4
   — carries **`gross_sqft` per condominium UNIT lot**, and it is the unit's own
   area, not the building's. Verified 2026-08-06 against 40 real R4 sales:

       matched                                40 of 40 BBLs      100%
       gross_sqft in the 200-3,000 range      39 of 40           unit-scale
       resulting $/USF                        $766 - $3,651      the right range

   `parid` is the 10-digit BBL, so it joins straight to the sale. Better still,
   the roll carries **`aptno`** — the apartment number — so the sale's own
   `apartment_number` cross-checks the join. Two independent statements of which
   unit this is, which is the difference between a join and a hopeful join.

   Roll years 2023-2027 are published, ~2.35M rows each.

⚠ A WITHDRAWN CONCLUSION, LEFT VISIBLE ON PURPOSE. This module first said the
   SF "is not public" and pointed at Marketproof, on the strength of three
   checks: DOF rolling sales (`gross_square_feet` populated on 0.7% of condo
   sales), PVAD `yjxr-fw8i` (no SF column), PLUTO (rows for 0.9% of unit lots).
   Every one of those readings was correct and the conclusion drawn from them
   was wrong — three absences were treated as a survey. Login said "assessment
   roll i think is right", and it is.

   The lesson is the searchable one: NOT FINDING A FIELD IN THREE DATASETS IS
   NOT EVIDENCE THAT THE FIELD DOES NOT EXIST. Search the catalogue for the
   COLUMN, not for the dataset you expect to hold it. Kept here rather than
   deleted, because a disproven belief that vanishes silently gets re-adopted.

WHAT THIS MODULE DOES

    1. Pull the SALE spine from DOF rolling sales — public, citywide, free.
    2. Join per-unit `gross_sqft` from the assessment roll, keyed on BBL, using
       the roll year nearest the sale, and CONFIRM the unit with `aptno`.
    3. Compute $/USF only where SF is real, and grade coverage
       full / partial / none exactly as `lib/rentPool.sfCoverage` grades rentals.
    4. Match to a parcel through the spine.

⚠ THE TRAP INHERITED FROM THE RENTAL SIDE. Filling a missing SF with a building
    average would push every building to `full` and turn estimates into
    measurements. `sf_source` rides on every row so that cannot happen by
    accident, and a unit whose `aptno` disagrees with the sale gets SF of None
    rather than a plausible wrong number.

NOTE THE ASYMMETRY WITH RENTALS, which is real and worth keeping in mind:
    condo SF is complete because DOF assesses every unit; rental SF is patchy
    because it depends on what a landlord chose to publish (Riverview North
    99%, 2-21 Malt Dr 0%).
"""
import json, os, pathlib, sys, time, urllib.parse, urllib.request
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sink

# Windows consoles default to cp1252, which cannot encode the warning glyphs this
# module prints — and a UnicodeEncodeError would kill a completed run at the
# report line, losing the run rather than the character.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SOURCE = "DOF_CONDO"

# ⚠ TWO SALES DATASETS, AND USING ONLY THE FIRST WAS A SILENT ONE-YEAR WINDOW.
#
#   usep-8jbt   NYC Citywide ROLLING Calendar Sales    — the last 12 MONTHS only
#   w2pb-icbu   NYC Citywide ANNUALIZED Calendar Sales — 2016-01-01 to 2025-12-31
#
# This module ran for hours against the rolling file with `--since=2016-01-01`
# and returned exactly the same 15,581 sales as `--since=2024-01-01`, because a
# date filter cannot reach earlier than the dataset's own floor. It then reported
# "15,581 market sales" with nothing to indicate the window had been capped by
# the source — a filter reporting its own output, which is the failure this
# project has met nine times.
#
# Measured 2026-08-06: rolling holds 2025-07-01 -> 2026-06-30 (80,476 rows);
# annualized holds 2016 -> 2025 and carries 208,136 condo-class rows. Thirteen
# times as many. Both are needed — annualized for the history, rolling for the
# months since it ends — and `coverage()` now states the real window rather than
# the requested one.
#
# ★ AND THE ANNUALIZED FILE CARRIES `bbl` AND `bin` DIRECTLY, so the parcel key
#   is READ rather than assembled from borough/block/lot. One less place to be
#   wrong, and `bin` opens a second join to DOB.
ROLLING = "usep-8jbt"
ANNUAL = "w2pb-icbu"
SALES = ROLLING              # kept for callers that still name it
DECODER_ENV = pathlib.Path("C:/dev/acris-decoder.env")
SPINE_DIR = pathlib.Path(os.environ.get(
    "DECODER_SPINE", pathlib.Path(__file__).with_name("spine")))

# R = condominium in DOF's building-class vocabulary. R0-R9 plus RR; the
# residential unit classes are what a comp set is built from.
CONDO_CLASS = "R"


def env(path=DECODER_ENV):
    v = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip().strip('"').strip("'")
    return v


def soda(dataset, params, tries=5):
    """Socrata with the app token and a retry.

    A dropped connection is FAILED and raises. Returning [] here would write a
    short pull that then looks authoritative forever — the single most expensive
    mistake available in this codebase.
    """
    tok = env().get("SOCRATA_APP_TOKEN")
    url = (f"https://data.cityofnewyork.us/resource/{dataset}.json?"
           + urllib.parse.urlencode(params))
    req = urllib.request.Request(url, headers={"X-App-Token": tok} if tok else {})
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=300) as f:
                return json.load(f)
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"FAILED after {tries} tries: {type(last).__name__}: {last}")


def bbl(boro, block, lot):
    return f"{int(boro)}{int(block):05d}{int(lot):04d}"


def unit_label(s):
    """What DOF printed, tidied but not destroyed: 'APT 5A' -> '5A'."""
    s = str(s or "").strip().upper()
    s = s.replace("APT.", "").replace("APT", "").replace("UNIT", "").replace("#", "").strip()
    return s.replace(" ", "") or None


def unit_key(s):
    """Identity across sources, which punctuate units differently."""
    s = "".join(ch for ch in str(s or "").upper() if ch.isalnum())
    return s or None


def usf(price, sf):
    """$/USF. None when SF is absent — NEVER estimated from an average."""
    if not sf or not price or sf <= 0 or price <= 0:
        return None
    return round(price / sf, 2)


def coverage(ds):
    """What window does this dataset ACTUALLY hold? Asked of the source, never
    assumed from the caller's `since`."""
    r = soda(ds, {"$select": "min(sale_date) as a, max(sale_date) as b, count(1) as n"})[0]
    return str(r.get("a") or "")[:10], str(r.get("b") or "")[:10], int(r.get("n") or 0)


def _shape(r, ds):
    """One raw row -> one sale, or a reason it is not one."""
    try:
        price = float(r.get("sale_price") or 0)
    except ValueError:
        price = 0
    if price < 1000:
        return None, "nominal_or_zero_price"
    # ⚠ DO NOT TRUST `bbl` IN THE ANNUALIZED FILE. It is NOT the parcel that sold.
    #
    #   boro/block/lot          DOF `bbl`      apt   address
    #   1/841/1044 -> 1008411044  1008417501   26A   16 WEST 40TH STREET, 26A
    #   1/172/1422 -> 1001721422  1001727504   6A    50 FRANKLIN STREET, 6A
    #   1/174/1537 -> 1001741537  1001740036   6H    91 LEONARD STREET, 6H
    #   1/135/1807 -> 1001351807  None         6     12 WARREN, 6
    #
    # `block`/`lot` identify the UNIT that traded. `bbl` gives the condominium —
    # sometimes its billing lot (75xx), sometimes its base lot, sometimes null.
    # Preferring `bbl` because it "states the BBL outright" moved 126,959 unit
    # sales onto their building's lot, and the distribution flipping to 79%
    # condo_billing was the only visible symptom.
    #
    # The apartment-number check is what caught it: matching the assessment roll
    # on a building lot while comparing UNIT numbers drove `aptno_conflict` from
    # 22 to 15,308. A guard is worth having precisely because it fires on the
    # mistake you did not anticipate.
    try:
        b = bbl(r["borough"], r["block"], r["lot"])
    except Exception:
        return None, "unusable_bbl"
    stated = str(r.get("bbl") or "").split(".")[0]
    condo_bbl = stated if len(stated) == 10 and stated != b else None
    gsf = r.get("gross_square_feet")
    try:
        gsf = float(gsf) if gsf not in (None, "", "0", 0) else None
    except ValueError:
        gsf = None
    return {
        "bbl": b,                      # the parcel that SOLD
        "condo_bbl": condo_bbl,        # the condominium DOF names, when it differs
        "bin": r.get("bin"),
        "unit": unit_label(r.get("apartment_number")),
        "unit_key": unit_key(r.get("apartment_number")),
        "date": str(r.get("sale_date") or "")[:10],
        "price": price, "sf": gsf, "sf_source": "DOF sale record" if gsf else None,
        "usf": usf(price, gsf), "address": r.get("address"),
        "neighborhood": r.get("neighborhood"),
        "bldg_class": r.get("building_class_at_time_of") or r.get("building_class_at_present"),
        "year_built": r.get("year_built"),
        "lat": r.get("latitude"), "lon": r.get("longitude"),
        "dataset": ds,
        "evidence": "index", "document_id": None, "page": None,
    }, None


def pull_sales(since="2016-01-01", limit_total=None):
    """EVERY condominium sale with a real price, across both DOF sales datasets.

    ⚠ A $0 or nominal price is not a market sale. DOF records intra-family
    transfers, deed corrections and sponsor conveyances at $0 or $10; averaging
    those into a comp set drags every rate to nonsense. Filtered, and COUNTED.

    ⚠ The two datasets OVERLAP (annualized ends 2025-12-31, rolling starts
    2025-07-01). Deduped on (bbl, date, price) with the annualized row winning,
    because it carries `bbl` and `bin` stated rather than assembled.
    """
    dropped, raw, sales, seen = Counter(), 0, [], set()
    windows = {}
    for ds, cls_col in ((ANNUAL, "building_class_at_time_of"),
                        (ROLLING, "building_class_at_present")):
        a, b, n = coverage(ds)
        windows[ds] = (a, b, n)
        if b and b < since:
            print(f"  {ds}: holds {a} -> {b}, entirely before --since={since}; skipped")
            continue
        eff = max(since, a) if a else since
        if eff != since:
            print(f"  ⚠ {ds}: asked for {since}, dataset starts {a} — window is {eff}")
        off = 0
        while True:
            rows = soda(ds, {
                "$select": "*",
                "$where": f"sale_date >= '{eff}T00:00:00.000' and {cls_col} like '{CONDO_CLASS}%'",
                "$order": "sale_date", "$limit": 50000, "$offset": off})
            if not rows:
                break
            raw += len(rows)
            for r in rows:
                s_, why = _shape(r, ds)
                if why:
                    dropped[why] += 1
                    continue
                k = (s_["bbl"], s_["date"], s_["price"])
                if k in seen:
                    dropped["overlap_between_datasets"] += 1
                    continue
                seen.add(k)
                sales.append(s_)
            off += len(rows)
            if len(rows) < 50000 or (limit_total and off >= limit_total):
                break
    pull_sales.windows = windows
    return sales, dict(dropped), raw


ROLL = "8y4t-faws"          # DOF assessment roll, tax classes 1,2,3,4


def attach_roll_sf(sales, chunk=180):
    """Join per-unit `gross_sqft` from the assessment roll onto each sale.

    ⚠ THE ROLL IS PUBLISHED ANNUALLY, SO A BBL HAS SEVERAL ROWS. Taking whichever
    came back first would silently mix roll years. The row used is the latest
    year at or before the sale — the assessment in force when it traded. A unit
    that was combined or subdivided changes area between years, and that is
    exactly the case a "just take the newest" rule would get wrong.

    ⚠ `aptno` IS A CHECK, NOT A BONUS. The sale and the roll each name the unit
    independently. When they disagree the BBL is not the unit we think it is, so
    SF is withheld — a missing rate is recoverable, a confident wrong one is not.
    """
    want = sorted({s["bbl"] for s in sales})
    roll = {}
    for i in range(0, len(want), chunk):
        part = want[i:i + chunk]
        where = "(" + " or ".join(f"parid='{b}'" for b in part) + ") and gross_sqft > 0"
        for r in soda(ROLL, {"$select": "parid,year,gross_sqft,aptno,units,bldg_class",
                             "$where": where, "$limit": 50000}):
            roll.setdefault(r["parid"], []).append(r)

    stat = Counter()
    for s in sales:
        rows = roll.get(s["bbl"])
        if not rows:
            stat["no_roll_row"] += 1
            continue
        sale_year = int(s["date"][:4]) if s["date"][:4].isdigit() else 9999
        # latest roll year at or before the sale; if none, the earliest available
        elig = [r for r in rows if str(r.get("year", "")).isdigit()
                and int(r["year"]) <= sale_year]
        pick = (max(elig, key=lambda r: int(r["year"])) if elig
                else min(rows, key=lambda r: int(r.get("year") or 9999)))
        roll_apt = unit_key(pick.get("aptno"))
        if s["unit_key"] and roll_apt and roll_apt != s["unit_key"]:
            # Same BBL, two different unit names. Do not guess which is right.
            s["sf_conflict"] = f"sale apt {s['unit']} vs roll aptno {pick.get('aptno')}"
            stat["aptno_conflict"] += 1
            continue
        sf = float(pick["gross_sqft"])
        s["sf"] = sf
        s["sf_source"] = f"DOF assessment roll {ROLL} FY{pick.get('year')}"
        s["sf_apt_confirmed"] = bool(roll_apt and roll_apt == s["unit_key"])
        s["usf"] = usf(s["price"], sf)
        stat["confirmed" if s["sf_apt_confirmed"] else "matched_no_apt_check"] += 1
    return dict(stat)


def sf_coverage(rows):
    """full >=80% real SF · partial >0 · none = 0 — the same grade rentPool
    applies to rentals, counting ONLY exact per-unit SF.

    This grade is what lets the card say ACTUAL rather than DERIVED, so it must
    never be computed over filled-in values.
    """
    n = len(rows)
    have = sum(1 for r in rows if r.get("sf"))
    if not n:
        return "none", 0, 0
    pct = have / n
    return ("full" if pct >= 0.8 else "partial" if pct > 0 else "none"), have, n


def load_spine_index():
    """BBL -> (kind, parent). Used to walk a condo UNIT lot up to the parcel the
    rest of the world keys on.

    ⚠ REFUSES A STALE SPINE, for the reason set out in SPINE_DEFECTS.md: under
    the pre-2026-08-06 vocabulary condo billing lots did not exist as parcels at
    all, so every new tower's sales read as 'not a parcel'.
    """
    p = SPINE_DIR / "spine.jsonl"
    if not p.exists():
        raise SystemExit(f"no spine at {p} — decoders must not run before it exists")
    idx, kinds = {}, Counter()
    with open(p, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            kinds[r.get("kind")] += 1
            # billing_bbl + condo_name come from condo_lineage.py, which resolved
            # 307,284 unit lots to their condominium via DOF's own condo_key.
            idx[r["bbl"]] = (r.get("kind"), r.get("parent"),
                             r.get("billing_bbl"), r.get("condo_name"))
    if {"ground", "reuc"} & set(kinds):
        raise SystemExit("STALE SPINE — rebuild with the corrected spine.py "
                         "(see SPINE_DEFECTS.md) before matching parcels.")
    if "condo_billing" not in kinds:
        raise SystemExit("STALE SPINE — no condo_billing parcels; every new "
                         "tower's sales would read as 'not a parcel'.")
    print("  spine: " + " · ".join(f"{k} {v:,}" for k, v in kinds.most_common()))
    return idx


def match_parcels(sales, idx):
    """Every sale placed against the spine, bucketed by what its BBL actually is.

    A condo sale's BBL is the UNIT lot. That is the correct, most specific
    parcel — and it is also the one that drops out of any join keyed to
    buildings, which is why the unit's parent is carried alongside.
    """
    buckets = defaultdict(list)
    for s in sales:
        row = idx.get(s["bbl"])
        if row is None:
            buckets["ABSENT_FROM_SPINE"].append(s)
            continue
        kind, parent, billing, cname = row
        s["kind"], s["parent_bbl"] = kind, parent
        # ── THE TWO LEVELS, AND BOTH ARE NEEDED ──────────────────────────────
        # `bbl`          the parcel that legally TRADED — the unit lot. This is
        #                where the assessment roll's per-unit SF lives.
        # `building_bbl` the condominium BILLING lot — where the COMP belongs,
        #                exactly as a StreetEasy rental belongs to its building.
        #
        # The rollup comes from the spine's lineage (DOF condo_key), never from
        # the sales file's own `bbl` column, which gives the billing lot on some
        # rows, the base lot on others and null on the rest.
        s["building_bbl"] = billing or (billing if kind == "condo_billing" else None)                             or (s["bbl"] if kind == "condo_billing" else None)
        s["condo_name"] = cname
        buckets[kind].append(s)
    return dict(buckets)


def report(since="2016-01-01"):
    run_id = f"condo-sales-{int(time.time())}"
    print("loading spine...")
    idx = load_spine_index()

    print(f"pulling DOF condo sales since {since} (paginated)...")
    sales, dropped, raw = pull_sales(since=since)
    print(f"  {raw:,} rows read  ->  {len(sales):,} market sales kept")
    for k, v in dropped.items():
        print(f"     dropped {v:,}  {k}")
    sink.heartbeat(SOURCE, run_id, done=0, total=len(sales),
                   note=f"{raw} raw rows, {len(sales)} market sales")

    if not sales:
        print("\n  0 sales. COMPLETE WITH ZERO — not 'never ran'.")
        sink.heartbeat(SOURCE, run_id, done=0, total=0, status="complete")
        return

    dof_sf = sum(1 for s in sales if s["sf"])
    print(f"\n  SF on the sale record itself: {dof_sf:,} of {len(sales):,} "
          f"({dof_sf/len(sales)*100:.1f}%) — which is why the roll is needed")

    print(f"\njoining per-unit gross_sqft from the assessment roll ({ROLL})...")
    st = attach_roll_sf(sales)
    for k, v in sorted(st.items(), key=lambda x: -x[1]):
        print(f"     {v:>7,}  {k}")

    grade, have, n = sf_coverage(sales)
    print(f"\n  SF COVERAGE: {have:,} of {n:,} sales ({have/n*100:.1f}%) — "
          f"grade '{grade}'")
    conf = sum(1 for s in sales if s.get("sf_apt_confirmed"))
    print(f"     of those, {conf:,} have the unit CONFIRMED by the roll's own "
          f"aptno agreeing with the sale's apartment number")
    print(f"     $/USF computable on {sum(1 for s in sales if s['usf']):,} sales")

    b = match_parcels(sales, idx)
    print(f"\nMATCHED AGAINST THE SPINE — {len(sales):,} sales\n")
    print(f"  {'parcel kind':<24}{'sales':>9}{'w/ SF':>8}   note")
    notes = {
        "condo_unit": "the unit's own tax lot — the correct, most specific parcel",
        "condo_billing": "sold at the billing lot — whole-condo or sponsor sale",
        "tax_lot": "an ordinary tax lot — a whole building or a pre-condo sale",
        "ABSENT_FROM_SPINE": "NOT A PARCEL IN ANY LAYER — investigate before using",
    }
    for k in sorted(b, key=lambda x: -len(b[x])):
        rows = b[k]
        print(f"  {k:<24}{len(rows):>9,}{sum(1 for r in rows if r['sf']):>8,}   "
              f"{notes.get(k, 'unexpected parcel kind')}")
    covered = sum(len(v) for v in b.values())
    print(f"\n  {covered:,} of {len(sales):,} sales bucketed"
          + ("" if covered == len(sales) else "   ⚠ DO NOT TRUST THIS — rows lost"))

    # ── THE COMPLETENESS TEST — RULE_DOCUMENTS_NOT_INDEXES.md ───────────────
    # "How many pages does this document have, and how many did I read?"
    #
    # For this lane the answer is ZERO, and it is printed rather than omitted.
    # `usep-8jbt` is DOF's INDEX of transactions — a row per sale — not the
    # recorded deed. The rule is explicit that an index row tells you a document
    # EXISTS and only the document tells you what it SAYS, so what follows is a
    # finding aid over the sales record, not a decode of it.
    #
    # The nominal-price count below is the proof rather than the theory: the
    # index is SILENT on price for a quarter of these rows, which reads exactly
    # like zero and gets believed exactly like zero — the same DEVR trap
    # (`document_amt = 0` on every one) in different clothes.
    deeds = sum(1 for s_ in sales if s_.get("document_id"))
    nom = dropped.get("nominal_or_zero_price", 0)
    print(f"\n  EVIDENCE TIER: index   (see RULE_APPLIED_COMPARABLES.md)")
    print(f"    {len(sales):,} sales indexed · {have:,} with SF from the "
          f"assessment roll · {deeds:,} DEEDS READ")
    print(f"    the index is silent on price for {nom:,} of {raw:,} rows "
          f"({nom/max(raw,1)*100:.0f}%) — those are dropped here, which is right "
          f"for an index and wrong to believe about the world")
    print(f"    the document is the recorded ACRIS deed, where consideration is "
          f"provable from the cover-page RPTT + RETT stamps")

    sink.heartbeat(SOURCE, run_id, done=len(sales), total=len(sales),
                   status="complete",
                   note=f"tier=index sf={grade} {have}/{n} deeds_read={deeds}")
    return b


if __name__ == "__main__":
    a = sys.argv[1:]
    since = next((x.split("=", 1)[1] for x in a if x.startswith("--since=")), "2016-01-01")
    report(since=since)


# ══ THE ARCHIVE — 2003 to 2015, the part no Socrata dataset holds ═══════════
#
# Login: "I want every condo sale not just 2016."
#
# The two Socrata sales datasets reach back only to 2016-01-01. The rest is
# published as `uzf5-f8n2`, which is NOT a dataset — it is a 67 MB blob named
# "Annualized Rolling Sales Update.zip" holding 65 per-borough .xls files:
#
#     sales_<boro>_03..06     2003-2006
#     sales_2007_<boro>       2007-2008
#     <year>_<boro>.xls       2009-2015
#
# So the full public sale record is 2003 -> today, in three formats, and any
# claim of "every condo sale" that stops at 2016 is short by thirteen years.
#
# ⚠ THE HEADER ROW MOVES. It is row 3 in the 2009 files and not guaranteed
#   elsewhere, so it is FOUND by looking for the row containing "BOROUGH"
#   rather than assumed. A hard-coded row index silently reads the first data
#   row as column names and drops a whole file's worth of sales.
ARCHIVE = pathlib.Path(__file__).with_name("sales_archive")


def _norm(h):
    return "".join(ch for ch in str(h).upper() if ch.isalnum())


def read_archive_file(path):
    """One .xls -> rows shaped like the Socrata sales files. Three outcomes."""
    import xlrd
    bk = xlrd.open_workbook(path)
    sh = bk.sheet_by_index(0)
    head_at = None
    for r in range(min(12, sh.nrows)):
        cells = [_norm(v) for v in sh.row_values(r)]
        if "BOROUGH" in cells and "BLOCK" in cells:
            head_at = r
            break
    if head_at is None:
        return [], "NO HEADER ROW FOUND"
    cols = {}
    for i, v in enumerate(sh.row_values(head_at)):
        cols[_norm(v)] = i

    def cell(row, *names):
        """⚠ xlrd RETURNS EVERY NUMERIC CELL AS A FLOAT, AND THAT SILENTLY
        DESTROYS UNIT LABELS. Apartment "1008" arrives as 1008.0; normalising it
        for matching gives "10080", which fails against the assessment roll's
        "1008" and looks like a genuine unit disagreement.

        Measured before this fix: the archive era reported 13-23% aptno
        conflicts against ~1% in the Socrata era, which serves strings. That
        step at exactly the 2016 source boundary — not a gradient with age — was
        the tell. 39,304 sales had their square footage withheld over a trailing
        ".0". An integral float is rendered as an integer here, once, for every
        column, so no downstream matcher has to know about it.
        """
        for n in names:
            if n in cols:
                v = row[cols[n]]
                if isinstance(v, str):
                    return v.strip()
                if isinstance(v, float) and v.is_integer():
                    return str(int(v))
                return v
        return None

    out = []
    for r in range(head_at + 1, sh.nrows):
        row = sh.row_values(r)
        # ⚠ THE DATE IS AN EXCEL SERIAL, AND `cell()` NOW RENDERS INTEGRAL FLOATS
        # AS INTEGERS — so it arrives as the string "39820", not the float
        # 39820.0. Fixing the apartment-number float broke this in the same
        # commit: 39820 is a perfectly plausible-looking value that is not a
        # date at all. Decode from the serial whenever the value is numeric,
        # whatever type it arrives as.
        d = cell(row, "SALEDATE")
        ser = None
        try:
            ser = float(d)
        except (TypeError, ValueError):
            ser = None
        if ser and ser > 20000:            # ~1954 onward; below that it is not a serial
            y, m, dd, *_ = xlrd.xldate_as_tuple(ser, bk.datemode)
            d = f"{y:04d}-{m:02d}-{dd:02d}"
        else:
            d = str(d or "")[:10].replace("/", "-")
        out.append({
            "borough": cell(row, "BOROUGH"),
            "block": cell(row, "BLOCK"),
            "lot": cell(row, "LOT"),
            "apartment_number": cell(row, "APARTMENTNUMBER"),
            "address": cell(row, "ADDRESS"),
            "neighborhood": cell(row, "NEIGHBORHOOD"),
            "sale_date": d,
            "sale_price": cell(row, "SALEPRICE"),
            "gross_square_feet": cell(row, "GROSSSQUAREFEET"),
            "year_built": cell(row, "YEARBUILT"),
            "building_class_at_time_of": cell(row, "BUILDINGCLASSATTIMEOFSALE",
                                              "BUILDINGCLASSATPRESENT"),
            "bbl": None,          # the archive states none; built from boro/block/lot
        })
    return out, None


def pull_archive():
    """Every archive file, with per-file denominators. A file that fails to read
    is FAILED and named — never counted as a file with no sales."""
    if not ARCHIVE.exists():
        raise SystemExit(f"no archive at {ARCHIVE} — download uzf5-f8n2 first")
    files = sorted(ARCHIVE.glob("*.xls"))
    sales, dropped, raw, bad = [], Counter(), 0, []
    for fp in files:
        rows, err = read_archive_file(fp)
        if err:
            bad.append((fp.name, err))
            continue
        raw += len(rows)
        kept = 0
        for r in rows:
            cls = str(r.get("building_class_at_time_of") or "")
            if not cls.upper().startswith(CONDO_CLASS):
                dropped["not_condo_class"] += 1
                continue
            s_, why = _shape(r, "archive:" + fp.name)
            if why:
                dropped[why] += 1
                continue
            sales.append(s_)
            kept += 1
        print(f"    {fp.name:<26}{len(rows):>8,} rows  ->{kept:>7,} condo sales")
    if bad:
        print(f"  ⚠ {len(bad)} FILE(S) UNREADABLE — these are not empty years:")
        for n, e in bad:
            print(f"      {n}: {e}")
    return sales, dict(dropped), raw, bad
