"""THE KEYING PROGRAM'S STATUS LINE (login format, 2026-08-20):

    <pulled> pulled · <total> total · +<delta> · +<pct>% · <overall>% overall

One line per engine. Delta = since the LAST time this script ran (state
sits beside the ledger). Totals: RD pass = the sealed universe 24,039,303;
PP bulk = the five dataset counts (cached after first fetch); pdf store =
count only (its denominator is phase-dependent).
"""
import json
import pathlib
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP

UNIVERSE = 24_039_303
LEDGER = CP.NAV_WORK / "rd_repull.jsonl"
STATE = CP.NAV_WORK / "keying_status_state.json"
STORE = pathlib.Path(r"D:\CRE Decoding System\02 Acquisitions"
                     r"\Legal Instruments Acquisition")

prev = json.loads(STATE.read_text()) if STATE.exists() else {}


def count_lines(p):
    if not p.exists():
        return 0
    n = 0
    with p.open("rb") as fh:
        while chunk := fh.read(1 << 22):
            n += chunk.count(b"\n")
    return n


def line(name, pulled, total):
    d = pulled - prev.get(name, 0)
    pd = 100 * d / total if total else 0
    ov = 100 * pulled / total if total else 0
    tt = f"{total:,} total · " if total else ""
    print(f"{name:<10} {pulled:>12,} pulled · {tt}+{d:,} · "
          f"+{pd:.3f}% · {ov:.2f}% overall")
    return pulled


now = {}

# RD pass (page-walk ledger) against the sealed universe
now["rd"] = line("rd pass", count_lines(LEDGER), UNIVERSE)

# PP bulk family
pp_total = prev.get("_pp_total", 0)
pp_have = 0
try:
    con = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True, timeout=60)
    for t in ("pp_master", "pp_legals", "pp_parties", "pp_references",
              "pp_remarks"):
        try:
            pp_have += con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except sqlite3.OperationalError:
            pass
    con.close()
except sqlite3.OperationalError:
    pp_have = prev.get("pp bulk", 0)
if not pp_total:
    try:
        import bulk
        pp_total = sum(int(bulk.socrata(ds, select="count(1) as n")[0]["n"])
                       for ds in ("sv7x-dduq", "uqqa-hym2", "nbbg-wtuz",
                                  "6y3e-jcrc", "fuzi-5ks9"))
    except Exception:
        pp_total = 0
now["pp bulk"] = line("pp bulk", pp_have, pp_total)
now["_pp_total"] = pp_total

# pdf store (files landed; denominator is phase-dependent, so count only)
pdfs = sum(1 for _ in STORE.rglob("*.pdf")) if STORE.exists() else 0
now["pdf store"] = line("pdf store", pdfs, 0)

now["_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
if prev.get("_at"):
    print(f"\n(deltas since {prev['_at']})")
STATE.write_text(json.dumps(now))
