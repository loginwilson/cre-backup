"""Bulk pulling — settings MEASURED on 2026-08-05, not assumed.

Every number here came from a benchmark, and the benchmark is in the docstring
so a future change can be argued with rather than guessed at. The whole point:
requests are the scarce resource on every source, and most of this project's
pulls were using a fraction of what the services will happily give.

    SOCRATA $limit         was 1,000  ->  50,000 honoured   (50x fewer requests)
                           the entire 1,201-row DEVR universe arrives in ONE
                           request in 0.5s
    SOCRATA in() clause    was 200 ids -> 500 ids           (2.5x)
                           1,000 ids = 25,133-char URL = HTTP 414
    CONCURRENCY            1 worker 27.2s -> 4 workers 4.4s (6.2x)
                           8 workers only 3.7s — diminishing, so 4-6 is the
                           honest setting, and it is gentler than 8
    ARCGIS                 maxRecordCount 1,000, supportsPagination true
                           -> page with resultOffset, 1,000 at a time
    CROSS-SOURCE           Socrata + two ArcGIS orgs concurrently in 0.7s —
                           independent limits, so different SOURCES parallelise
                           for free

⚠ NONE OF THIS APPLIES TO ACRIS IMAGES. That endpoint is rate-limited by policy
(see fetch_budget.py) and is deliberately excluded — going faster there is how
this project got blocked. Fast on the open data, slow on the images.
"""
import json, re, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

TOKEN = "XBMcBRBwtwiD4elm0XS5iwLRZ"
SOCRATA_LIMIT = 50000      # measured honoured
IN_CLAUSE_MAX = 500        # measured; 1,000 -> HTTP 414
WORKERS = 5                # measured sweet spot (6.2x at 4, 7.4x at 8)
ARCGIS_PAGE = 1000         # declared maxRecordCount


def _get(url, timeout=180, attempts=4):
    """⚠ RETRY 5xx ONLY, AND NEVER 4xx.

    Measured 2026-08-10: pulling five datasets for 138,513 ids (278 chunks at 5
    workers) died on a single transient HTTP 500. The same chunk succeeded
    immediately at one worker, so it was load, not a bad query — and with no
    retry anywhere in this file, one blip discarded the whole run.

    The split matters. A 5xx is the server having a moment and is worth another
    go. A 4xx is THIS CLIENT being wrong — the 400 that made all five index
    datasets look broken an hour ago was a bad $order of my own making, and
    retrying it would have hidden the bug behind four identical failures instead
    of one.

    ⚠ AND THIS IS SOCRATA/ARCGIS ONLY. It must never be reached for ACRIS
    images. There, a refusal is an answer: stop, do not retry, do not rotate
    anything. Retrying is what turned one refusal into three on 2026-08-05 and
    cost the image endpoint for an hour. This file never touches that host.
    """
    for i in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as f:
                return json.load(f)
        except urllib.error.HTTPError as e:
            if e.code < 500 or i == attempts - 1:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if i == attempts - 1:
                raise
        time.sleep(2 ** i)


