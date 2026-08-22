"""LOAD THE SPINE, THE LEDGER AND THE GEOMETRY INTO SUPABASE.

    python to_supabase.py --check                  # what exists, what is loaded
    python to_supabase.py --parcels                # 1,175,952
    python to_supabase.py --geometry mappluto      # 856,614 polygons
    python to_supabase.py --geometry dtm           # 858,094 polygons
    python to_supabase.py --keys --condo --sink    # the smaller tables

Target: the DECODER project (`C:/dev/acris-decoder.env`), Login's call — all
five decoder chats write there, so the spine belongs where they can all reach it.

⚠ RUN `migration_003_spine_ledger.sql` FIRST. PostgREST cannot execute DDL and
  this project exposes no `exec_sql` RPC, so the tables have to be created once
  from the Supabase SQL editor. This module refuses to load into a table that
  does not exist rather than reporting zero rows written as success.

⚠ EVERY LOAD RECONCILES. `--check` reads the row count back from the server and
  compares it to what is on disk. A loader that reports what it SENT rather than
  what LANDED is the same silent-shortfall failure this project has met nine
  times, and at 1.7M rows over ~1,700 requests a dropped batch is not a
  hypothetical.
"""
import json, math, os, pathlib, sys, time, urllib.error, urllib.parse, urllib.request
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ENV = "C:/dev/acris-decoder.env"
SPINE_DIR = pathlib.Path(os.environ.get(
    "DECODER_SPINE", pathlib.Path(__file__).with_name("spine")))
SINK_DIR = pathlib.Path(os.environ.get("DECODER_SINK",
                                       pathlib.Path(__file__).with_name("sink")))
KEYS = pathlib.Path("buildings/streeteasy-parcel-keys.json")


def env():
    v = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip()
    return v["ACRIS_SUPABASE_URL"], v["ACRIS_SUPABASE_SERVICE_KEY"]


URL, KEY = env()
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}",
     "Content-Type": "application/json"}


def post(table, rows, on_conflict, tries=4):
    """Upsert one batch. Raises on failure — a batch that 4xx'd is NOT zero rows
    written, it is an unknown state, and continuing past it silently truncates."""
    if not rows:
        return 0
    body = json.dumps(rows).encode()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                f"{URL}/rest/v1/{table}?on_conflict={on_conflict}", data=body,
                headers={**H, "Prefer": "resolution=merge-duplicates,return=minimal"},
                method="POST")
            with urllib.request.urlopen(req, timeout=600) as f:
                f.read()
            return len(rows)
        except urllib.error.HTTPError as e:
            msg = e.read()[:300].decode(errors="replace")
            if e.code in (404,) or "PGRST205" in msg:
                raise SystemExit(
                    f"\nTABLE `{table}` DOES NOT EXIST.\n"
                    f"Run migration_003_spine_ledger.sql in the Supabase SQL "
                    f"editor first — PostgREST cannot create it.\n  {msg}")
            last = f"HTTP {e.code}: {msg}"
            time.sleep(2 * (i + 1))
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{table} FAILED after {tries} tries: {last}")


def count(table):
    """Server-side row count. The only number that means anything."""
    req = urllib.request.Request(
        f"{URL}/rest/v1/{table}?select=*&limit=1",
        headers={**H, "Prefer": "count=exact", "Range": "0-0"})
    try:
        with urllib.request.urlopen(req, timeout=180) as f:
            cr = f.headers.get("Content-Range") or ""
        n = cr.rsplit("/", 1)[-1]
        return int(n) if n.isdigit() else None
    except urllib.error.HTTPError as e:
        return f"ABSENT ({e.code})"
    except Exception as e:
        return f"FAILED ({type(e).__name__})"


def stream(rows, table, on_conflict, batch=500, label=""):
    sent, t0 = 0, time.time()
    buf = []
    for r in rows:
        buf.append(r)
        if len(buf) >= batch:
            sent += post(table, buf, on_conflict)
            buf = []
            if sent % (batch * 40) == 0:
                rate = sent / max(time.time() - t0, 1)
                print(f"    {sent:,} sent · {rate:,.0f}/s")
    if buf:
        sent += post(table, buf, on_conflict)
    print(f"  {label or table}: {sent:,} rows sent in {time.time()-t0:,.0f}s")
    return sent


