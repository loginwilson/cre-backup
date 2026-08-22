"""THE KEYING WALK - every parcel-less doc id fires rd + pdf together and
comes back keyed (login design + mandate 2026-08-20: "every single unique
doc id [gets] a bbl match... you fire both the rd and pdf for both").

Per document, ONE worker does the whole unit of work:
  1. rd_endpoint  -> recorded_details captured faithfully (jsonl), the
                     page's id-echo asserted BEFORE anything is read
  2. map          -> if pages > 0: fetch pages -> G4 pdf into the store
  3. classify     -> parcel (BBL on page) / reference / neither
Store landing: BBL recovered -> By Parcel (dated filename); else party ->
By Party/<sanitized>; else By Document. The key upgrade later MOVES the file
(one copy always).

Measured on the 400-doc pilot (same day): 2.01 docs/s · 13.3 pg/s at 8
workers, 0 failures; newest digital slice keyed 97% (mostly sync-lag docs).
Refusal anywhere -> the whole walk stops (shared event). Resume-safe: the
jsonl is the ledger; already-pulled ids are skipped on restart.

Usage:  python keying_walk.py [--era digital|film] [--workers 8] [--limit N]
"""
import argparse
import html as _h
import sys, re, io, time, json, sqlite3, pathlib, threading, hashlib
import urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP
import live_delta as LD
import fetch_pages
import img2pdf
import rd_parse as RD

_ap = argparse.ArgumentParser()
_ap.add_argument("--era", choices=["digital", "film"], default="digital")
_ap.add_argument("--workers", type=int, default=8)
_ap.add_argument("--limit", type=int, default=0,
                 help="0 = the whole era's parcel-less list")
_a = _ap.parse_args()
WORKERS = _a.workers
# ⚠ digital = EVERY id that starts with a digit-2 year, 2003 onward. The
# pilot's '20[12]*' silently excluded 2003-2009 (third char 0) - caught when
# the walk list came up 167k short of the census. Letters (FT_/BK_/RC_)
# never match '2*', so the simple glob is the correct one.
GLOB = "2*" if _a.era == "digital" else "FT_*"
N = _a.limit or 2_000_000
OUT = CP.NAV_WORK / "rd_repull.jsonl"
STORE = pathlib.Path(r"D:\CRE Decoding System\02 Acquisitions"
                     r"\Legal Instruments Acquisition")
BORO = {"MANHATTAN": 1, "BRONX": 2, "BROOKLYN": 3, "QUEENS": 4,
        "STATEN ISLAND": 5}
VIEW = "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView"

stop = threading.Event()
lock = threading.Lock()
stats = {"match": 0, "ref": 0, "neither": 0, "fail": 0, "pages": 0,
         "imageless": 0, "pdfs": 0}

con = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True,
                      check_same_thread=False)
NOPCL = ("NOT EXISTS (SELECT 1 FROM parcel_document p"
         " WHERE p.document_id = d.document_id)")

done = set()
if OUT.exists():
    with OUT.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                done.add(json.loads(line)["id"])
            except Exception:
                pass
todo = []
with lock:
    for did, dt, rec_date in con.execute(
            f"SELECT d.document_id, d.doc_type, d.recorded_date FROM document d"
            f" WHERE d.document_id GLOB '{GLOB}' AND {NOPCL}"
            f" ORDER BY d.document_id DESC"):
        if did not in done:
            todo.append((did, dt or "", rec_date or ""))
        if len(todo) >= N:
            break
print(f"keying walk [{_a.era}]: {len(todo)} docs · {WORKERS} workers "
      f"({len(done)} already pulled)", flush=True)

# ⚠ SECTIONS ARE BOUNDED BY THE NEXT SECTION, NEVER BY A CHARACTER SPAN.
# Measured 2026-08-20 (pull demo, login watching): a 30,000-char span let
# PARTY 1 swallow PARTY 2, PARTY 3 AND the PARCELS table - ghost rows named
# "PARTY 2" / "BOROUGH" / nbsp-blanks landed in ~8.9k ledger rows as if
# they were parties. Entities are unescaped BEFORE parsing for the same
# reason: "&nbsp;" is data-shaped noise that survives every truthiness
# check. (scrub_ledger.py repaired the already-walked rows offline.)
_SECTION_ENDS = {"PARTY 1": "PARTY 2", "PARTY 2": "PARTY 3",
                 "PARTY 3": "PARCELS", "PARCELS": "REFERENCES",
                 "REFERENCES": "REMARKS", "REMARKS": None}
_GHOST = {"", "NAME", "PARTY 2", "PARTY 3/OTHER", "PARCELS", "BOROUGH"}


def cells_of(html, section, span=None):
    up = html.upper()
    i = up.find(section)
    if i < 0:
        return []
    end = _SECTION_ENDS.get(section)
    j = up.find(end, i + len(section)) if end else -1
    chunk = html[i:j] if j >= 0 else html[i:i + (span or 30000)]
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", chunk, re.S | re.I)[:25]:
        cs = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip()
              for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
        if any(cs):
            rows.append(cs)
    return rows

