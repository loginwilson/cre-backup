"""DCP / ZAP — where the parcel key went, and how to get it back.

THE FINDING THIS MODULE EXISTS FOR

    The Socrata export of the Zoning Application Portal (hgx4-8ukb, 32,931
    projects) has NO BBL, NO BLOCK, NO LOT and NO ADDRESS. The finest geography
    it carries is the community district. So every DCP land-use action — every
    rezoning, every CPC special permit — is unattachable to a parcel from the
    open-data feed alone.

    The ZAP application itself has them. Its config is published in the page's
    own <meta name="labs-zap-search/config/environment"> tag, which names the
    API it reads:

        host = https://zap-api-production.herokuapp.com

    and GET /projects/<project_id> returns, among other things:

        bbls                    ['3074230011','3074230036','3074230038']
        bbl-featurecollection   the same lots as geometry
        dcp-bsanumber           <- a BSA calendar number, when there is one
        dcp-lpcnumber           <- an LPC number, when there is one
        artifacts / packages    the filed documents, on SharePoint

    ★ dcp-bsanumber and dcp-lpcnumber are the reason this is worth more than a
      BBL lookup. They are DCP asserting, in its own record, that this project
      is the same matter as a BSA case and an LPC action. That is a join across
      all three of this chat's sources that none of the three feeds publishes.

⚠ ACCESS, STATED HONESTLY

    zap.planning.nyc.gov publishes `Allow: /` — fully permissive. The API host
    is a heroku app that returns 404 on its own robots.txt, so it publishes no
    policy of its own. It is the backend the permitted public site calls to
    render a public page, and every field returned is already displayed on that
    page. That is the basis for reading it, and it is a judgement rather than a
    stated permission — so: one request at a time, paced, and stop on any
    refusal. No concurrency.

⚠ THE ACTION IS NOT IN THE `actions` COLUMN

    Measured on all 32,931 rows: `actions` is populated on 1,480 — 4.5%. The
    ULURP number encodes the same thing ('220026ZMK' = ZM, Brooklyn) and parses
    on 27,968 — 84.9%. A census taken from the column understates every action
    type ~19x.
"""
import json, os, pathlib, re, sys, time, urllib.error, urllib.request
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk
import facts as F
import runlock
import sink

SOURCE = "DCP"
ZAP = "hgx4-8ukb"                  # 32,931 projects, no parcel key
API = "https://zap-api-production.herokuapp.com"
UA = ("BSA-decoder/1.0 (NYC parcel research, public ZAP records; "
      "contact loginwilson88@gmail.com)")
PACE = 1.5
_last = [0.0]

LEDGER = pathlib.Path(os.environ.get(
    "DCP_LEDGER", pathlib.Path(__file__).with_name("dcp_ledger.jsonl")))
# the `source_documents` coverage table from LEDGER_SCHEMA.md — one row per
# document that EXISTS, whether or not it has been read. Written before any
# retrieval is attempted, because "no facts in this project" and "never opened
# this project's documents" are opposite statements that look identical unless
# something records the difference.
DOCS = pathlib.Path(os.environ.get(
    "DCP_DOCS", pathlib.Path(__file__).with_name("dcp_documents.jsonl")))

# what a filed document is, read off its own filename. DCP names its artifacts
# descriptively, so the inventory is classifiable without opening anything —
# which is exactly as far as an index is allowed to take you.
DOC_TYPE = [
    ("zoning_comparison_table", r"zoning\s*comparison|conformance.{0,12}compliance|bulk\s*table"),
    ("zoning_change_map", r"zoning\s*(change\s*)?map|rezoning\s*map"),
    ("project_description", r"project\s*description|LR\s*(item\s*)?3"),
    ("eas", r"\bEAS\b|environmental\s*assessment"),
    ("eis", r"\bEIS\b|environmental\s*impact"),
    ("technical_memorandum", r"technical\s*memo"),
    ("mih_text", r"\bMIH\b|appendix\s*f|inclusionary"),
    ("cpc_report", r"\bCPC\b|city\s*planning\s*commission\s*report"),
    ("council_resolution", r"council\s*resolution|\bcc\s*resolution"),
    ("restrictive_declaration", r"restrictive\s*declaration|\bRD\b"),
    ("site_plan", r"site\s*plan|survey"),
    ("tax_map", r"tax\s*map"),
    ("land_use_map", r"land\s*use|area\s*map"),
    ("site_photos", r"site\s*photos?|photographs?"),
    ("waterfront", r"waterfront|WRP"),
    ("racial_equity_report", r"racial\s*equity"),
    ("signature_form", r"signature\s*form|authorization\s*letter"),
    ("notice", r"notice\s*of\s*receipt|lead\s*agency|filing\s*receipt"),
]