def socrata(dataset, where=None, select=None, limit=None, paginate=True, **extra):
    """A Socrata pull that CANNOT silently truncate.

    ⚠ The first version defaulted to $limit=50,000 and returned exactly 50,000
    rows for a dataset holding 62,306. A result whose length equals the limit is
    indistinguishable from a complete one — the same failure shape as the silent
    skip, the empty scan, and the no-op filter. So:

      * with `paginate` (the default) the pull KEEPS GOING with $offset until a
        page comes back short. No caller can under-read by forgetting a limit.
      * with an explicit `limit`, the cap is honoured but a full page raises a
        warning through `truncated`, so a deliberate sample is never mistaken
        for a census.
    """
    def page(off, lim):
        p = {"$limit": lim, "$offset": off, "$$app_token": TOKEN}
        if where:
            p["$where"] = where
        if select:
            p["$select"] = select
        p.update({f"${k}": v for k, v in extra.items()})
        # ⚠ $offset PAGING WITHOUT $order IS NOT STABLE. Measured 2026-08-06 on
        # ic3t-wcy2 job_type='NB': the pull returned 199,888 rows every time —
        # the correct total — but only 199,679 DISTINCT ids, having silently
        # duplicated 209 rows and dropped 209 others. Two runs an hour apart
        # differed from each other. With $order on a unique column the same
        # pull returns 199,888 rows and 199,888 distinct ids.
        #
        # The count is right in both cases, which is the whole problem: the one
        # check anybody performs on a bulk pull is the one this failure passes.
        # `:id` is Socrata's own row identifier — unique, indexed, and present
        # on every dataset this project reads (verified on ic3t-wcy2, w9ak-ipjd,
        # ipu4-2q9a, bs8b-p36w, pkdm-hqz6, bnx9-e6tj, yvxd-uipr).
        #
        # ⚠ AND AGGREGATES NEED IT JUST AS MUCH — THIS GUARD USED TO SKIP THEM.
        #
        # The original read "not applied to aggregates: `$order=:id` is invalid
        # alongside $group", which is TRUE and led to the wrong conclusion:
        # applying no order at all. A paginated $group query is exactly as
        # unstable as the row query this guard was written to fix.
        #
        # Measured 2026-08-09 on 8h5j-fqxa grouped by borough,block,lot — the
        # SAME query, minutes apart:
        #     run 1   1,249,947 distinct tuples
        #     run 2     949,018 distinct tuples
        # A 300,000-row disagreement, and each run looked perfectly clean on
        # its own. The parcel bank's foundation number was taken from run 1.
        #
        # The fix is not `:id` but the GROUP COLUMNS, which are unique per
        # output row by definition and are valid in $order alongside $group.
        #
        # ⚠ A GUARD THAT COVERS ONE CASE AND EXEMPTS ITS SIBLING IS THE MOST
        # DANGEROUS KIND — the exemption is documented, so it reads as handled.
        # ⚠ AND THERE IS A THIRD CASE BETWEEN THE TWO ABOVE: THE BARE AGGREGATE.
        # `select="count(1) as n"` with no $group returns exactly ONE row, so
        # there is nothing to page and nothing to order — but `$order=:id` is
        # invalid alongside an aggregate and Socrata answers 400. Measured
        # 2026-08-10: all five ACRIS index datasets failed identically on a
        # plain row count, which is the tell that the fault is in this client
        # and not in five datasets.
        #
        # Note the shape of the mistake. The comment above congratulates itself
        # for covering rows AND groups — and the case it missed is the one that
        # is neither. Enumerating the branches you thought of does not prove the
        # enumeration is complete.
        agg = bool(select) and re.match(
            r"\s*(count|sum|avg|min|max)\s*\(", select, re.I) is not None
        if paginate and "order" not in extra and not (agg and "group" not in extra):
            if "group" in extra:
                p.setdefault("$order", extra["group"])
            else:
                p.setdefault("$order", ":id")
        return _get(f"https://data.cityofnewyork.us/resource/{dataset}.json?"
                    + urllib.parse.urlencode(p))

    if limit is not None and not paginate:
        rows = page(0, limit)
        socrata.truncated = (len(rows) == limit)
        return rows
    step = limit or SOCRATA_LIMIT

    # ⚠ SERIAL PAGING WAS THE ENTIRE COST OF THE BIG PULLS, AND THE FIX WAS
    # ALREADY IN THIS FILE. `arcgis_all` below gets the count first, computes
    # the offsets, and fetches them CONCURRENTLY. This function discovered its
    # offsets one page at a time instead — so a 17M-row pull at 50,000/page is
    # 341 sequential round trips, and the ACRIS per-type walk that ought to take
    # about a minute takes eight to forty-five.
    #
    # Nothing about Socrata required that. Once the count is known the offsets
    # are arithmetic, and `$order` (set in page() above) is what makes them
    # stable — the same guard that already had to exist for correctness.
    #
    # ⚠ THE COUNT DOES NOT MAKE THE PULL SAFE ON ITS OWN. The dataset can grow
    # between the count and the last page, so the computed offsets can end
    # short. The tail is therefore still walked serially until a page comes back
    # short — the one thing that actually proves the end was reached.
    _agg = bool(select) and re.match(
        r"\s*(count|sum|avg|min|max)\s*\(", select, re.I) is not None
    out, off = [], 0
    if paginate and limit is None and not _agg and "group" not in extra:
        # ⚠ FETCH PAGE ONE BEFORE ASKING HOW MANY THERE ARE. Counting first
        # looks tidier and taxes every SMALL pull with a round trip it never
        # needed — and most pulls in this project are small: socrata_in() chunks
        # ids 500 at a time, so a 174,086-document index pull is 349 chunks per
        # dataset that each fit in ONE page. Counting them all first added 1,745
        # requests to buy parallelism that could not apply.
        #
        # A short first page IS the answer. Only when it comes back full is
        # there anything to parallelise, and only then is the count worth its
        # round trip.
        first = page(0, step)
        if len(first) < step:
            socrata.truncated = False
            return first
        out = list(first)
        cnt = None
        try:
            r = socrata(dataset, where=where, select="count(1) as n",
                        paginate=False, limit=1)
            cnt = int(r[0]["n"]) if r else None
        except Exception:
            cnt = None                      # fall through to the serial walk
        if cnt and cnt > step:
            offsets = list(range(step, cnt, step))
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                for rows in ex.map(lambda o: page(o, step), offsets):
                    out.extend(rows)
            # ⚠ THE COUNT DOES NOT PROVE THE END. The dataset can grow between
            # the count and the last page, so keep walking until a page comes
            # back short — the only thing that actually establishes completion.
            off = step + len(offsets) * step
            while True:
                rows = page(off, step)
                out.extend(rows)
                if len(rows) < step:
                    break
                off += step
            socrata.truncated = False
            return out
        off = step                          # count unavailable: walk from page 2

    while True:
        rows = page(off, step)
        out.extend(rows)
        if len(rows) < step or (limit and len(out) >= limit):
            break
        off += step
    socrata.truncated = False
    return out[:limit] if limit else out