# ── Esri rings -> PostGIS EWKT ───────────────────────────────────────────────
def _area(ring):
    """Signed shoelace area. Counter-clockwise is positive."""
    a = 0.0
    for i in range(len(ring) - 1):
        a += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
    return a / 2.0


def _pip(x, y, ring):
    inside, n, j = False, len(ring), len(ring) - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def rings_to_ewkt(rings):
    """Esri packs a parcel's OUTER rings and its HOLES into one flat array, with
    outer rings clockwise and holes counter-clockwise.

    ⚠ TREATING EVERY RING AS A SEPARATE POLYGON IS THE BUG THIS GUARDS AGAINST.
    A courtyard would become solid ground, and `ST_Contains` would then place a
    pin in the middle of a block onto the building that surrounds it — the same
    class of silent mis-placement the whole keying exercise exists to remove.

    So: negative signed area = outer ring, positive = hole, and each hole is
    assigned to the outer ring that actually contains it (tested on a vertex,
    not a bounding box — nested lots make bbox containment wrong).
    """
    outers, holes = [], []
    for r in rings:
        if len(r) < 4:
            continue                        # degenerate; not a ring
        (holes if _area(r) > 0 else outers).append(r)
    if not outers:
        # every ring read as a hole: the winding is not what Esri documents.
        # Fall back to treating them as outers rather than dropping the parcel,
        # and it is visible because holes will be empty.
        outers, holes = holes, []
    if not outers:
        return None
    assigned = [[o] for o in outers]
    for h in holes:
        px, py = h[0][0], h[0][1]
        for i, o in enumerate(outers):
            if _pip(px, py, o):
                assigned[i].append(h)
                break
        # a hole inside no outer ring is dropped — it is not a hole in this parcel

    def ring_txt(r):
        pts = ",".join(f"{p[0]:.6f} {p[1]:.6f}" for p in r)
        if r[0][0] != r[-1][0] or r[0][1] != r[-1][1]:
            pts += f",{r[0][0]:.6f} {r[0][1]:.6f}"   # PostGIS requires closure
        return f"({pts})"

    polys = ",".join("(" + ",".join(ring_txt(r) for r in grp) + ")" for grp in assigned)
    return f"SRID=4326;MULTIPOLYGON({polys})"


