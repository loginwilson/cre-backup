"""HOW each source is actually obtained — recorded, not remembered.

LOGIN, 2026-08-06:

    "some sites allow direct plug in, others are in preview pulling, others are
     in browser scaling. its important to record how your decoder works for our
     supabase to operate consistently"

WHY A REGISTRY AND NOT A PARAGRAPH IN A README

    Every count in Supabase means something different depending on how it was
    obtained, and the number itself does not say which. `decoder_documents` now
    holds DCP rows with decode_status='unread' and LPC rows with
    decode_status='unavailable'. Both are zero-pages-read. They are not the same
    thing, and only the RETRIEVAL METHOD explains the difference:

        DCP unread       the document exists and is published, and the fetch
                         returns HTTP 401 — an ACCESS question, still open
        LPC unavailable  the document was never published; the archive starts
                         in 2016 — a PUBLICATION fact, permanently settled

    A reader who does not know the method will treat those identically, retry
    the second forever, and conclude the first is a bug. So the method belongs
    in the database next to the rows it explains.

THE METHODS THIS PROJECT HAS ACTUALLY MET (not a taxonomy invented in advance —
each was discovered by trying)

    structured_api    a JSON feed. Free, unmetered, no document. The INDEX.
                      Socrata/ArcGIS. Never a source of facts on its own —
                      see RULE_DOCUMENTS_NOT_INDEXES.

    direct_url        the document sits at a URL you can compute from an id.
                      Plain HTTP GET. The cheapest possible retrieval, and the
                      only one that scales without a browser.
                      ⚠ Both direct_url sources here 403 the default
                        python-urllib UA. A descriptive UA gets 200. A 403 is
                        not always a refusal — sometimes it is a UA block, and
                        the difference is one header.

    app_backend_api   the page is a client-side app and its data comes from a
                      JSON backend whose host is published in the page's own
                      <meta name="…/config/environment"> tag. Reading that tag
                      is how ZAP's API was found. Unauthenticated, returns
                      everything the public page renders.

    browser_render    the served HTML is an empty shell; nothing exists until
                      the app runs. A plain fetch returns a skeleton and looks
                      like a page with no data. Needs a real browser.

    authenticated     the document is published but the fetch returns 401/403
                      to an anonymous client. NOT retrievable. Recorded as an
                      open question, never probed around.

    unpublished       a record exists in an index and no document was ever
                      posted. Permanently unreadable, and that is a fact about
                      the world rather than a gap in the work.
"""
import json, pathlib, sys, urllib.error, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))

ENV = r"C:/dev/acris-decoder.env"

DDL = """
-- run once in the Supabase SQL editor; PostgREST cannot create tables
create table if not exists decoder_source_registry (
  source            text not null,
  stream            text not null,          -- which universe within the source
  method            text not null,          -- structured_api | direct_url |
                                            -- app_backend_api | browser_render |
                                            -- authenticated | unpublished
  host              text,
  dataset_or_path   text,
  url_template      text,
  auth              text,                   -- none | user_agent | login_required
  robots_policy     text,                   -- what the host publishes, verbatim
  robots_read_how   text,                   -- how that was obtained
  pace_seconds      numeric,
  user_agent        text,
  cache_path        text,
  parser_version    text,
  universe          bigint,                 -- documents this stream contains
  retrievable       bigint,                 -- how many can actually be fetched
  retrievable_note  text,
  owner_chat        text,                   -- which decoder owns this stream
  verified_on       date,
  traps             text,
  updated_at        timestamptz default now(),
  primary key (source, stream)
);
"""

UA_DESC = ("BSA-decoder/1.0 (NYC parcel research; "
           "contact loginwilson88@gmail.com)")