socrata.truncated = False


def socrata_in(dataset, column, values, select=None, quote=True, workers=WORKERS):
    """A big `column in (...)` pull, chunked to the measured URL ceiling and run
    concurrently. Chunking is not optional — 1,000 ids is a 414."""
    vals = [str(v) for v in values]
    chunks = [vals[i:i + IN_CLAUSE_MAX] for i in range(0, len(vals), IN_CLAUSE_MAX)]
    def one(part):
        joined = ",".join(f"'{v}'" if quote else v for v in part)
        return socrata(dataset, where=f"{column} in({joined})", select=select)
    out = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for rows in ex.map(one, chunks):
            out.extend(rows)
    return out


def arcgis_all(layer_url, where="1=1", out_fields="*", geometry=False,
               workers=WORKERS, cap=200000):
    """Page an ArcGIS layer past maxRecordCount using resultOffset.

    Pages are fetched concurrently AFTER the count is known, so the offsets are
    computed rather than discovered — no sequential walk.
    """
    cnt = _get(layer_url + "/query?" + urllib.parse.urlencode({
        "where": where, "returnCountOnly": "true", "f": "json"})).get("count", 0)
    cnt = min(cnt, cap)
    offsets = list(range(0, cnt, ARCGIS_PAGE))
    def page(off):
        return _get(layer_url + "/query?" + urllib.parse.urlencode({
            "where": where, "outFields": out_fields,
            "returnGeometry": "true" if geometry else "false",
            "resultOffset": off, "resultRecordCount": ARCGIS_PAGE,
            "outSR": 2263 if geometry else "", "f": "geojson" if geometry else "json"}))
    rows = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for d in ex.map(page, offsets):
            rows.extend(d.get("features") or [])
    return rows, cnt


def parallel(tasks, workers=WORKERS):
    """Run independent pulls across DIFFERENT sources at once. Their limits are
    independent, so this is free throughput — the single best lever available
    while ACRIS images are rate-limited."""
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(lambda f: f(), tasks))


if __name__ == "__main__":
    import time
    t0 = time.time()
    devr = socrata("bnx9-e6tj", where="doc_type='DEVR'",
                   select="document_id,document_amt,recorded_datetime")
    print(f"whole DEVR universe: {len(devr):,} rows in ONE request, {time.time()-t0:.1f}s")
    t0 = time.time()
    legals = socrata_in("8h5j-fqxa", "document_id", [d["document_id"] for d in devr])
    print(f"all their legals:    {len(legals):,} rows in "
          f"{-(-len(devr)//IN_CLAUSE_MAX)} chunked requests, {time.time()-t0:.1f}s")
    print(f"   (the old way: {-(-len(devr)//200)} requests at 200 ids, run one at a time)")