def doc_type(name):
    """⚠ NORMALISE BEFORE MATCHING. DCP names its files with hyphens and a
    leading index — `01.-Project-Description.pdf`, `06.-Owners--Authorization-
    Letters.pdf`, `LandUse.pdf`. Patterns written with `\\s*` between words match
    none of them, and the first run classified 64 of 65 documents as
    'unclassified' while looking like it had a working classifier."""
    s = re.sub(r"[-_.]+", " ", name or "")
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)     # LandUse -> Land Use
    s = re.sub(r"^\s*\d{1,3}\s+", "", s)           # drop the ordering prefix
    for kind, pat in DOC_TYPE:
        if re.search(pat, s, re.I):
            return kind
    return "unclassified"

BOROUGH_LETTER = set("MXKQRY")
ULURP = re.compile(r"(\d{6})\s*([A-Z]{2,4})")

ACTION_MEANING = {
    "ZM": "zoning map amendment — the district itself changes",
    "ZS": "CPC special permit — conditions bind the site",
    "ZR": "zoning text amendment",
    "ZC": "certification",
    "ZA": "authorization",
    "ZJ": "zoning special permit (joint)",
    "RC": "renewal / close-out",
    "PP": "disposition of city property",
    "HK": "housing action (UDAAP / HPD)",
    "HD": "housing disposition",
}
ENVELOPE_ACTIONS = ("ZM", "ZS", "ZR", "ZC", "ZA", "ZJ")


def action_codes(row):
    """Action codes for a project, from the ULURP number rather than the
    `actions` column — see the module docstring for why."""
    out = set()
    for _, code in ULURP.findall(row.get("ulurp_numbers") or ""):
        out.add(code[:-1] if len(code) >= 3 and code[-1] in BOROUGH_LETTER else code)
    return sorted(out)


# same discipline as LPC — the ZAP export has 35 columns and the decoder reads
# eight of them. The parcel key is not in any of them; it comes from the API.
ZAP_COLUMNS = ("project_id,project_name,project_brief,ulurp_numbers,borough,"
               "public_status,project_status,certified_referred,approval_date,"
               "completed_date,app_filed_date,primary_applicant,actions")


def index(where=None):
    return bulk.socrata(ZAP, where=where, select=ZAP_COLUMNS)


def queue(envelope_only=False):
    """⚠ THE DEFAULT USED TO BE envelope_only=True, AND THAT WAS A GAP.

    Filtering to the 7,102 zoning-action projects meant the documents of the
    other 25,829 were never catalogued at all — not read, not listed, not
    counted. A project absent from the coverage table is the one failure the
    table exists to prevent: nothing downstream can know to look for it.

    Priority still favours the envelope actions (they sort first). Scope now
    covers everything. Order decides what a partial run is worth; scope decides
    whether the record is complete.
    """
    return _queue(envelope_only)


