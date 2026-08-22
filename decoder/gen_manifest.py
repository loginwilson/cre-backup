"""Regenerate the FULL DOCUMENT MANIFEST section of a parcel writeup.

The prose abbreviates companion ids ("...005") for readability. That is fine to
read and useless to verify: watch_parcels.py greps for full document ids, so an
abbreviated citation looks exactly like a document nobody wrote up. This appends
a table of every full id so coverage is checkable by machine rather than trusted.

Idempotent: the manifest is delimited and replaced, never appended twice.
"""
import json, pathlib, re, sys, urllib.request

HERE = pathlib.Path(__file__).parent
BEGIN = "<!-- MANIFEST:BEGIN -->"
END = "<!-- MANIFEST:END -->"


def get(u):
    with urllib.request.urlopen(u.replace(" ", "%20")) as r:
        return json.load(r)


def index_docs(borough, block, lot):
    out, off = set(), 0
    while True:
        r = get("https://data.cityofnewyork.us/resource/8h5j-fqxa.json"
                f"?borough={borough}&block={block}&lot={lot}"
                f"&$select=document_id&$order=:id&$limit=1000&$offset={off}")
        out |= {x["document_id"] for x in r}
        if len(r) < 1000:
            return out
        off += 1000


def master(ids):
    rows, ids = [], sorted(ids)
    for i in range(0, len(ids), 50):
        w = " in (" + ",".join("'" + c + "'" for c in ids[i:i + 50]) + ")"
        rows += get("https://data.cityofnewyork.us/resource/bnx9-e6tj.json"
                    f"?$where=document_id{w}&$select=document_id,doc_type,"
                    "document_date,recorded_datetime,document_amt&$limit=200")
    return {r["document_id"]: r for r in rows}


def build(borough, block, lot, path):
    ids = index_docs(borough, block, lot)
    m = master(ids)

    def key(i):
        r = m.get(i, {})
        return ((r.get("document_date") or r.get("recorded_datetime") or "")[:10], i)

    lines = [BEGIN, "", "---", "",
             f"## FULL DOCUMENT MANIFEST — all {len(ids)}, machine-checkable", "",
             "Every document ACRIS indexes against this lot, in instrument-date "
             "order. The prose above abbreviates companion ids (`...005`); this "
             "table spells them out so `watch_parcels.py` verifies coverage "
             "instead of trusting the narrative.", "",
             "| date | document_id | type | index amt |", "|---|---|---|---|"]
    for i in sorted(ids, key=key):
        r = m.get(i, {})
        d = (r.get("document_date") or "")[:10]
        if not d:
            d = "rec " + (r.get("recorded_datetime") or "")[:10]
        amt = float(r.get("document_amt") or 0)
        a = "$" + format(amt, ",.0f") if amt else ""
        lines.append("| " + d + " | `" + i + "` | " + r.get("doc_type", "?") +
                     " | " + a + " |")
    lines += ["", END, ""]
    block_text = "\n".join(lines)

    p = HERE / path
    txt = p.read_text(encoding="utf-8")
    if BEGIN in txt:
        txt = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?",
                     block_text, txt, flags=re.S)
    else:
        txt = txt.rstrip("\n") + "\n\n" + block_text
    p.write_text(txt, encoding="utf-8")
    print(f"{path}: manifest with {len(ids)} documents")


if __name__ == "__main__":
    build("1", "800", "49", "LOT49_EVENTS.md")