# ── loaders ──────────────────────────────────────────────────────────────────
def load_parcels():
    p = SPINE_DIR / "spine.jsonl"
    n = sum(1 for _ in open(p, encoding="utf-8"))
    print(f"parcels: {n:,} on disk")

    def gen():
        with open(p, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                yield {
                    "bbl": r["bbl"], "boro": int(r["boro"]) if str(r.get("boro","")).isdigit() else None,
                    "block": r.get("block"), "lot": r.get("lot"),
                    "kind": r.get("kind"), "status": r.get("status") or "live",
                    "has_condo": bool(r.get("has_condo")), "has_reuc": bool(r.get("has_reuc")),
                    "has_air": bool(r.get("has_air")), "has_sub": bool(r.get("has_sub")),
                    "has_easement": bool(r.get("has_easement")),
                    "parent_bbl": r.get("parent"), "base_bbl": r.get("base_bbl"),
                    "billing_bbl": r.get("billing_bbl"), "condo_key": r.get("condo_key"),
                    "condo_name": r.get("condo_name"),
                    "child_count": len(r.get("children") or []),
                    "source": r.get("source"),
                    # lineage from the DOF Digital Alteration Book. Arrays, because
                    # a lot apportioned into five parcels has five successors.
                    "successors": r.get("successors"),
                    "predecessors": r.get("predecessors"),
                    "succession": r.get("succession"),
                }
    stream(gen(), "parcels", "bbl", batch=1000, label="parcels")
    return n


def load_geometry(layer, batch=200):
    """⚠ SMALL BATCHES ON PURPOSE. A polygon is orders of magnitude larger than a
    parcel row; 1,000 of them is a multi-megabyte request that times out.

    ⚠ A PARCEL CAN BE SEVERAL POLYGONS, AND THEY ARE ALL THE PARCEL.
    The DTM carries 70 multi-part parcels — one BBL, several disjoint outlines
    (a lot split by a street, an L around a corner). Emitting one row per polygon
    put the same (layer, bbl) twice in one batch and Postgres refused it:

        21000  ON CONFLICT DO UPDATE command cannot affect row a second time

    The tempting fix is to keep the first and drop the rest. That is wrong: half
    a parcel would then sit in the overlay looking whole, and ST_Contains would
    return nothing for a pin on the other half — a missing answer that looks
    exactly like "this pin is on a street bed". So the parts are MERGED into one
    MultiPolygon, which is what a multi-part parcel actually is.

    Pages are ordered by BBL, so parts arrive adjacent and a one-BBL buffer is
    enough. A BBL that reappears out of order is skipped AND COUNTED, never
    silently dropped.
    """
    d = SPINE_DIR / "geometry" / layer
    files = sorted(d.glob("p*.json"))
    if not files:
        raise SystemExit(f"no geometry for {layer} — run spine_geometry.py --pull {layer}")
    stat = Counter()

    def gen():
        cur_bbl, cur_rings, cur_attr, seen = None, [], {}, set()

        def flush():
            if cur_bbl is None:
                return None
            w = rings_to_ewkt(cur_rings)
            if not w:
                stat["unconvertible"] += 1
                return None
            stat["ok"] += 1
            if len(cur_rings) and cur_attr.get("_parts", 1) > 1:
                stat["multipart_merged"] += 1
            row = {"layer": layer, "bbl": cur_bbl, "geom": w}
            if layer == "mappluto":
                row |= {"units_res": cur_attr.get("ur"), "bldg_class": cur_attr.get("cls"),
                        "address": cur_attr.get("adr")}
            return row

        for fp in files:
            for r in json.loads(fp.read_text(encoding="utf-8")):
                if r["bbl"] == cur_bbl:
                    cur_rings.extend(r["rings"])          # another part of the SAME parcel
                    cur_attr["_parts"] = cur_attr.get("_parts", 1) + 1
                    continue
                out = flush()
                if out:
                    yield out
                if r["bbl"] in seen:
                    # non-adjacent repeat: reported rather than merged blindly,
                    # because merging across a gap would hide an ordering bug
                    stat["out_of_order_duplicate"] += 1
                    cur_bbl, cur_rings, cur_attr = None, [], {}
                    continue
                seen.add(r["bbl"])
                cur_bbl, cur_rings, cur_attr = r["bbl"], list(r["rings"]), dict(r)
        out = flush()
        if out:
            yield out

    sent = stream(gen(), "parcel_geometry", "layer,bbl", batch=batch,
                  label=f"parcel_geometry[{layer}]")
    print(f"    converted ok {stat['ok']:,} · unconvertible {stat['unconvertible']:,}"
          f" · multi-part merged {stat['multipart_merged']:,}"
          f" · out-of-order duplicates skipped {stat['out_of_order_duplicate']:,}")
    return sent


def load_keys():
    if not KEYS.exists():
        print("  no key table — run key_buildings.py first")
        return 0
    rows = json.loads(KEYS.read_text(encoding="utf-8"))
    print(f"building_parcel_keys: {len(rows):,} on disk")
    seen = set()
    def gen():
        for r in rows:
            s_ = r.get("slug")
            if not s_ or s_ in seen:
                continue
            seen.add(s_)
            yield {"source": "STREETEASY", "slug": s_, "bbl": r.get("bbl"),
                   "ground_bbl": r.get("ground_bbl"), "verdict": r["verdict"],
                   "reason": (r.get("reason") or "")[:500] or None,
                   "name": r.get("name"), "address": r.get("address"),
                   "source_units": r.get("source_units"),
                   "units_res": r.get("units_res"), "bldg_class": r.get("bldg_class"),
                   "area": r.get("area"),
                   "se_id": r.get("se_id") or r.get("seId")}
    return stream(gen(), "building_parcel_keys", "source,slug", batch=500)


def load_condo(since="2003-01-01"):
    """EVERY condo sale — archive (2003-2015) + annualized (2016-2025) +
    rolling (through today) — matched to a spine parcel and loaded.

    ⚠ `bbl` IS THE UNIT LOT THAT TRADED. `building_bbl` is the condominium
    BILLING lot, taken from the spine's DOF-condo_key lineage — NOT from the
    sales file's own `bbl` column, which gives the billing lot on some rows, the
    base lot on others and null on the rest. The billing lot matters because it
    is the only one of the two that HAS GEOMETRY: a condo unit lot is a tax
    fiction stacked in the air (measured: 0 of 60 sampled unit lots have a
    polygon, 59 of 60 billing lots do), so the billing lot is the only door from
    a unit sale onto the map.

    ⚠ unit_type / beds ARE NULL FOR EVERY DOF SALE. The sales files carry no
    bedroom count in any era. That is an absence in the source, not a gap in the
    load, and filling it from an average would turn a missing field into a
    fabricated one. Marketproof supplies it on the active side.
    """
    import condo_sales as CS
    print("pulling the archive (2003-2015)...")
    arch, adrop, araw, bad = CS.pull_archive()
    print(f"  archive: {araw:,} rows -> {len(arch):,} condo sales")

    print(f"pulling Socrata (2016 ->) ...")
    soc, sdrop, sraw = CS.pull_sales(since="2016-01-01")
    print(f"  socrata: {sraw:,} rows -> {len(soc):,} condo sales")

    # dedupe across all three sources on the sale's own identity
    sales, seen, dupe = [], set(), 0
    for s_ in arch + soc:
        k = (s_["bbl"], s_["date"], s_["price"])
        if k in seen:
            dupe += 1
            continue
        seen.add(k)
        sales.append(s_)
    print(f"  combined: {len(sales):,} unique sales ({dupe:,} duplicated across sources)")

    print("joining per-unit SF from the assessment roll...")
    st = CS.attach_roll_sf(sales)
    for k, v in sorted(st.items(), key=lambda x: -x[1]):
        print(f"     {v:>8,}  {k}")

    print("matching to the spine...")
    idx = CS.load_spine_index()
    buckets = CS.match_parcels(sales, idx)
    for k in sorted(buckets, key=lambda x: -len(buckets[x])):
        print(f"     {k:<22}{len(buckets[k]):>9,}")

    def src(s_):
        d = str(s_.get("dataset") or "")
        return ("DOF_ARCHIVE" if d.startswith("archive:") else
                "DOF_ANNUAL" if d == CS.ANNUAL else
                "DOF_ROLLING" if d == CS.ROLLING else "DOF")

    out, skipped = [], 0
    for s_ in sales:
        if not s_.get("date") or not s_.get("price"):
            skipped += 1
            continue
        out.append({
            "bbl": s_["bbl"], "building_bbl": s_.get("building_bbl"),
            "building_name": s_.get("condo_name"),
            "unit": s_.get("unit"), "unit_key": s_.get("unit_key"),
            "unit_type": None, "beds": None,      # absent in every DOF sales file
            "sf": s_.get("sf"), "sf_source": s_.get("sf_source"),
            "sf_confirmed": bool(s_.get("sf_apt_confirmed")),
            "amount": s_["price"], "psf": s_.get("usf"),
            "status": "historical",               # every DOF sale is closed
            "event_date": s_["date"], "address": s_.get("address"),
            "neighborhood": s_.get("neighborhood"),
            "bldg_class": s_.get("bldg_class"),
            "year_built": int(s_["year_built"]) if str(s_.get("year_built") or "").split(".")[0].isdigit() else None,
            "source": src(s_), "evidence": "index",
        })
    if skipped:
        print(f"  ⚠ {skipped:,} skipped for a missing date or price")

    # dedupe on the table's own key — PostgREST 500s if one request updates the
    # same row twice, and (bbl, event_date, amount) is coarser than the sale id
    final, seen2, collided = [], set(), 0
    for r in out:
        k = (r["bbl"], r["event_date"], r["amount"])
        if k in seen2:
            collided += 1
            continue
        seen2.add(k)
        final.append(r)
    if collided:
        print(f"  {collided:,} rows share (bbl, date, amount) — same unit, same day, "
              f"same price; counted once")
    return stream(iter(final), "condo_sales", "bbl,event_date,amount", batch=500,
                  label="condo_sales")


def load_sink():
    """The fact sink and the run heartbeats. `runs` keeps only the LATEST beat
    per run_id — the JSONL is append-only and every beat is a row there."""
    f = SINK_DIR / "facts.jsonl"
    r = SINK_DIR / "runs.jsonl"
    n = 0
    if f.exists():
        rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        n += stream(({"source": x.get("source"), "source_doc_id": x.get("document_id"),
                      "page": str(x.get("page")) if x.get("page") is not None else None,
                      "bbl": (x.get("bbls") or [None])[0],
                      "predicate": x.get("predicate"), "happened": x.get("happened"),
                      "recorded": x.get("recorded"), "value": x.get("value"),
                      "unit": x.get("unit"), "parties": x.get("parties"),
                      "confidence": x.get("confidence") or "read",
                      "evidence": x.get("evidence") or "document",
                      "derivation": x.get("derivation"), "verbatim": x.get("verbatim"),
                      "parser_version": x.get("parser"), "run_id": x.get("run_id")}
                     for x in rows), "facts", "fact_id", batch=500, label="facts")
    if r.exists():
        beats = [json.loads(l) for l in r.read_text(encoding="utf-8").splitlines() if l.strip()]
        latest = {}
        for b in beats:
            k = b["run_id"]
            if k not in latest or b["at"] >= latest[k]["at"]:
                latest[k] = b
        n += stream(({"run_id": b["run_id"], "source": b["source"], "done": b.get("done") or 0,
                      "total": b.get("total"), "status": b.get("status") or "running",
                      "note": b.get("note"),
                      "last_beat": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(b["at"]))}
                     for b in latest.values()), "runs", "run_id", batch=500, label="runs")
    return n