# Only first-hand entries. A stream this chat does not own is recorded as
# unestablished rather than guessed — a registry that invents a method is worse
# than no registry, because it will be believed.
REGISTRY = [
    # ── BSA ────────────────────────────────────────────────────────────────
    dict(source="BSA", stream="applications_index", method="structured_api",
         host="data.cityofnewyork.us", dataset_or_path="yvxd-uipr",
         url_template="https://data.cityofnewyork.us/resource/yvxd-uipr.json",
         auth="none", robots_policy="n/a — open data API",
         robots_read_how="n/a", pace_seconds=0, user_agent=None,
         cache_path=None, parser_version="bulk.socrata",
         universe=10805, retrievable=10805,
         retrievable_note="index rows; NOT documents. Finding aid only.",
         owner_chat="BSA/LPC/DCP", verified_on="2026-08-06",
         traps="`lots` is free text truncated at 20 chars; 1,365 rows "
               "non-numeric; 'tent.' means the lot does not exist yet; index "
               "block/lot disagrees with the document on 20.4% of 2015+ cases. "
               "Sibling dataset 99rv-74dm returns 10,805 rows with ZERO KEYS — "
               "structurally empty, looks like data, is not."),
    dict(source="BSA", stream="decision_resolutions", method="direct_url",
         host="www.nyc.gov",
         dataset_or_path="/assets/bsa/downloads/pdf/decisions/",
         url_template="https://www.nyc.gov/assets/bsa/downloads/pdf/decisions/"
                      "{calendar}.pdf",
         auth="user_agent", robots_policy="User-agent: * / Disallow: /html/misc/",
         robots_read_how="GET /robots.txt with a descriptive UA. The DEFAULT "
                         "python-urllib UA gets 403 on robots.txt itself — the "
                         "policy was always published, the default UA could "
                         "not read it.",
         pace_seconds=2.0, user_agent=UA_DESC, cache_path="decoder/bsa_cache/",
         parser_version="bsa/6", universe=10805, retrievable=10047,
         retrievable_note="~93% of URLs resolve, measured by decade probe. "
                          "404s cluster in RECENT cases — decided but not yet "
                          "posted. The URL is a FORMULA built from the calendar "
                          "number, so 100% of rows carry a URL and that says "
                          "nothing about the file existing.",
         owner_chat="BSA/LPC/DCP", verified_on="2026-08-06",
         traps="TWO DOCUMENT FORMATS. BSA changed layout in 2020: 2019-and-"
               "earlier is the bulletin form (ACTION OF THE BOARD, PREMISES "
               "AFFECTED, 'Borough of X', date in a certification line), 2020+ "
               "is the standalone form. Measured 67.9% bulletin / 24.0% modern. "
               "Bulletin documents also BUNDLE CASES ('104-08-BZY thru "
               "119-08-BZY') and list every lot of the series."),
    # ── LPC ────────────────────────────────────────────────────────────────
    dict(source="LPC", stream="permits_index", method="structured_api",
         host="data.cityofnewyork.us", dataset_or_path="dpm2-m9mq",
         url_template="https://data.cityofnewyork.us/resource/dpm2-m9mq.json",
         auth="none", robots_policy="n/a — open data API", robots_read_how="n/a",
         pace_seconds=0, user_agent=None, cache_path=None,
         parser_version="bulk.socrata", universe=349692, retrievable=348462,
         retrievable_note="1,230 permits carry no regulation_number and cannot "
                          "be addressed at all.",
         owner_chat="BSA/LPC/DCP", verified_on="2026-08-06",
         traps="No bbl column — keys on borough/block/lot with borough as a "
               "title-case NAME, a fourth convention among LPC's five datasets."),
    dict(source="LPC", stream="permit_documents", method="direct_url",
         host="s-media.nyc.gov",
         dataset_or_path="/agencies/lpc/Permits/PermitFiles/",
         url_template="https://s-media.nyc.gov/agencies/lpc/Permits/"
                      "PermitFiles/{regulation_number}.pdf",
         auth="user_agent",
         robots_policy="NONE PUBLISHED — /robots.txt returns 404",
         robots_read_how="GET /robots.txt -> HTTP 404. A 404 is not a refusal "
                         "and not a permission. These are permit documents the "
                         "LPC links from its own public decision search; read "
                         "slowly, one at a time, stop on any sign of refusal.",
         pace_seconds=1.5, user_agent=UA_DESC, cache_path="decoder/lpc_cache/",
         parser_version="lpc_cofa/4", universe=348462, retrievable=126900,
         retrievable_note="THE ARCHIVE STARTS IN 2016 — measured 0/4 per year "
                          "for 2012-2015, 4/4 per year 2017-2026. So ~219,805 "
                          "permits are `unavailable` (never published) and "
                          "~126,900 are `unread` (published, not yet fetched). "
                          "EVERY permit type is served, not only CofA: CNE, "
                          "PMW, XCNE, MISC, WSL, NOC all returned 200 on "
                          "sampling.",
         owner_chat="BSA/LPC/DCP", verified_on="2026-08-06",
         traps="A CofA states NO envelope numbers — no floor area, no FAR, no "
               "height. It regulates FORM, not quantity, so a decoder written "
               "on the BSA template reports it empty when it is not."),
    dict(source="LPC", stream="designations", method="structured_api",
         host="data.cityofnewyork.us", dataset_or_path="ncre-qhxs",
         url_template="https://data.cityofnewyork.us/resource/ncre-qhxs.json",
         auth="none", robots_policy="n/a", robots_read_how="n/a",
         pace_seconds=0, user_agent=None, cache_path=None,
         parser_version="n/a", universe=39363, retrievable=39363,
         retrievable_note="THE BINDING FACT IS FULLY STRUCTURED — per-BBL, with "
                          "designation date and type. No document needed except "
                          "for the 1,508 rows whose `boundaries` says 'See "
                          "designation report' or 'Partial lot'.",
         owner_chat="BSA/LPC/DCP", verified_on="2026-08-06",
         traps="Every row reads status=DESIGNATED. There are NO calendared rows "
               "here, despite the brief and lpc.py both describing this dataset "
               "as designated AND calendared."),
    # ── DCP ────────────────────────────────────────────────────────────────
    dict(source="DCP", stream="zap_projects_index", method="structured_api",
         host="data.cityofnewyork.us", dataset_or_path="hgx4-8ukb",
         url_template="https://data.cityofnewyork.us/resource/hgx4-8ukb.json",
         auth="none", robots_policy="n/a", robots_read_how="n/a",
         pace_seconds=0, user_agent=None, cache_path=None,
         parser_version="bulk.socrata", universe=32931, retrievable=32931,
         retrievable_note="Index only.",
         owner_chat="BSA/LPC/DCP", verified_on="2026-08-06",
         traps="NO BBL, NO BLOCK, NO LOT, NO ADDRESS on any of 32,931 rows — "
               "the finest geography is the community district. The `actions` "
               "column is populated on 4.5%; the ULURP number encodes the same "
               "thing on 84.9%."),
    dict(source="DCP", stream="zap_project_records", method="app_backend_api",
         host="zap-api-production.herokuapp.com",
         dataset_or_path="/projects/{project_id}",
         url_template="https://zap-api-production.herokuapp.com/projects/"
                      "{project_id}",
         auth="none",
         robots_policy="none on the API host (404); the app it serves publishes "
                       "Allow: / at zap.planning.nyc.gov",
         robots_read_how="Host found in the ZAP page's own <meta name="
                         "'labs-zap-search/config/environment'> tag. Every "
                         "field returned is already rendered on the public page.",
         pace_seconds=1.5, user_agent=UA_DESC, cache_path=None,
         parser_version="dcp finding-aid", universe=32931, retrievable=32931,
         retrievable_note="THIS IS WHERE THE PARCEL KEY LIVES. Returns `bbls`, "
                          "geometry, and dcp-bsanumber / dcp-lpcnumber — a "
                          "cross-source join no feed publishes. Legacy "
                          "P-prefixed projects (6,391 of the envelope subset) "
                          "carry no geography and no documents.",
         owner_chat="BSA/LPC/DCP", verified_on="2026-08-06",
         traps="The API repeats BBLs — 29.5% of projects carry a duplicate. "
               "Dedupe or every count is inflated."),
    dict(source="DCP", stream="zap_filed_documents", method="authenticated",
         host="nyco365.sharepoint.com",
         dataset_or_path="/sites/nycdcppfs/dcp_artifacts/",
         url_template="(catalogued from the project record; not fetchable)",
         auth="login_required",
         robots_policy="n/a — request never reaches a policy",
         robots_read_how="Three retrieval forms tried (folder+filename, "
                         "site+serverRelativeUrl, _layouts/15/download.aspx"
                         "?SourceUrl=). All returned HTTP 401.",
         pace_seconds=None, user_agent=UA_DESC, cache_path=None,
         parser_version=None, universe=None, retrievable=0,
         retrievable_note="INVENTORY IS PUBLIC, CONTENT IS NOT. Every filed "
                          "document's name, type, date and location is "
                          "catalogued from the project record; the files "
                          "themselves need authentication. Recorded as an OPEN "
                          "QUESTION to ask, not a limit to probe around.",
         owner_chat="BSA/LPC/DCP", verified_on="2026-08-06",
         traps="Names are self-describing and worth the catalogue on their own: "
               "'10. Zoning Comparison Table.pdf' is the district before/after."),
    dict(source="DCP", stream="council_resolutions", method="authenticated",
         host="webapi.legistar.com", dataset_or_path="/v1/nyc/matters",
         url_template="(no computable URL established from dcp-ccresolutionnumber)",
         auth="api_token_required",
         robots_policy="none published — legistar.council.nyc.gov/robots.txt 404s",
         robots_read_how="GET webapi.legistar.com/v1/nyc/matters -> HTTP 403 "
                         "'Token is required'. GET legistar.council.nyc.gov/"
                         "robots.txt -> 404. A token would have to be obtained; "
                         "that is a question to ask, not a limit to probe.",
         pace_seconds=None, user_agent=UA_DESC, cache_path=None,
         parser_version=None, universe=None, retrievable=0,
         retrievable_note="THE FINAL ENTITLEMENT INSTRUMENT FOR ULURP. An action "
                          "that reaches the City Council is approved there, often "
                          "WITH MODIFICATIONS, so the Council resolution — not the "
                          "CPC report — is what actually binds. The reference "
                          "number is published in the ZAP project record and "
                          "every one found is ledgered as unread. ⚠ Sparsely "
                          "populated: 1 of 16 actions on a sample of completed "
                          "ULURP projects, and the value is a bare integer.",
         owner_chat="BSA/LPC/DCP", verified_on="2026-08-06",
         traps="The number is a bare integer ('646') with no year, so it is not "
               "even self-identifying without the project's date."),
    dict(source="DCP", stream="zap_project_page", method="browser_render",
         host="zap.planning.nyc.gov", dataset_or_path="/projects/{project_id}",
         url_template="https://zap.planning.nyc.gov/projects/{project_id}",
         auth="none", robots_policy="User-agent: * / Allow: /",
         robots_read_how="GET /robots.txt, 200.",
         pace_seconds=2.0, user_agent=UA_DESC, cache_path=None,
         parser_version=None, universe=32931, retrievable=32931,
         retrievable_note="Used only to VERIFY the API against an independent "
                          "witness. A plain fetch returns an empty shell — the "
                          "page is a client-side app, so scraping the HTML "
                          "yields a skeleton that looks like a page with no "
                          "data.",
         owner_chat="BSA/LPC/DCP", verified_on="2026-08-06",
         traps="Do not read this host at scale when the API answers the same "
               "question for a fraction of the cost."),
]