def _queue(envelope_only=True):
    """The projects worth resolving to parcels, highest signal first."""
    rows = index()
    out = []
    for r in rows:
        codes = action_codes(r)
        if envelope_only and not any(c in ENVELOPE_ACTIONS for c in codes):
            continue
        out.append({**r, "action_codes": codes})
    # ⚠ ORDER IS NOT COSMETIC, AND THIS IS THE SECOND TIME IT BIT. Measured on
    # the first 285 projects pulled: 205 returned NO BBLs, and every single one
    # of those 205 had a `P`-prefixed project id — P1977K0071, P1977Q0168 —
    # legacy records migrated into ZAP from the paper era with no geography and
    # no documents attached. 90% of the envelope-action queue (6,391 of 7,102)
    # is P-prefixed, so an order that front-loads them spends nine tenths of the
    # run before reaching anything with a parcel on it.
    #
    # The same shape as the BSA queue sorted newest-first straight into the
    # unpublished decisions. A queue's ORDER decides what a partial run is worth.
    rank = {c: i for i, c in enumerate(ENVELOPE_ACTIONS)}
    def key(r):
        pid = str(r.get("project_id") or "")
        legacy = pid.startswith("P")
        year = pid[1:5] if legacy else pid[:4]
        return (1 if legacy else 0,                       # modern first
                -int(year) if year.isdigit() else 0,      # newest first
                min((rank.get(c, 99) for c in r["action_codes"]), default=99))
    out.sort(key=key)
    return out


def project(project_id, attempts=4):
    """One ZAP project, paced, with backoff on transient failures.

    ⚠ A SINGLE 503 USED TO END A 32,931-PROJECT SWEEP. The API is a heroku app
    and will occasionally return 503 or drop a connection over a run measured in
    hours. Without a retry, one blip 13 hours in loses the tail of the sweep and
    the ledger simply stops — which reads as "the corpus ends here" rather than
    "the network hiccuped". Backing off is also the polite response to a 503:
    the server is saying it is busy.
    """
    last = None
    for n in range(attempts):
        wait = PACE - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(f"{API}/projects/{project_id}",
                                         headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404):
                raise                     # a real answer, not a hiccup
            last = e
        except Exception as e:
            last = e
        time.sleep(min(2 ** n * 3, 45))
    raise last


def read_project(payload):
    """The parcel key, the cross-source links, and the document inventory."""
    a = (payload.get("data") or {}).get("attributes") or {}
    inc = payload.get("included") or []
    # ⚠ THE API LISTS THE SAME FILE UNDER SEVERAL CONTAINERS. A document that
    # belongs to both an `artifact` and a `package` is returned once per
    # container — measured up to SEVEN times for one file, and 787 distinct
    # documents arriving as 1,519 rows. Identity is the SharePoint
    # serverRelativeUrl (a content-addressed token), falling back to the
    # filename. Same shape as the duplicated BBLs: the API repeats, and storing
    # raw inflates every count downstream by an amount nobody can see.
    docs, seen = [], set()
    raw = 0
    for x in inc:
        if x["type"] not in ("artifacts", "packages"):
            continue
        at = x.get("attributes") or {}
        for f in (at.get("documents") or []):
            raw += 1
            ident = f.get("serverRelativeUrl") or f.get("name")
            if ident in seen:
                continue
            seen.add(ident)
            docs.append({"kind": x["type"], "artifact": at.get("dcp-name"),
                         "file": f.get("name"),
                         "location": at.get("dcp-artifactdocumentlocation"),
                         "server_relative_url": f.get("serverRelativeUrl"),
                         "created": f.get("timeCreated")})
    acts = [{"name": (x.get("attributes") or {}).get("dcp-name"),
             "code": (x.get("attributes") or {}).get("dcp-action-value"),
             "ulurp": (x.get("attributes") or {}).get("dcp-ulurpnumber"),
             "status": (x.get("attributes") or {}).get("statuscode"),
             "zr": (x.get("attributes") or {}).get("dcp-zoningresolution-value"),
             # ★ THE FINAL ENTITLEMENT INSTRUMENT. A ULURP action that reaches
             # the City Council is approved THERE, often with modifications, and
             # the Council resolution — not the CPC report — is what binds. The
             # number is in this payload and nothing else publishes the link.
             "cc_resolution": (x.get("attributes") or {}).get("dcp-ccresolutionnumber")}
            for x in inc if x["type"] == "actions"]
    return {
        "project_id": a.get("dcp-name"),
        "project_name": a.get("dcp-projectname"),
        # ⚠ THE API REPEATS BBLs. Measured over 1,395 resolved projects: 412
        # (29.5%) carry at least one duplicate, 478 duplicate slots in 20,597 —
        # 2.3%. P2017R0264 returns ['5006270007','5006270007']; P2013X0354
        # repeats 2022940030. Stored raw, a parcel is counted twice by anything
        # that counts, and at 20,000 rows nobody notices. Deduped in document
        # order, because order is the only thing the API's sequence carries.
        "bbls": list(dict.fromkeys(str(b) for b in (a.get("bbls") or []))),
        "bbls_raw_count": len(a.get("bbls") or []),
        "has_geometry": bool(a.get("bbl-featurecollection")),
        "borough": a.get("dcp-borough"),
        "community_districts": a.get("dcp-validatedcommunitydistricts"),
        "status": a.get("dcp-publicstatus"),
        "ulurp_non": a.get("dcp-ulurp-nonulurp"),
        "certified": a.get("dcp-certifiedreferred"),
        "completed": a.get("dcp-projectcompleted"),
        "brief": (a.get("dcp-projectbrief") or "")[:1200],
        # ★ the cross-source links no feed publishes
        "bsa_number": a.get("dcp-bsanumber"),
        "lpc_number": a.get("dcp-lpcnumber"),
        "ceqr_number": a.get("dcp-ceqrnumber"),
        "applicant_team": a.get("applicantteam") or [],
        "actions": acts,
        "documents": docs,
        "documents_raw_count": raw,
    }


