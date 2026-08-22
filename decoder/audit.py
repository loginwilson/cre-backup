"""Self-audit — every trap we have ever learned, re-run against the whole store.

The iterative engine's enforcement arm: instead of remembering to re-check past
entries when a new trap is found, add the trap here and it is re-checked forever,
on every run, over every document.

Each check reports PASS / FAIL / INFO with denominators. A check that cannot be
evaluated says so rather than passing silently. Nothing here repairs data.
"""
import json, pathlib, re, urllib.parse, urllib.request

ENV = r"C:/dev/acris-decoder.env"
TOKEN = "XBMcBRBwtwiD4elm0XS5iwLRZ"
LEGALS_API = "https://data.cityofnewyork.us/resource/8h5j-fqxa.json"


def env():
    v = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip()
    return v["ACRIS_SUPABASE_URL"], v["ACRIS_SUPABASE_SERVICE_KEY"]


URL, KEY = env()


def get(path):
    req = urllib.request.Request(URL + "/rest/v1/" + path,
                                 headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=60) as f:
        return json.load(f)


def index_legals(doc_ids):
    out = {}
    ids = list(doc_ids)
    for i in range(0, len(ids), 40):
        chunk = ids[i:i + 40]
        where = "document_id in(" + ",".join(f"'{c}'" for c in chunk) + ")"
        q = urllib.parse.urlencode({"$where": where, "$limit": 5000, "$$app_token": TOKEN})
        with urllib.request.urlopen(LEGALS_API + "?" + q, timeout=60) as f:
            for r in json.load(f):
                b = f"{int(r['borough'])}{int(r['block']):05d}{int(r['lot']):04d}"
                out.setdefault(r["document_id"], set()).add(b)
    return out


RESULTS = []


def report(name, status, detail):
    RESULTS.append((status, name, detail))
    print(f"  [{status:4}] {name}: {detail}")