def flatfield(flat, label):
    g = re.search(label + r":\s*([^:]{1,50}?)\s+[A-Z#%][A-Za-z.#% -]{2,}:", flat)
    v = g.group(1).replace("\u00a0", " ").strip() if g else ""
    return "" if v.upper() == "N/A" else v

def sanitize(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")[:60] or "UNNAMED"

ua = {"User-Agent": fetch_pages.UA}

def get(url, referer, timeout=90):
    req = urllib.request.Request(url, headers={**ua, "Referer": referer})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")

def one(doc):
    did, dt, rec_date = doc
    if stop.is_set():
        return
    try:
        # 1 · rd
        body, ct = get(LD.BASE + "/DS/DocumentSearch/DocumentDetail?doc_id=" + did,
                       LD.BASE + "/DS/DocumentSearch/")
        html = _h.unescape(body.decode("utf-8", "replace")).replace("\xa0", " ")
        LD.check_refused(html)
        flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
        # ⚠ THE ID-ECHO ASSERTION (added after the pilot): read NOTHING until
        # the page proves it is about the doc we asked for. Richmond served a
        # different document off a duplicate instrument number TODAY - a
        # captured BBL from someone else's page is the one unrecoverable
        # error, so mismatch = fail, never a capture.
        if not re.search(r"DOCUMENT ID:\s*" + re.escape(did), flat):
            raise ValueError(f"page does not echo {did}")
        # THE COPY-PASTE RULE lives in rd_parse.parse_acris - THE one place
        # the page format is known (login: "figure it out once and you are
        # good for all 24,039,303"; a second regex for the same page is how
        # the demo truncated MCON to "M" while this walker read it right).
        rec = {"id": did, "type": dt,
               "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        rec.update(RD.parse_acris(html))
        pcls = [p["bbl"] for p in rec.get("parcels", [])]
        parties = rec.get("parties", [])

        # 2 · pdf (map first; 0/-1 pages = imageless, no fetch)
        body, ct = get(VIEW + "?doc_id=" + did,
                       LD.BASE + "/DS/DocumentSearch/DocumentDetail?doc_id=" + did)
        mhtml = body.decode("utf-8", "ignore")
        mm = re.search(r"TotalPages%22%3A(-?\d+)", mhtml)
        total = int(mm.group(1)) if mm else 0
        frames = []
        if total > 0:
            for p in range(1, total + 1):
                if stop.is_set():
                    return
                data, ct = get(f"{fetch_pages.BASE}?doc_id={did}&page={p}",
                               VIEW + "?doc_id=" + did, timeout=90)
                fetch_pages._check_denied(data, ct)
                if data[:2] not in (b"II", b"MM") or \
                   hashlib.md5(data).hexdigest() == fetch_pages.PLACEHOLDER:
                    break
                frames.append(data)
                with lock:
                    stats["pages"] += 1
        # 3 · land + classify
        datep = (rec_date or "0000-00-00")[:10]
        refs = rec.get("references", [])
        if pcls:
            key, kind = pcls[0], "match"
            d = STORE / "By Parcel" / key[0] / key[1:6] / key[6:]
        elif parties:
            key, kind = sanitize(parties[0]["name"]), "ref" if refs else "neither"
            d = STORE / "By Party" / key
        else:
            key, kind = did, "ref" if refs else "neither"
            d = STORE / "By Document"
        if frames:
            d.mkdir(parents=True, exist_ok=True)
            pdf = d / f"{datep}_{did}.pdf"
            pdf.write_bytes(img2pdf.convert(frames))
            rec["pdf"] = str(pdf.relative_to(STORE))
            with lock:
                stats["pdfs"] += 1
        elif total <= 0:
            rec["image"] = "imageless"
            with lock:
                stats["imageless"] += 1
        with lock:
            stats[kind] += 1
            with OUT.open("a", encoding="utf-8") as out:
                out.write(json.dumps(rec, separators=(",", ":")) + "\n")
    except fetch_pages.AccessDenied as e:
        stop.set()
        print(f"  REFUSED at {did} - STOPPING ALL: {e}", flush=True)
    except Exception as e:
        with lock:
            stats["fail"] += 1
        print(f"  {did} FAIL {type(e).__name__}", flush=True)

t0 = time.time()
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    for i, _ in enumerate(ex.map(one, todo), 1):
        if i % 500 == 0:
            el = time.time() - t0
            with lock:
                s = dict(stats)
            print(f"  {i}/{len(todo)} · {el:.0f}s · {i/el:.2f} docs/s · "
                  f"match {s['match']} ref {s['ref']} neither {s['neither']} "
                  f"· {s['pdfs']} pdfs ({s['pages']} pp) · "
                  f"imageless {s['imageless']}", flush=True)

el = time.time() - t0
n = stats["match"] + stats["ref"] + stats["neither"]
print(f"\nPILOT: {n} walked (+{stats['fail']} failed) in {el/60:.1f} min "
      f"= {n/el:.2f} docs/s · {stats['pages']/max(el,1):.1f} pg/s", flush=True)
for k in ("match", "ref", "neither", "imageless", "pdfs"):
    print(f"  {k:<10} {stats[k]}")
if n:
    total_walk = 416_343 + 1_339_151
    print(f"\nfull ACRIS walk ({total_walk:,} docs) at this pace: "
          f"{total_walk / (n/el) / 86400:.1f} days")
