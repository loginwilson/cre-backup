"""MAP EVERY DOCUMENT OF A TYPE — exact page counts, not extrapolations.

⚠ WHY THIS MATTERS MORE THAN IT SOUNDS. Every storage figure, every acquisition
estimate and every "can we afford this type" answer in this project has rested
on PAGE COUNTS EXTRAPOLATED FROM ONE PARCEL. ZONE's 6.5 pages/doc and EASE's 42
came from n=2 each, on lot 49, and between them they carry the whole 1.22M-page
zoning estimate.

Mapping is ~199 requests/second and 13 KB apiece. The entire zoning and
air-rights universe — 68,294 documents — is about six minutes. There is no
reason to estimate any of it.

⚠ AND THE MAP IS NOT JUST A PAGE COUNT. It gives, per document:
    hid_TotalPages   what GetImage will serve
    instrument       which pages are the actual instrument
    hid_Sup          where supporting documents start
    hid_Tax          whether an RP-5217 exists (the third price witness)
which is what makes acquisition targeted instead of a range scan — the
technique that got this project blocked in August.
"""
import asyncio
import json
import pathlib
import sys
import time

import amap
import bulk

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MASTER = "bnx9-e6tj"

# the types that answer ENVELOPE and ENCUMBER, smallest first so a partial run
# still finishes something useful
TYPES = ["DECM", "AIRRIGHT", "MERG", "DEVR", "EASE", "ZONE"]


def ids_for(doc_type):
    rows = bulk.socrata(MASTER, where=f"doc_type='{doc_type}'",
                        select="document_id", paginate=True)
    # ⚠ DEDUPE. The MASTER pull returns exact duplicate rows — 16 of them on
    # DEVR, same document_id and CRFN. Every "N documents" figure quoted from a
    # count(1) is a ROW count and runs ~1.3% high.
    seen, out = set(), []
    for r in rows:
        d = r["document_id"]
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out, len(rows)


async def main(types):
    summary = []
    for t in types:
        print(f"\n{'='*66}\n{t}")
        t0 = time.time()
        ids, nrows = ids_for(t)
        print(f"  {nrows:,} rows -> {len(ids):,} distinct documents "
              f"({nrows-len(ids)} duplicate rows)")
        await amap.run(ids, conc=16)
        # read back only this type's maps
        got = {}
        idset = set(ids)
        for line in pathlib.Path("docmaps.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r["doc_id"] in idset and r.get("hid_TotalPages"):
                    got[r["doc_id"]] = r
        pages = sum(r["hid_TotalPages"] for r in got.values())
        inst = sum(r.get("instrument_pages") or r["hid_TotalPages"]
                   for r in got.values())
        tax = sum(1 for r in got.values() if r.get("hid_Tax"))
        row = {"type": t, "docs": len(ids), "mapped": len(got),
               "pages": pages, "instrument_pages": inst, "with_tax": tax,
               "mean_pp": round(pages / max(len(got), 1), 1),
               "secs": round(time.time() - t0, 1)}
        summary.append(row)
        print(f"  mapped {len(got):,}/{len(ids):,} · {pages:,} pages "
              f"(mean {row['mean_pp']}) · {inst:,} instrument · "
              f"{tax} with RP-5217 · {row['secs']}s")
        json.dump(summary, open("_type_maps.json", "w"), indent=1)

    print(f"\n{'='*66}\n{'type':<10}{'docs':>9}{'pages':>12}{'mean':>7}"
          f"{'acquire @24/s':>15}{'OCR @218/hr':>13}")
    tp = ti = 0
    for r in summary:
        tp += r["pages"]; ti += r["instrument_pages"]
        print(f"{r['type']:<10}{r['docs']:>9,}{r['pages']:>12,}{r['mean_pp']:>7}"
              f"{r['instrument_pages']/24/3600:>13.1f} h"
              f"{r['instrument_pages']/218/24:>11.1f} d")
    print(f"{'TOTAL':<10}{'':>9}{tp:>12,}{'':>7}{ti/24/3600:>13.1f} h"
          f"{ti/218/24:>11.1f} d")
    # ⚠ THE OCR COLUMN IS SERIAL, SINGLE CORE, AND IS THE REAL CONSTRAINT.
    # Acquisition is hours; extraction is months. Read the two columns together
    # or the plan comes out wrong.


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or TYPES))