def check():
    print(f"SUPABASE {URL}\n")
    on_disk = {}
    p = SPINE_DIR / "spine.jsonl"
    if p.exists():
        on_disk["parcels"] = sum(1 for _ in open(p, encoding="utf-8"))
    for layer in ("mappluto", "dtm"):
        d = SPINE_DIR / "geometry" / layer
        if d.exists():
            # ⚠ COUNT DISTINCT PARCELS, NOT POLYGON ROWS. 48 DTM parcels are
            # multi-part — one BBL, several disjoint outlines — and they load as
            # ONE MultiPolygon each. Counting rows made the denominator 70 too
            # high and reported a complete load as "PARTIAL — 70 short": a
            # correct load accused by a wrong denominator, which is the same
            # class of error as a wrong load excused by one.
            bbls = set()
            for f in d.glob("p*.json"):
                for r in json.loads(f.read_text(encoding="utf-8")):
                    bbls.add(r["bbl"])
            on_disk[f"geom[{layer}]"] = len(bbls)
    if KEYS.exists():
        on_disk["building_parcel_keys"] = len(json.loads(KEYS.read_text(encoding="utf-8")))

    print(f"  {'table':<24}{'on server':>12}{'on disk':>12}   state")
    geom_total = count("parcel_geometry")
    for t in ("parcels", "source_documents", "facts", "runs",
              "building_parcel_keys", "condo_sales", "parcel_geometry"):
        srv = count(t)
        disk = on_disk.get(t, "—")
        if t == "parcel_geometry":
            disk = sum(v for k, v in on_disk.items() if k.startswith("geom["))
        state = ("MISSING — run the migration" if isinstance(srv, str) else
                 "empty" if srv == 0 else
                 "loaded" if isinstance(disk, int) and srv >= disk else
                 f"PARTIAL — {disk - srv:,} short" if isinstance(disk, int) else "loaded")
        print(f"  {t:<24}{str(srv):>12}{str(disk):>12}   {state}")