# ⚠ EXPLICIT, NOT DERIVED. You cannot infer which stream produces document rows
# from `method` alone: DCP has three non-index streams and only ONE of them
# (zap_filed_documents) yields rows in decoder_documents — the other two are how
# the parcel key and the verification witness are obtained. Deriving it would be
# a rule that happens to work for BSA and LPC and is wrong for DCP.
#
# A source absent from this map gets NULL, which means "the stream was never
# established by the decoder that wrote the row" — not "none exists". DOS is
# absent because this chat does not own it and will not name another decoder's
# retrieval method.
DOCUMENT_STREAM = {
    "BSA": "decision_resolutions",
    "LPC": "permit_documents",
    "DCP": "zap_filed_documents",
    # council_resolutions ALSO produces document rows for DCP; those rows set
    # document_stream themselves at write time, which is why the map stays
    # one-per-source and the writer overrides it when it knows better.
}


def _env():
    v = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip()
    return v["ACRIS_SUPABASE_URL"], v["ACRIS_SUPABASE_SERVICE_KEY"]


def push():
    base, key = _env()
    body = json.dumps(REGISTRY).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/rest/v1/decoder_source_registry?on_conflict=source,stream",
        data=body,
        headers={"apikey": key, "Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "Prefer": "resolution=merge-duplicates,return=minimal"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as f:
            return True, f.status
    except urllib.error.HTTPError as e:
        return False, f"{e.code} {e.read().decode('utf-8','ignore')[:300]}"


def report():
    print(f"{'source':<6}{'stream':<24}{'method':<18}{'universe':>10}"
          f"{'retrievable':>13}  auth")
    for r in REGISTRY:
        u = f"{r['universe']:,}" if r["universe"] else "—"
        g = f"{r['retrievable']:,}" if r["retrievable"] is not None else "—"
        print(f"{r['source']:<6}{r['stream']:<24}{r['method']:<18}{u:>10}"
              f"{g:>13}  {r['auth']}")


if __name__ == "__main__":
    if "--ddl" in sys.argv:
        print(DDL)
        raise SystemExit(0)
    report()
    print()
    ok, detail = push()
    print(f"push -> {'OK' if ok else 'FAILED'}: {detail}")
    if not ok:
        print("\nIf the table is missing, run this in the Supabase SQL editor:")
        print(DDL)
