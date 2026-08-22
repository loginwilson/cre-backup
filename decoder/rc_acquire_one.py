"""ONE RICHMOND DOCUMENT, END TO END — what the specification holds, and every hop.

    ACRIS_CORPUS_ROOT=D:/acris python rc_acquire_one.py [BBL]

Traces and TIMES the acquisition path for a single document so the cost per unit
is measured rather than assumed, and so the exact hop that stops is visible.
"""
import sqlite3, sys, time, pathlib, urllib.request, urllib.error
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP, rc_source as RC, rc_sync as RS

BBL = sys.argv[1] if len(sys.argv) > 1 else "5000150012"
c = sqlite3.connect("file:" + str(CP.SPEC_DB).replace("\\", "/") + "?mode=ro",
                    uri=True, timeout=300)
row = c.execute(
    "SELECT d.document_id, d.doc_type, d.recorded_date, d.image_state,"
    "       b.instrument, b.book, b.page"
    " FROM parcel_document pd"
    " JOIN document d ON d.document_id = pd.document_id"
    " LEFT JOIN rc_binding b ON b.document_id = d.document_id"
    " WHERE pd.bbl = ? AND substr(d.document_id,1,3)='RC_'"
    " ORDER BY d.recorded_date DESC LIMIT 1", (BBL,)).fetchone()
did, dtype, rec, img, instr, book, page = row
iid = did[3:]

print("  WHAT THE SPECIFICATION HOLDS")
print(f"    bbl            {BBL}")
print(f"    document_id    {did}")
print(f"    internal_id    {iid}        <- the acquisition key")
print(f"    instrument     {instr}      <- the official citation (rc_binding)")
print(f"    doc_type       {dtype}")
print(f"    recorded       {rec}")
print(f"    image_state    {img}")
print(f"    book/page      {book or '(none)'}/{page or '(none)'}")
print(f"    STORE          {CP.STORE}")

print("\n  THE PATH")
T = time.time()
t0 = time.time()
w = RS.Window("08/17/2026", "08/17/2026")
print(f"    hop 1  session + search        {time.time()-t0:>6.2f}s")

t0 = time.time()
d = w.detail(iid)
t_detail = time.time() - t0
print(f"    hop 2  detail page             {t_detail:>6.2f}s  "
      f"-> {len(d.get('parties') or [])} parties · {len(d.get('bbls') or [])} lots"
      f" · {d.get('amount')} · image={d.get('image_state')}")
for p in (d.get("parties") or [])[:4]:
    print(f"             {p['role']:<12} {p['name']}")

t0 = time.time()
url = RC.BASE + f"/ViewVscmsDocument/ViewContent?p_endorsementId={iid}"
req = urllib.request.Request(url)
req.add_header("User-Agent", RC.UA)
req.add_header("Referer", RC.BASE + f"/Search/ViewDocumentInfo/{iid}")
final = err = None
try:
    with w.s.op.open(req, timeout=60) as r:
        final, code = r.geturl(), r.status
except urllib.error.HTTPError as e:
    final, err = e.url, f"HTTP {e.code}"
except Exception as e:
    err = type(e).__name__
t_img = time.time() - t0
print(f"    hop 3  mint image url          {t_img:>6.2f}s")
print(f"             resolved -> {(final or '')[:96]}")
print(f"    hop 4  fetch image bytes       {'BLOCKED — ' + str(err) if err else 'ok'}")

dest = pathlib.Path(CP.STORE) / f"{did}.pdf"
print(f"\n  WOULD STORE AT  {dest}")
print(f"  TIME PER DOCUMENT (hops 1-3, session amortised): {t_detail + t_img:.2f}s")
print(f"  total this trace: {time.time()-T:.2f}s")