# ══ RESIDENTIAL LEASES — the StreetEasy harvest ═════════════════════════════
LEASES_RAW = pathlib.Path(__file__).with_name("leases_raw")


def load_leases(batch=500):
    """Every pulled listing, active and historical, keyed to a spine parcel.

    ⚠ GROUP BY BBL BEFORE WRITING. 1,286 parcels carry more than one building
    (3,249 buildings). Gotham Point is two towers on lot 4000067503 — 689 + 443
    = 1,132, exactly the lot's unitsres. Written per-building in separate passes
    they overwrite each other and the loss is invisible: the ledger looks whole
    and is missing a tower. Merged here, before a single row is sent.

    Across lots nothing merges, however much two lots share a name — Malt Drive
    is two listings on two lots and stays two records.

    ⚠ IDENTITY IS (bbl, source_id), NOT (bbl, unit, date, amount). Measured on
    the first 24 buildings: 1,106 of 35,156 records (3.1%) shared unit+date+
    amount while being different listings. Keyed the coarse way the load drops
    3% of every building's history and says nothing.

    ⚠ psf IS DELIBERATELY NULL. Operator: "I can run the costs in app so you
    dont have to calc just pull." A rate is a derivation, and deriving it here
    would bake one definition of $/RSF into the store.
    """
    files = sorted(LEASES_RAW.glob("leases_*.jsonl"))
    if not files:
        raise SystemExit(f"nothing in {LEASES_RAW} — run the pull first")

    # ⚠ WHEN THE SOURCE WAS READ, not when the row was written. The receiver
    # names each file with the epoch at which that pull began, so the pull time
    # is recoverable from the filename rather than guessed from the load.
    # On a daily cadence this is the field that answers "how stale is this?" —
    # `now()` at insert would say the data is fresh the moment it lands, however
    # old the pull behind it.
    import datetime
    pulled_at = {}
    for fp in files:
        try:
            ts = int(fp.stem.split("_")[1])
            pulled_at[fp] = datetime.datetime.fromtimestamp(
                ts, datetime.timezone.utc).isoformat()
        except Exception:
            pulled_at[fp] = None

    seen, rows, stat = set(), [], Counter()
    by_bbl_names = defaultdict(set)
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    stat["unparseable"] += 1
                    continue
                if r.get("test"):
                    continue
                bbl, sid = r.get("bbl"), r.get("source_id")
                if not bbl or not sid:
                    stat["missing_bbl_or_source_id"] += 1
                    continue
                k = (bbl, str(sid))
                if k in seen:
                    stat["duplicate_listing"] += 1
                    continue
                seen.add(k)
                by_bbl_names[bbl].add(r.get("building_name") or "")
                r["_pulled_at"] = pulled_at.get(fp)
                rows.append(r)
    print(f"{len(files)} file(s) · {len(rows):,} unique listings")
    for k, v in stat.items():
        print(f"    {v:,} {k}")

    # one lot, several buildings -> the lot takes the SHARED NAME PREFIX
    # ("Gotham Point", not "Gotham Point South"), so the record names the place
    # rather than whichever tower happened to be written last.
    def shared(names):
        names = [n for n in names if n]
        if not names:
            return None
        if len(names) == 1:
            return names[0]
        p = names[0]
        for n in names[1:]:
            while p and not n.startswith(p):
                p = p[:-1]
        p = p.strip(" -–—,")
        return p if len(p) >= 4 else sorted(names)[0]

    lot_name = {b: shared(ns) for b, ns in by_bbl_names.items()}
    multi = sum(1 for b, ns in by_bbl_names.items() if len({n for n in ns if n}) > 1)
    print(f"  {len(by_bbl_names):,} parcels · {multi:,} carry buildings with different "
          f"names (merged under a shared prefix)")

    def gen():
        for r in rows:
            yield {
                "bbl": r["bbl"], "building_name": lot_name.get(r["bbl"]) or r.get("building_name"),
                "unit": r.get("unit"), "unit_key": r.get("unit_key"),
                "unit_type": r.get("unit_type"), "beds": r.get("beds"),
                "sf": r.get("sf"), "amount": r.get("amount"),
                "psf": None,                       # derived downstream, on purpose
                # TWO CATEGORIES ONLY — the two panels on the building page.
                # The pull records StreetEasy's own finer codes in the raw file,
                # but they are not categories here and nothing keys on them.
                "status": ("active" if (r.get("lane") or r.get("status")) == "active"
                           else "historical"),
                "event_date": r.get("event_date"),
                "source": "STREETEASY", "source_id": str(r.get("source_id")),
                "evidence": "listing",
                "se_status": r.get("se_status"),
                "available_at": r.get("available_at"),
                "source_pulled_at": r.get("_pulled_at"),
            }
    import datetime
    run_id = f"streeteasy-{int(time.time())}"
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    post("runs", [{"run_id": run_id, "source": "STREETEASY",
                   "started_at": started, "done": 0, "total": len(rows),
                   "status": "running", "note": f"{len(files)} raw file(s)"}],
         "run_id")
    try:
        n = stream(gen(), "residential_leases", "bbl,source_id", batch=batch,
                   label="residential_leases")
    except Exception as e:
        post("runs", [{"run_id": run_id, "source": "STREETEASY", "done": 0,
                       "total": len(rows), "status": "FAILED",
                       "note": str(e)[:300]}], "run_id")
        raise
    post("runs", [{"run_id": run_id, "source": "STREETEASY",
                   "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "done": n, "total": len(rows), "status": "complete",
                   "note": f"{len(by_bbl_names):,} parcels"}], "run_id")
    return n


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--check" in a or not a:
        check()
    if "--parcels" in a:
        load_parcels()
    if "--geometry" in a:
        load_geometry(a[a.index("--geometry") + 1])
    if "--keys" in a:
        load_keys()
    if "--condo" in a:
        load_condo()
    if "--sink" in a:
        load_sink()
    if "--leases" in a:
        load_leases()
    if a and "--check" not in a:
        print()
        check()
