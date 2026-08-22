"""The DOS public-inquiry portal — the reach layer the Socrata register cannot give.

WHY THIS EXISTS, measured 2026-08-06

    `n9v6-gdp6` is the ACTIVE entity register. An SPE that wound up after its
    deal closed is simply not in it, so 790 of 2,486 corporate names on the
    rights instruments resolved to nothing — and "nothing" is where a broker's
    outreach stops.

    The portal at apps.dos.ny.gov publishes those entities anyway, INACTIVE ones
    included, with their service-of-process name and address. Proven on
    SUTTON 58 OWNER, LLC (dos_id 4592052, inactive since 2015-03-17), which the
    Socrata pipeline could only mark "dissolved": the portal names
    HOWARD W. MUCHNICK, MUCHNICK, GOLIEB & GOLIEB, P.C., 200 Park Avenue South,
    Suite 1700 — an attorney, reachable, today.

⚠ WHAT THE PORTAL DOES **NOT** HAVE

    Document images. The Filing History tab lists File Date, Cert Code,
    Document Type, PAGE COUNT and File Number, and offers no link, no viewer and
    no download — the table is plain text. NY DOS does not publish filing images
    at all, so the ARTICLES OF ORGANIZATION that names the organiser, and the
    CERTIFICATE OF MERGER that names the survivor, are obtainable only by paid
    copy, FOIL, or inspection in Albany. Merger History renders EMPTY even for
    an entity with a merger on file — who absorbed it is on the paper only.

    Page count is still worth taking: it is `pages_total` in LEDGER_SCHEMA, so
    the ledger can carry an honest `pages_read / pages_total` — 0 / 11 rather
    than a bare zero.

⚠ THE HOST DEFENDS ITSELF, AND THAT IS A LIMIT TO RESPECT, NOT TO BEAT

    apps.dos.ny.gov sits behind BIG-IP with F5 Shape (`/TSPD/?type=22`, and a
    `TSPD_74` token in localStorage). curl, urllib and a headless browser all get
    the TLS connection RESET; only a real browser is served. An early UI walk
    started erroring after roughly ten quick page loads.

    So this module drives the site's own JSON endpoint from a real logged-in
    browser tab, ONE request per entity — fewer than the three page loads the UI
    itself makes — spaced 3.5s, and it HALTS on the first non-200, non-JSON or
    unsuccessful response instead of retrying around it. If the host says stop,
    the answer is to stop and use FOIL, not to look more like a browser.

WHERE THE OUTPUT GOES — `sink.party`, not `sink.emit`

    A service-of-process address has no document and no page, so it cannot be a
    `facts.Fact` without inventing one. It is current state, not an assertion
    read off a page. See sink.party for why that needed a third row type.
★ THE ENDPOINT MAP — measured 2026-08-06, five surfaces, only one of them used

    POST /PublicInquiryWeb/api/PublicInquiry/...

      GetEntityRecordByID          {SearchID, AssumedNameFlag}
          entityGeneralInfo + sopAddress. HARVESTED for 262 entities.

      GetComplexSearchMatchingEntities
          {searchValue, searchByTypeIndicator:"EntityName",
           searchExpressionIndicator:"BeginsWith"|"Contains"|"BaseWord",
           entityStatusIndicator:"AllStatuses",
           entityTypeIndicator:[Corporation, LimitedLiabilityCompany,
                                LimitedPartnership, LimitedLiabilityPartnership],
           listSortedBy, listPaginationInfo:{listStartRecord, listEndRecord}}
          ★★ THE HIGHEST-VALUE SURFACE HERE. It searches ALL STATUSES and ALL
          ENTITY TYPES, so it reaches the INACTIVE and FOREIGN entities that
          n9v6-gdp6 omits by construction. Proven: "1039 MADISON OWNER LLC",
          unresolvable in every Socrata dataset, resolves here as a Delaware
          FOREIGN LLC, inactive. This is the route to the 528 corporate names
          (21% of the denominator) that currently resolve to nothing.

      GetNameHistoryByID           {SearchID, AssumedNameFlag, EntityName, ...}
          nameHistoryResultList: the entity name AS IT STOOD ON EACH FILING,
          with fileDate, documentType, fileNumber.
          ⚠ HYPOTHESIS, NOT YET A FINDING. ACRIS records the name at the time of
          the DEAL; the register carries only the CURRENT name. An entity that
          renamed after closing is therefore unmatchable by current name, and
          this endpoint is the only published bridge. Tested on ONE entity
          (2286637), which had exactly one name — so the mechanism is confirmed
          to work and its YIELD is entirely unmeasured. The test: run it over
          the 1,695 already-matched entities, count how many report >1 name, and
          check whether any prior name is one of the 528 unresolved ACRIS names.

      GetFilingHistoryByID
          fileDate, certCode, documentType, PAGECOUNT, fileNumber, filingDocGUID.
          pageCount is `pages_total` in LEDGER_SCHEMA — it makes the ledger read
          "0 of 11 read" instead of a bare zero, WITHOUT opening anything.

      GetMergerHistoryByID
          Returns resultIndicator "NoHistoryAvailable" even for entities holding
          a CERTIFICATE OF MERGER (checked on 4592052 and 2286637). Merger
          lineage is NOT published. Recorded here so nobody spends the request
          again — who absorbed whom is on the paper only.

⚠ AND THE DOCUMENT ROUTE, WHICH EXISTS AND DOES NOT ANSWER

    The app's own bundle defines
        GET https://apps.dos.ny.gov/GenericApi/api/Generic/GetDocumentData
        ?documentId=<...>            (the API states the parameter name itself,
                                      by rejecting the call with a 400)
    backed by IBM FileNet. Passed the `filingDocGUID` that the public filing
    history hands out, in both braced and unbraced form, it returns 200 with
    isSuccess=false and a server-side NullReferenceException out of
    FileNetClient.QuerySingle — i.e. the public filing GUIDs are not keys into
    whatever that store serves.

    Probing further would mean guessing at an internal API that is throwing
    unhandled exceptions, so it was stopped there. The conclusion stands and is
    now evidenced three ways: DOS publishes no filing images.

⚠ THE PACE CEILING, MEASURED THE HARD WAY

    262 GetEntityRecordByID calls at 3.5s completed clean, zero refusals. The
    very next surface — GetComplexSearchMatchingEntities — HUNG on its second
    call: no error, no status, just no response, and the renderer went
    unresponsive after. The host does not refuse loudly; it stalls. So treat
    this as a hand-paced, small-batch surface and never as a pipeline, and read
    a hang as a refusal rather than something to retry through.
"""
import json, pathlib, re, sys, collections

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sink