def to_facts(d, run_id=None, emit=True):
    """DELIBERATELY EMITS NOTHING. Read the paragraph before changing this.

    ⚠ THIS FUNCTION USED TO WRITE FACTS, AND IT WAS WRONG TO.

    RULE_DOCUMENTS_NOT_INDEXES.md: *"do not write a fact whose only source is an
    index row, a search result, or a summary/detail screen."*

    A ZAP project record is precisely a detail screen. It is generated from
    DCP's case-management system, not read off a filed page. Every fact this
    function emitted carried `page="project-record"` — which is not a page, and
    the field was doing nothing except satisfying a validator that exists to
    stop this exact thing. `document_id` + `page` means *walk me back to the
    paper*, and there was no paper to walk back to.

    The real documents ARE catalogued here — 10,429 of them across 327 projects,
    with names that state their own contents (`10. Zoning Comparison Table.pdf`,
    `11. Zoning Change Map.pdf`, the EAS). They sit on SharePoint and every
    retrieval form returns **HTTP 401**. So DCP's honest position is:

        finding aid   COMPLETE   — 1,983 BBLs and 10,429 document names, which
                                   is legitimate index work, use #1 in the rule
        decode        NOT STARTED — zero documents read, therefore zero facts

    Those two must not be allowed to look alike, which is the whole point of
    reporting `complete with 0 facts` differently from `never ran`. DCP has run;
    it has read nothing; it asserts nothing.

    What the run produces instead is `source_documents` ledger rows — the
    coverage table from LEDGER_SCHEMA.md, recording WHAT EXISTS AND HAS NOT BEEN
    READ. That is the single most important thing to store, and it is the only
    defence against a timeline that looks complete and is not.

    This function starts emitting again when, and only when, a DCP document has
    actually been opened and read to its last page.
    """
    return []


def _append(path, rec):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, separators=(",", ":"), default=str) + "\n")
        f.flush()


def done_already():
    if not LEDGER.exists():
        return set()
    out = set()
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("status") in ("resolved", "no_bbl"):
                out.add(r["project_id"])
    return out