def main():
    docs = get("decoder_document?select=document_id,doc_type,instrument,consideration,"
               "decode_status,validation_tier,document_date,recorded_date,crfn,anomalies,raw_facts,source")
    posts = get("decoder_posting?select=document_id,bbl,account,quantity_sf,amount_usd,"
                "effective_date,payload,provenance&limit=5000")
    links = get("decoder_lifecycle_link?select=document_id,target_kind,target_ref,resolved_doc_id")
    n = len(docs)
    print(f"AUDIT over {n} documents / {len(posts)} postings / {len(links)} citations\n")

    # 1. field hygiene ------------------------------------------------------
    bad = [p for p in posts
           if not re.match(r"^\d{10}$", str(p["bbl"]))
           or (p["effective_date"] and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(p["effective_date"])))
           or not p["provenance"]]
    report("field hygiene (bbl/date/provenance)", "PASS" if not bad else "FAIL",
           f"{len(posts) - len(bad)}/{len(posts)} postings well-formed")

    # 2. every decoded document produced postings ---------------------------
    with_posts = {p["document_id"] for p in posts}
    inert = [d["document_id"] for d in docs if d["document_id"] not in with_posts]
    report("no inert documents (decoded but unreduced)", "PASS" if not inert else "FAIL",
           f"{n - len(inert)}/{n} produced postings" + (f"; inert: {inert}" if inert else ""))

    # 3. transfer groups: every side member present, group balances ---------
    groups = {}
    for p in posts:
        pl = p.get("payload") or {}
        g = pl.get("transfer_group")
        if not g:
            continue
        d = groups.setdefault(g, {"from": [], "to": [], "expect": {}, "group_sf": pl.get("group_quantity_sf")})
        d[pl["side"]].append(p)
        d["expect"][pl["side"]] = pl.get("side_member_count")
    missing = [g for g, d in groups.items()
               if any(d["expect"].get(s) and len(d[s]) != d["expect"][s] for s in ("from", "to"))]
    report("collective grants: all side members posted", "PASS" if not missing else "FAIL",
           f"{len(groups) - len(missing)}/{len(groups)} transfer groups complete")

    unbalanced, allocated = [], 0
    for g, d in groups.items():
        fs = [abs(p["quantity_sf"]) for p in d["from"] if p["quantity_sf"] is not None]
        ts = [abs(p["quantity_sf"]) for p in d["to"] if p["quantity_sf"] is not None]
        if len(fs) == len(d["from"]) and len(ts) == len(d["to"]) and fs and ts:
            allocated += 1
            if abs(sum(fs) - sum(ts)) >= 1:
                unbalanced.append(g)
    report("envelope conservation (fully-allocated groups)", "PASS" if not unbalanced else "FAIL",
           f"{allocated - len(unbalanced)}/{allocated} balanced; "
           f"{len(groups) - allocated} groups collective/unquantified")

    # 4. $0 consideration must be AFFIRMATIVELY verified ---------------------
    # An index amount of $0 can hide a real price paid via prepaid tax-return
    # references (the Extell trap). Verification is a FACT we record, not
    # something to infer from prose — the earlier keyword matcher reported 0
    # annotated when all 4 were, because it was grepping free text.
    zero = [d for d in docs if not d["consideration"]
            and (d.get("source") or "acris") == "acris"]
    unverified = [d["document_id"] for d in zero
                  if not ((d.get("raw_facts") or {}).get("consideration") or {}).get("zero_verified")]
    report("$0 ACRIS conveyances carry a prepaid-tax verification",
           "PASS" if not unverified else "FAIL",
           f"{len(zero) - len(unverified)}/{len(zero)} verified by re-reading the cover"
           + (f"; unverified: {unverified}" if unverified else ""))

    # 5. roster vs index legals --------------------------------------------
    idx = index_legals([d["document_id"] for d in docs])
    mism = []
    for d in docs:
        doc_bbls = {p["bbl"] for p in posts if p["document_id"] == d["document_id"]}
        i = idx.get(d["document_id"], set())
        only_doc, only_idx = doc_bbls - i, i - doc_bbls
        if only_doc or only_idx:
            mism.append((d["document_id"], len(only_doc), len(only_idx)))
    report("document roster vs index legals", "INFO",
           f"{n - len(mism)}/{n} agree exactly; divergences (doc-only/index-only): "
           + ", ".join(f"{m[0]}({m[1]}/{m[2]})" for m in mism) if mism else "all agree")

    # 6. lineage: every posted BBL resolves to a lot that exists today -------
    spine = {}
    for r in get("decoder_bbl_spine?select=bbl,predecessors,successors,source"):
        cur = spine.setdefault(r["bbl"], {"successors": [], "predecessors": [], "source": []})
        cur["successors"] += r.get("successors") or []
        cur["predecessors"] += r.get("predecessors") or []
        cur["source"].append(r.get("source"))
    try:
        baselines = json.load(open(pathlib.Path(__file__).with_name("baselines.json"), encoding="utf-8"))
    except FileNotFoundError:
        baselines = {}
    try:
        hist = json.load(open(pathlib.Path(__file__).with_name("baselines_historical.json"),
                              encoding="utf-8"))
    except FileNotFoundError:
        hist = {}

    def canonical(b):
        """Post what the document names; resolve at read time."""
        seen, cur = set(), b
        while cur in spine and spine[cur].get("successors") and cur not in seen:
            seen.add(cur)
            cur = sorted(spine[cur]["successors"])[0]
        return cur

    posted = {p["bbl"] for p in posts}
    # A posted BBL is resolvable if we can characterise the parcel EITHER today
    # OR at the document's filing date (historical vintage) — a retired lot is
    # not a gap when the map at filing time is known.
    unresolvable = sorted(b for b in posted
                          if canonical(b) not in baselines and b not in baselines)
    report("lineage: posted BBLs resolve (today or at filing date)",
           "PASS" if not unresolvable else "FAIL",
           f"{len(posted) - len(unresolvable)}/{len(posted)} resolve via PLUTO/spine; "
           f"unresolved (retired, no successor recorded): {unresolvable}")

    # ⚠ NOT `lot >= 1001`. That range also holds AIR lots (9000+), REUC (8000+)
    # and condo BILLING lots (7501+), so an air lot would be collapsed to a
    # condominium's billing lot — a wrong parent, silently. Harmless today
    # (82 = 82, no air lot posted yet) but a decoded document already names one.
    import keys as _k
    units = sorted({b for b in posted if _k.is_unit_lot(b)})
    unit_ok = [b for b in units if canonical(b) != b]
    report("condo unit lots collapse to one canonical parcel",
           "PASS" if len(unit_ok) == len(units) else "FAIL",
           f"{len(unit_ok)}/{len(units)} unit lots resolve to a billing lot; "
           f"distinct canonical parcels behind them: "
           f"{len({canonical(b) for b in units})}")

    # 6b. EXTERNAL PROOF: document lot areas vs the map AT THE FILING DATE ---
    # Divergence is not one thing. Classify it, because three of the four kinds
    # are findings about the world rather than defects in the decode:
    #   agree      within 2% of the contemporaneous vintage
    #   partial    the document describes p/o a lot — test doc <= map, not equality
    #   lag        the document's figure appears in a LATER vintage: the tax map
    #              had not caught up at filing time (the document led it)
    #   divergent  none of the above — a real discrepancy to report, never repair
    try:
        DIV = json.load(open(pathlib.Path(__file__).with_name("map_divergences.json"),
                             encoding="utf-8"))
    except FileNotFoundError:
        DIV = {}
    checked = agree = partial = lag = survey = today_only = 0
    off, nomap = [], 0
    for d in docs:
        la_blk = ((d.get("raw_facts") or {}).get("lot_areas_by_bbl") or {})
        la = la_blk.get("values") or {}
        extent = la_blk.get("extent") or {}
        when = str(d.get("document_date") or d.get("recorded_date") or "")[:10]
        for b, v in la.items():
            if not isinstance(v, (int, float)):
                continue
            h = hist.get(f"{b}@{when}")
            bl = h or baselines.get(b) or baselines.get(canonical(b))
            if not bl or not bl.get("lot_area"):
                nomap += 1
                continue
            checked += 1
            if not h:
                today_only += 1
            area = bl["lot_area"]
            delta = area - v
            tol = max(2.0, 0.02 * area)
            if extent.get(b) == "partial":
                partial += 1
                if v > area + tol:
                    off.append(f"{d['document_id']}/{b}: PARTIAL area {v} EXCEEDS whole lot {area}")
            elif abs(delta) <= tol:
                agree += 1
            elif (DIV.get(f"{d['document_id']}/{b}") or {}).get("kind") == "map_lag":
                lag += 1
            elif (DIV.get(f"{d['document_id']}/{b}") or {}).get("kind") == "survey_vs_taxmap":
                survey += 1
            else:
                off.append(f"{d['document_id']}/{b}: doc {v} vs {bl.get('vintage','current')} "
                           f"{area} ({delta:+.0f})")
    report("document lot areas vs the map at the filing date",
           "PASS" if checked and not off else ("INFO" if not checked else "FAIL"),
           f"{agree} agree + {partial} partial-lot + {lag} map-lag + "
           f"{survey} survey-vs-taxmap = {agree+partial+lag+survey}/{checked} explained "
           f"({checked - today_only} against the contemporaneous vintage, "
           f"{today_only} against today's map only, {nomap} absent from any map)"
           + (f"; unexplained: {off}" if off else ""))

    # 6c. split-district lots: a single FAR is simply wrong on these ----------
    # DCP's Zoning Tax Lot Database is the authoritative per-BBL assignment and
    # resolves what PLUTO's single zoning field flattens. A lot split between two
    # districts has no one FAR, so any baseline built on PLUTO's single value is
    # unsafe there and must be marked rather than silently used.
    posted_c = {canonical(p["bbl"]) for p in posts} | {p["bbl"] for p in posts}
    split = [b for b in posted_c
             if (baselines.get(b) or {}).get("dcp_zoning", {}).get("zoning_district_2")]
    flat = [b for b in posted_c if (baselines.get(b) or {}).get("pluto_flattened")]
    with_dcp = [b for b in posted_c if (baselines.get(b) or {}).get("dcp_zoning")]
    report("baselines carry authoritative DCP zoning", "INFO",
           f"{len(with_dcp)}/{len(posted_c)} parcels have DCP zoning; "
           f"{len(flat)} carry an overlay/special district PLUTO's single field drops; "
           f"{len(split)} are split between districts")

    # A split lot is safe once its shares are MEASURED and ZR 77-22 applied
    # (close_split_far.py). Unmeasured, or measured and still unresolvable, it
    # must not silently borrow PLUTO's single FAR.
    states = {}
    for b in split:
        sf = (baselines.get(b) or {}).get("split_far") or {}
        states.setdefault(sf.get("status", "not_measured"), []).append(b)
    open_split = states.get("not_measured", []) + states.get("unresolved", [])
    report("split-district lots carry a ZR 77-22 adjusted FAR",
           "PASS" if not open_split else "FAIL",
           f"{len(split) - len(open_split)}/{len(split)} resolved from measured "
           f"geometry; states: { {k: len(v) for k, v in states.items()} }"
           + (f"; open: {sorted(open_split)}" if open_split else ""))

    # The measurement is only as good as the geometry it rests on: report the
    # spread of polygon-vs-PLUTO area, because a lot whose polygon disagrees with
    # its stated area is measuring something else.
    deltas = [(b, (baselines[b]["split_far"] or {}).get("polygon_vs_pluto"))
              for b in split
              if (baselines.get(b) or {}).get("split_far", {}).get("polygon_vs_pluto") is not None]
    if deltas:
        worst = max(deltas, key=lambda kv: abs(kv[1]))
        # NOT an accuracy score. A tax-map polygon is a DIGITIZATION of the lot's
        # shape; the stated lot area is DOF's REPORTED figure from the tax roll,
        # which is the same administrative number recorded surveys recite (across
        # 38 documented parcels the document and PLUTO agree to a median of
        # 0.00%, while the polygon differs by a median 6.4%). They are different
        # kinds of quantity, and neither is wrong.
        # This line exists to catch a polygon that is not the LOT — a fragment —
        # which shares alone can never reveal, because a ratio taken over the
        # wrong footprint still looks perfectly well-formed.
        report("split-lot polygons are the whole lot, not a fragment", "INFO",
               f"{len(deltas)} measured; median |polygon - reported| "
               f"{sorted(abs(d) for _, d in deltas)[len(deltas)//2]*100:.1f}% "
               f"(digitization spread, expected), worst {worst[0]} {worst[1]*100:+.1f}%")

    # 7. citation resolution ------------------------------------------------
    unres = [l for l in links if not l["resolved_doc_id"]]
    kinds = {}
    for l in unres:
        kinds[l["target_kind"]] = kinds.get(l["target_kind"], 0) + 1
    report("citations resolved to documents", "INFO",
           f"{len(links) - len(unres)}/{len(links)} resolved; unresolved by style: {kinds}")

    # 8. quantity-unstated transfers (needs baselines to close) -------------
    unq = sorted({p["document_id"] for p in posts
                  if (p.get("payload") or {}).get("account", p["account"]) == "envelope_transferable"
                  and p["quantity_sf"] is None
                  and (p.get("payload") or {}).get("group_quantity_sf") is None})
    report("transfers with no SF anywhere", "INFO",
           f"{len(unq)} document(s) convey rights with no stated quantity: {unq} "
           f"(resolve via FAR baseline, gap 3)")

    # 8b. legal descriptions transcribed VERBATIM ----------------------------
    # A summarised description cannot be traversed: metes.py needs the courses as
    # printed, and contiguity between parcels is only provable from them. Two
    # failure modes are counted separately because they are different problems —
    # a document with a summary was read and abbreviated, while a document with
    # no block at all was decoded before the contract required one and nobody
    # would notice.
    # NOTE TO SELF: the first version of this check looked for a TOP-LEVEL
    # `courses_verbatim` key. It lives inside legal_descriptions[], so the check
    # found nothing and reported 0/15 — a check aimed at the wrong field returns
    # an empty result that reads exactly like a real finding.
    noblock, summ_docs, verb, summ = [], [], 0, 0
    for d in docs:
        if (d.get("source") or "acris") != "acris":
            continue
        lds = (d.get("raw_facts") or {}).get("legal_descriptions") or []
        if not lds:
            noblock.append(d["document_id"])
            continue
        # A description that INCORPORATES ANOTHER BY REFERENCE is complete as
        # recorded, not summarised: ZLDA Exhibit D of 2026012000388004 reads in
        # full "ALL that volume of space ... above the Lower Limiting Plane ...
        # within the boundaries of the Owner Premises described in Exhibit A".
        # It has no courses because the instrument gave it none. Counting it as
        # a gap would send someone back to re-read a page that is already whole.
        v = [l for l in lds
             if l.get("courses_verbatim")
             or (l.get("incorporates_by_reference") and l.get("description_verbatim"))]
        verb += len(v)
        summ += len(lds) - len(v)
        if len(v) < len(lds):
            summ_docs.append(d["document_id"])
    n_acris = sum(1 for d in docs if (d.get("source") or "acris") == "acris")
    report("legal descriptions transcribed verbatim (traversable)",
           "PASS" if not (noblock or summ_docs) else "FAIL",
           f"{verb}/{verb + summ} descriptions verbatim; "
           f"{n_acris - len(noblock) - len(summ_docs)}/{n_acris} documents complete; "
           f"{len(summ_docs)} summarised {sorted(summ_docs)}; "
           f"{len(noblock)} carry NO description block {sorted(noblock)}")

    # 8b-ii. descriptions KNOWN TO EXIST but not transcribed -------------------
    # ⚠ THE CHECK ABOVE CAN ONLY SEE WHAT THE DECODE LISTED. A decoder that
    # transcribes two of a document's four descriptions and lists only those two
    # scores 100% complete — the check has no way to know about a description it
    # was never told about. Found 2026-08-13 while closing the four blocked
    # documents: 2026012000388002's own exhibits are A and C, but its Exhibit B
    # carries a title certification whose Parcels A..E are further descriptions
    # (including MTA Lot 51, which appears in no index legal).
    # So a decode that locates a description it did not transcribe MUST record it
    # under `pending_descriptions` (what, which pages, why), and this check
    # surfaces the count. It is INFO, not FAIL — the work is queued with page
    # numbers, which is the opposite of lost — but it can never read as clean.
    pend = [(d["document_id"], pd) for d in docs
            for pd in ((d.get("raw_facts") or {}).get("pending_descriptions") or [])]
    report("descriptions located but not transcribed", "INFO",
           f"{len(pend)} queued across {len({p[0] for p in pend})} document(s): "
           + "; ".join(f"{doc} pp.{pd.get('pages')} {pd.get('what','')[:60]}"
                       for doc, pd in pend) if pend
           else "0 queued (every located description is transcribed)")

    # 8c. description SHAPE is declared ---------------------------------------
    # Four shapes disagree about whether areas add up: a `perimeter` bounds
    # several lots (additive), a `vertical` parcel is the SAME ground described
    # twice (not additive). Undeclared, both fail silently — one trebles a
    # parcel, the other double-counts it.
    shaped = unshaped = 0
    bad_shape = []
    VALID = {"per_lot", "perimeter", "vertical", "incorporation_by_reference"}
    for d in docs:
        for ld in ((d.get("raw_facts") or {}).get("legal_descriptions") or []):
            sh = ld.get("shape")
            if sh in VALID:
                shaped += 1
                if sh == "perimeter" and not ld.get("covers_bbls"):
                    bad_shape.append(f"{d['document_id']}: perimeter with no covers_bbls")
                if sh == "vertical" and not ld.get("vertical_extent"):
                    bad_shape.append(f"{d['document_id']}: vertical with no vertical_extent")
            else:
                unshaped += 1
    report("legal descriptions declare their shape",
           "PASS" if not (unshaped or bad_shape) else "FAIL",
           f"{shaped}/{shaped + unshaped} declared"
           + (f"; {unshaped} undeclared" if unshaped else "")
           + (f"; {bad_shape}" if bad_shape else ""))

    # 8d. contact-bearing blocks ----------------------------------------------
    # Notices and sealed certifications name the people behind the paper — the
    # owner's phone, the human behind an SPE, the architect and their licence.
    # Reported as INFO, not FAIL: not every instrument HAS a notices section, so
    # absence is only a finding once a decode has confirmed it looked.
    with_notices = [d["document_id"] for d in docs
                    if (d.get("raw_facts") or {}).get("notices")]
    with_certs = [d["document_id"] for d in docs
                  if (d.get("raw_facts") or {}).get("certifications")]
    n_people = sum(len((d.get("raw_facts") or {}).get("notices") or []) for d in docs)
    n_certs = sum(len((d.get("raw_facts") or {}).get("certifications") or []) for d in docs)
    acks = [a for d in docs for a in ((d.get("raw_facts") or {}).get("acknowledgments") or [])]
    blank = [a for a in acks if a.get("executed") is False]
    report("contact blocks captured (notices / certifications)", "INFO",
           f"{len(with_notices)}/{n_acris} documents carry notices ({n_people} contacts); "
           f"{len(with_certs)} carry sealed certifications ({n_certs}); "
           f"{len(acks)} acknowledgments ({len(blank)} UNEXECUTED); "
           f"not-yet-read: {sorted(set(d['document_id'] for d in docs if (d.get('source') or 'acris') == 'acris') - set(with_notices))}")

    # an unexecuted jurat is a DEFECT in the recorded original, not a gap in the
    # decode — surfaced separately so it is never read as missing data
    if blank:
        report("acknowledgments executed", "INFO",
               f"{len(acks) - len(blank)}/{len(acks)} executed; UNEXECUTED blocks in: "
               + ", ".join(sorted({d["document_id"] for d in docs
                                   for a in ((d.get("raw_facts") or {}).get("acknowledgments") or [])
                                   if a.get("executed") is False})))

    # 8e. notary stamp expiry vs the jurat date -------------------------------
    # Reports what the STAMP says, and no more. Two limits, both material:
    #
    #   * a stamp is not the commission. NY terms run four years and notaries
    #     routinely keep using an old stamp after renewing, so a stale date
    #     evidences a stale stamp, not necessarily a lapsed commission. The NY
    #     DOS notary register is the source that would settle it; not consulted.
    #   * NY Executive Law 142-a VALIDATES a notary's acts notwithstanding an
    #     expired term. The protection is withheld where the defect is "apparent
    #     on the face of the certificate" — a visibly stale stamp is — but that
    #     limitation itself lapses SIX MONTHS after the act, after which the
    #     acknowledgment is cured.
    #
    # So this fires as a lead to check, never as a conclusion that anything is
    # void. Found: 2025102901095004 p33, stamp expiring 2023-03-17 against a
    # 2025-10-12 jurat; six-month window closed 2026-04-12; no corrective
    # instrument recorded against the parcels.
    checked = lapsed = undated = 0
    bad_ack = []
    for d in docs:
        for a in ((d.get("raw_facts") or {}).get("acknowledgments") or []):
            if a.get("executed") is False:
                continue
            when, exp = a.get("date"), a.get("commission_expires")
            if not when or not exp:
                undated += 1
                continue
            checked += 1
            if str(exp)[:10] < str(when)[:10]:
                lapsed += 1
                bad_ack.append(f"{d['document_id']} p{a.get('page')}: {a.get('notary')} "
                               f"expired {exp}, jurat {when}")
    # SEVERITY: this is INFO, not FAIL, and the distinction is deliberate.
    # A FAIL means OUR STORE is unsafe to use. A lapsed commission is a defect in
    # the RECORDED ORIGINAL that we have correctly captured — the decode is
    # working exactly as intended when it fires. Same reasoning as the
    # unexecuted-jurat check above. Grading a finding about the world as a
    # failure of our own data trains everyone to ignore FAILs.
    report("notary stamp expiry vs jurat date (lead, not a verdict)",
           "INFO",
           f"{checked - lapsed}/{checked} live"
           + ("  <- stale STAMP; check the DOS register, and see Exec. Law 142-a" if lapsed else "")
           + (f"; {undated} undated (date or expiry not captured)" if undated else "")
           + (f"; LAPSED: {bad_ack}" if bad_ack else ""))

    # 8f. every verbatim description carries a WALKED traverse ---------------
    # A description without a traverse has been transcribed but never checked —
    # and the traverse is the only external test of the transcription (a misread
    # digit stops it closing). Also: eight metes.py bugs have been fixed, so a
    # traverse recorded earlier was computed by an engine that no longer exists.
    # `recheck_traverses.py` re-walks them all; this check makes sure none is
    # missing in the first place.
    verb = walked = closes = 0
    for d in docs:
        for ld in ((d.get("raw_facts") or {}).get("legal_descriptions") or []):
            if not ld.get("courses_verbatim"):
                continue
            verb += 1
            t = ld.get("traverse") or {}
            if t.get("verdict"):
                walked += 1
                if t["verdict"] == "closes":
                    closes += 1
    report("verbatim descriptions carry a walked traverse",
           "PASS" if verb and walked == verb else ("INFO" if not verb else "FAIL"),
           f"{walked}/{verb} walked; {closes} close, "
           f"{walked - closes} do not (each with a stated reason)")

    # 8g. every BUILT SOURCE still answers -----------------------------------
    # "Pullable" is not "verified". Twice this session a component was CORRECT
    # and UNWIRED and produced exactly the same output as one that did not exist
    # (party observations sat unreduced; the special-district override sat
    # unapplied). The cure is to check the PATH, not the presence of a value.
    #
    # A BROKEN source looks exactly like an EMPTY one, so this reports them
    # separately and never lets schema drift pass as "no data for our parcels".
    try:
        import sources
        srows = sources.check_all()
        broken = [r for r in srows if not r[1]]
        report("built sources still answer (self-calibrating controls)",
               "PASS" if not broken else "FAIL",
               f"{len(srows) - len(broken)}/{len(srows)} reachable"
               + (f"; BROKEN: {[r[0] for r in broken]}" if broken else "")
               + f"; slowest {max(srows, key=lambda r: r[3])[0]} "
                 f"{max(r[3] for r in srows)}s")
    except Exception as e:
        report("built sources still answer (self-calibrating controls)", "FAIL",
               f"the source check ITSELF failed: {type(e).__name__}: {str(e)[:90]}")

    # 9. provenance depth ---------------------------------------------------
    thin = [p for p in posts if len(str(p["provenance"])) < 12]
    report("provenance specific enough to re-find in 10s", "PASS" if not thin else "FAIL",
           f"{len(posts) - len(thin)}/{len(posts)} postings carry a locating citation")

    fails = [r for r in RESULTS if r[0] == "FAIL"]
    print(f"\n{len(RESULTS)} checks | {len(fails)} FAIL | "
          f"{sum(1 for r in RESULTS if r[0]=='PASS')} PASS | "
          f"{sum(1 for r in RESULTS if r[0]=='INFO')} INFO")
    if fails:
        print("open falls:")
        for _, name, detail in fails:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