ENDPOINT = "/PublicInquiryWeb/api/PublicInquiry/GetEntityRecordByID"

# A commercial registered agent is a WALL, not a lead: it is the same mailroom
# for thousands of unrelated entities. Clustering on its address would "discover"
# that 142 SPEs share an owner in Albany, which is CSC's post room. Flagged so
# nothing downstream can mistake one for a principal.
AGENT = re.compile(r"CORPORATION SERVICE|C T CORPORATION|CT CORPORATION|COGENCY|"
                   r"NATIONAL REGISTERED|INCORP SERVICES|LEGALINC|REGISTERED AGENT|"
                   r"UNITED STATES CORPORATION AGENTS|VCORP|BUSINESS FILINGS|"
                   r"CAPITOL SERVICES|PARACORP|NORTHWEST REGISTERED", re.I)

# The entity naming itself as its own agent tells you nothing new — "THE LLC",
# "THE CORPORATION" or the entity's own name is the default the form prints.
SELF = re.compile(r"^\s*(THE\s+(LLC|CORPORATION|COMPANY|PARTNERSHIP)|N/?A)\s*$", re.I)


def reach_kind(sop_name, entity_name):
    if not sop_name:
        return "none"
    if AGENT.search(sop_name):
        return "commercial agent (wall)"
    if SELF.match(sop_name):
        return "self (no new party named)"
    if entity_name and sop_name.strip().upper() == entity_name.strip().upper():
        return "self (no new party named)"
    return "NAMED third party"


def ingest(harvest, targets, run_id):
    """harvest: {dos_id: record} from the browser walk. targets: the DOS-ID list
    with its ACRIS name and parcels."""
    by_id = {t["dos_id"]: t for t in targets}
    counts = collections.Counter()
    for dos_id, r in harvest.items():
        t = by_id.get(dos_id, {})
        kind = reach_kind(r.get("sop_name"), r.get("name"))
        counts[kind] += 1
        sink.party("DOS", r.get("name"), bbls=t.get("bbls") or [], entity_id=dos_id,
                   contact_name=r.get("sop_name") or None,
                   address=r.get("sop_addr") or None, status=r.get("status"),
                   run_id=run_id, reach=kind, acris_name=t.get("acris"),
                   entity_type=r.get("type"), formed=r.get("filed") or None,
                   inactive_date=r.get("inactive") or None,
                   county=r.get("county"), jurisdiction=r.get("juris"),
                   reason_for_status=r.get("reason") or None,
                   note="NY DOS public-inquiry register; current state, not a "
                        "document. DOS publishes no filing images.")
    return counts


if __name__ == "__main__":
    S = pathlib.Path(sys.argv[1])
    harvest = json.loads((S / "dos_portal_harvest.json").read_text(encoding="utf-8"))
    targets = json.loads((S / "dos_portal_targets.json").read_text(encoding="utf-8"))["withid"]
    run_id = f"dos-portal-{len(harvest)}"
    total = len(targets)
    sink.heartbeat("DOS_PORTAL", run_id, done=0, total=total, note="ingesting")
    counts = ingest(harvest, targets, run_id)
    got = sum(counts.values())
    sink.heartbeat("DOS_PORTAL", run_id, done=got, total=total,
                   status="complete" if got >= total else "running",
                   note=f"{got}/{total} entities; " +
                        "; ".join(f"{k}={v}" for k, v in counts.most_common()))
    print(f"entities ingested {got:,} / {total:,} targeted")
    for k, v in counts.most_common():
        print(f"   {v:>5}  {k}")
    if got < total:
        print(f"   ⚠ {total-got:,} NOT retrieved — the walk halted or was capped. "
              f"They are absent, not empty.")
