"""DOF — the VALUE axis: assessment, exemptions, abatements, sales, distress.

The last mapped-but-unbuilt source, and the one that answers questions the
envelope cannot: what is it worth, what does it pay, what does it owe, and what
did it last trade for.

⚠ `parid` IS A BBL under another name. Verified 799/800 sampled rows of
`muvi-b6kx` decode cleanly to the same boro/block/lot the row carries
separately. That makes it the SIXTH parcel-key form in this project:

    BBL string · boro/block/lot (FIVE borough spellings) · registrationid ·
    buildingid · BIN · parid

Key formats here, measured 2026-08-05:
    a5nd-6mit  assessment CHANGE   `parid` only
    muvi-b6kx  exemption detail    `parid` + boro NUMERIC '1' + block/lot unpadded
    rgyu-ii48  abatement detail    `parid` only
    w2pb-icbu  annualized sales    `bbl` + borough NUMERIC + block/lot unpadded
    9rz4-mjek  tax lien sale       borough NUMERIC + block/lot unpadded, NO bbl
    aht6-vxai  Article 7 petitions no parcel key in the sample — needs a look
    rgy2-tti8  assessment roll     **HTTP 403** — not openly queryable

Why these matter for a DEVELOPMENT decoder, not just a valuation one:
  * **a5nd-6mit assessment CHANGE** — "a large jump often follows a completed
    alteration or a lost exemption". A LIFECYCLE SIGNAL, not a valuation input.
  * **muvi-b6kx exemptions** — 421-a, ICAP. These are the subsidies that make a
    development pencil, and their EXPIRY is a dated event.
  * **aht6-vxai Article 7** — the owner suing the City over the assessment. An
    owner asserting in court that the property is worth less than assessed is a
    motivated seller wearing a disguise.
  * **9rz4-mjek lien sale** — the distress ladder: noticed, sold, chronic.
"""
import sys, pathlib
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk
import keys

ASSESS_CHANGE = "a5nd-6mit"
EXEMPTIONS = "muvi-b6kx"
ABATEMENTS = "rgyu-ii48"
SALES = "w2pb-icbu"
LIEN_SALE = "9rz4-mjek"
ARTICLE7 = "aht6-vxai"

SPEC = {
    ASSESS_CHANGE: {"key": "parid"},
    EXEMPTIONS:    {"key": "parid"},
    ABATEMENTS:    {"key": "parid"},
    SALES:         {"key": "bbl"},
    LIEN_SALE:     {"key": "boro_block_lot", "col": "borough", "case": "num"},
}


def control_query_ok(dataset):
    """Self-calibrating, branching on the dataset's actual key."""
    sample = bulk.socrata(dataset, limit=1, paginate=False)
    if not sample:
        return False, f"{dataset}: returned nothing"
    row, sp = sample[0], SPEC[dataset]
    if sp["key"] in ("parid", "bbl"):
        val = row.get(sp["key"])
        if not val:
            return False, f"{dataset}: sample has no {sp['key']} — has {sorted(row)[:6]}"
        found = bulk.socrata(dataset, where=f"{sp['key']}='{val}'", limit=5, paginate=False)
        return bool(found), f"{dataset}: {sp['key']}={val!r} -> {len(found)} rows"
    boro, blk = row.get(sp["col"]), row.get("block")
    if not (boro and blk):
        return False, f"{dataset}: sample lacks {sp['col']}/block — has {sorted(row)[:6]}"
    found = bulk.socrata(dataset, where=f"{sp['col']}='{boro}' and block='{blk}'",
                         limit=5, paginate=False)
    return bool(found), f"{dataset}: {sp['col']}={boro!r} block={blk!r} -> {len(found)} rows"


def rows_for(bbls, dataset):
    sp = SPEC[dataset]
    vals = [str(int(b)) for b in bbls]
    if sp["key"] in ("parid", "bbl"):
        return bulk.socrata_in(dataset, sp["key"], vals)
    groups = defaultdict(set)
    wanted = set()
    for b in bbls:
        boro, blk, lot = keys.parts(b)
        groups[str(boro)].add(str(blk))
        wanted.add((str(boro), str(blk), str(lot)))
    out = []
    for boro, blocks in groups.items():
        blocks = sorted(blocks)
        for i in range(0, len(blocks), bulk.IN_CLAUSE_MAX):
            joined = ",".join(f"'{x}'" for x in blocks[i:i + bulk.IN_CLAUSE_MAX])
            out += bulk.socrata(dataset, where=f"{sp['col']}='{boro}' and block in({joined})")
    # strict lot filter — an equal count before and after means it did nothing
    strict = [r for r in out
              if (str(r.get(sp["col"])), str(r.get("block")), str(r.get("lot"))) in wanted]
    return strict


if __name__ == "__main__":
    for ds in (ASSESS_CHANGE, EXEMPTIONS, ABATEMENTS, SALES, LIEN_SALE):
        ok, detail = control_query_ok(ds)
        print(f"  [{'PASS' if ok else 'FAIL'}] {detail}")