def run(rows, run_id=None, emit=True, beat_every=25):
    run_id = run_id or f"dcp-{int(time.time())}"
    # ⚠ ONE WRITER PER SOURCE. Three separate corruptions came from two
    # processes appending to the same ledger; see runlock.py.
    _lock = runlock.Lock(SOURCE, run_id).acquire(script="dcp.py")
    total = len(rows)
    seen = done_already()
    counts = Counter()
    sink.heartbeat(SOURCE, run_id, done=0, total=total,
                   note=f"{len(seen)} already resolved")
    for i, r in enumerate(rows, 1):
        pid = r.get("project_id")
        if pid in seen:
            counts["skipped"] += 1
            continue
        try:
            d = read_project(project(pid))
            n = len(d["bbls"])
            counts["resolved" if n else "no_bbl"] += 1
            counts["bbls"] += n
            counts["with_bsa"] += bool(d["bsa_number"])
            counts["with_lpc"] += bool(d["lpc_number"])
            counts["documents"] += len(d["documents"])
            fs = to_facts(d, run_id=run_id, emit=emit)   # returns [] by design
            counts["facts"] += len(fs)
            # the coverage table: every document that exists, marked UNREAD.
            name_counts = Counter(x.get("file") for x in d["documents"])
            for doc in d["documents"]:
                kind = doc_type(doc.get("file"))
                counts[f"doc:{kind}"] += 1
                # ⚠ A DCP FILENAME IS NOT A DOCUMENT ID. Measured over 20,415
                # (project, file) pairs: only 18,598 distinct filenames, and
                # `LandUse.pdf` is used by 2,049 SEPARATE PROJECTS. 6,095
                # filenames appear in more than one project.
                #
                # decoder_documents keys on (source, source_doc_id, bbl), so a
                # bare filename merges unrelated documents about unrelated
                # parcels into one row — and the merge is silent, because an
                # upsert is exactly what you asked for. BSA's calendar number
                # and LPC's regulation number are genuinely unique; DCP has no
                # such id, so one is composed.
                # ⚠ AND A FILENAME REPEATS WITHIN A PROJECT TOO. 2019K0147
                # returns 105 documents under 63 distinct names — the same name
                # uploaded more than once, each with its OWN SharePoint token.
                # Those are separate filings, not duplicates: collapsing them on
                # name would have silently dropped 42 of 105 documents while the
                # count still looked plausible.
                #
                # So the readable id is used when a name is unique in the
                # project, and disambiguated by the token when it is not.
                # Deterministic, so re-runs converge on the same key.
                fname = doc.get("file")
                tok = (doc.get("server_relative_url") or "").strip("/")
                doc_id = (f"{pid}/{fname}" if name_counts[fname] == 1
                          else f"{pid}/{fname}#{tok[-8:]}")
                # the SHARED coverage table (LEDGER_SCHEMA table 2). A local
                # file only this chat reads is the same mistake as a retraction
                # only this chat knows about.
                sink.ledger(SOURCE, doc_id, bbls=d["bbls"],
                            doc_type=kind, decode_status="unread",
                            pages_total=None, pages_read=0, run_id=run_id,
                            project_id=pid, file_name=doc.get("file"),
                            artifact=doc.get("artifact"),
                            created=doc.get("created"),
                            location=doc.get("location"),
                            unread_reason="HTTP 401 — SharePoint requires "
                                          "authentication; access is an open "
                                          "question, not a failure")
                _append(DOCS, {
                    "source": SOURCE, "source_doc_id": doc_id,
                    "file_name": doc.get("file"),
                    "project_id": pid, "bbls": d["bbls"], "doc_type": kind,
                    "artifact": doc.get("artifact"), "kind": doc.get("kind"),
                    "created": doc.get("created"),
                    "location": doc.get("location"),
                    "server_relative_url": doc.get("server_relative_url"),
                    "decode_status": "unread",
                    "unread_reason": "HTTP 401 — SharePoint requires "
                                     "authentication; access is an open question",
                    "pages_total": None, "pages_read": 0, "run_id": run_id})
            # every Council resolution referenced is a DOCUMENT that exists
            for a in d["actions"]:
                if not a.get("cc_resolution"):
                    continue
                counts["council_resolutions"] += 1
                sink.ledger(SOURCE, f"CC-RES/{a['cc_resolution']}", bbls=d["bbls"],
                            doc_type="council_resolution", decode_status="unread",
                            pages_total=None, pages_read=0, run_id=run_id,
                            document_stream="council_resolutions",
                            project_id=pid, ulurp=a.get("ulurp"),
                            action_code=a.get("code"),
                            unread_reason="Council resolutions are published via "
                                          "Legistar; webapi.legistar.com returns "
                                          "403 'Token is required' and "
                                          "legistar.council.nyc.gov publishes no "
                                          "robots.txt (404). Retrieval is an "
                                          "ACCESS QUESTION TO ASK, not a gap.")
            _append(LEDGER, {"project_id": pid,
                             "status": "resolved" if n else "no_bbl",
                             "bbls": d["bbls"], "n_bbl": n,
                             "actions": [a.get("code") for a in d["actions"]],
                             "cc_resolutions": [a.get("cc_resolution")
                                                for a in d["actions"]
                                                if a.get("cc_resolution")],
                             "bsa_number": d["bsa_number"],
                             "lpc_number": d["lpc_number"],
                             "documents": len(d["documents"]),
                             "doc_names": [x["file"] for x in d["documents"][:40]],
                             "project_name": d["project_name"],
                             "facts": len(fs), "run_id": run_id,
                             "at": int(time.time())})
        except Exception as e:
            # ⚠ NOTHING THAT READS `d` BELONGS HERE. A patch that inserted the
            # Council-resolution loop by matching on a line present in BOTH
            # branches put it here too, where the project fetch has just failed
            # and `d` is unbound — so a transient 503 became an
            # UnboundLocalError and killed the sweep. The failure path may only
            # record the failure.
            counts["FAILED"] += 1
            _append(LEDGER, {"project_id": pid, "status": "FAILED",
                             "note": f"{type(e).__name__}: {e}",
                             "run_id": run_id, "at": int(time.time())})
        if i % beat_every == 0:
            _lock.beat()
            sink.heartbeat(SOURCE, run_id, done=i, total=total,
                           note=json.dumps(dict(counts)))
    sink.heartbeat(SOURCE, run_id, done=total, total=total,
                   status="complete" if not counts["FAILED"] else "PARTIAL",
                   note="FINDING AID ONLY — 0 documents read, therefore 0 facts "
                        "by design (RULE_DOCUMENTS_NOT_INDEXES). "
                        + json.dumps(dict(counts)))
    _lock.release()
    return {"run_id": run_id, "total": total, "counts": dict(counts)}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    # ⚠ THE FLAG THAT UNDID THE FIX. `queue()`'s default was changed to cover
    # all 32,931 projects, and this line went on passing
    # `envelope_only=not a.all_actions` — which is True unless the flag is
    # given. The default moved; the caller pinned it back. The sweep ran to
    # completion, reported success, and covered 7,102.
    #
    # A default is only a default where nobody overrides it. The narrow scope is
    # now the flag you have to ask for, so forgetting it widens rather than
    # narrows.
    ap.add_argument("--envelope-only", action="store_true",
                    help="only the 7,102 zoning-action projects (default: all "
                         "32,931 — every project's documents get catalogued)")
    ap.add_argument("--census", action="store_true")
    a = ap.parse_args()
    if a.census:
        rows = index()
        c = Counter()
        for r in rows:
            for x in action_codes(r):
                c[x] += 1
        print(f"{len(rows):,} ZAP projects")
        print(f"  with a parcel key in the export: 0")
        for k, v in c.most_common(20):
            print(f"    {k:<4} {v:>6,}  {ACTION_MEANING.get(k,'')}")
        sys.exit()
    q = queue(envelope_only=a.envelope_only)
    if a.limit:
        q = q[:a.limit]
    print(f"queue: {len(q):,} projects"
          f"{' (LIMITED — a sample, not the universe)' if a.limit else ''}")
    print(json.dumps(run(q), indent=1, default=str))
