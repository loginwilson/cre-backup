"""PUT THE DISPUTED RUNS BACK ON THE PAGE. The bridge between two address spaces.

    python locate.py --doc 2015022400608001 --ocr ppbox/2015022400608001
    python locate.py --doc ... --ocr ... --crops        # write the PNGs

⚠ THE CHANNELS SHARE NO ADDRESS SPACE AND THAT IS THE WHOLE PROBLEM.
Paddle knows WHERE (polygons) but reads characters worse. The VLM reads
characters better but returns no coordinates at all. The index knows values but
never looked at the page. fuse.py built the first shared address - a token
index both readers agree on. This file builds the second - the mapping from
that token index onto pixels - and only the OCR channel can supply it.

Without this step the escalation queue is a list of complaints. With it, every
disputed run is a rectangle a stronger model or a person can be shown.

⚠ pp_doc.py JOINS ITS ITEMS WITH A SINGLE SPACE TO MAKE THE .txt, so walking
the items in order and tokenising each one reproduces exactly the token stream
fuse.py aligned against. That equivalence is the only reason this mapping is
sound, and it breaks the moment the OCR channel's .txt is written by anything
other than that join - which is why --ocr must name a pp_doc run, not one of
the old bakeoff engines whose .txt has no sibling .json.

⚠ A BOX FROM A ROTATED PASS IS IN THE ROTATED IMAGE'S FRAME.
pp_doc can read a page at 0/90/270 and keeps every item from every angle. Those
boxes are NOT comparable: a polygon found at 90 degrees indexes the rotated
bitmap, not the original. Cropping the original with it returns a plausible
rectangle of the WRONG part of the page - a silent error that looks like a
successful crop. Items with angle != 0 are refused here and reported, never
quietly cropped.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "bakeoff" / "out"
PAGES = HERE.parent / "bakeoff" / "pages"
EV = HERE / "_evidence"

TOKEN = re.compile(r"\S+")
PAD = 12          # px of breathing room around a crop
MIN_H = 24        # a 3px-tall crop is unreadable even when it is correct


def token_index(items):
    """Map every OCR token position -> the recognition item it came from.

    Returns a list the same length as the channel's token stream, each entry
    the index of the item that produced it.
    """
    owner = []
    for k, it in enumerate(items):
        for _ in TOKEN.finditer(it.get("text") or ""):
            owner.append(k)
    return owner


def unrotate(x, y, angle, W, H):
    """Map a point in PIL's rotate(angle, expand=True) output back to the original.

    ⚠ DERIVED BY MEASUREMENT, NOT FROM MEMORY. A sign error here does not throw
    - it returns a plausible rectangle of the WRONG part of the page, and the
    crop looks like a successful one. The mapping was verified against a
    single-pixel probe at both diagonals, all four corners and interior points,
    for every angle, before this function was allowed to replace the refusal it
    supersedes. `expand=True` swaps W and H at 90 and 270, which is exactly the
    detail an eyeballed derivation gets wrong.
    """
    a = angle % 360
    if a == 0:
        return x, y
    if a == 90:
        return W - 1 - y, x
    if a == 180:
        return W - 1 - x, H - 1 - y
    if a == 270:
        return y, H - 1 - x
    # ⚠ ARBITRARY ANGLES ARE NOT SUPPORTED AND MUST NOT BE APPROXIMATED.
    # pp_doc only ever renders 0/90/180/270; anything else means the caller
    # changed and this mapping is no longer the right one.
    raise ValueError(f"unrotate only handles right angles, got {angle}")


def bbox(boxes):
    xs = [p[0] for b in boxes for p in b]
    ys = [p[1] for b in boxes for p in b]
    return [min(xs), min(ys), max(xs), max(ys)]


def anchor_region(runs, idx, ocr_name, items, owner, page_w=None, page_h=None):
    """Bracket an OCR-less run between the nearest AGREED runs on either side.

    ⚠ THIS IS THE ONLY WAY TO TELL "PADDLE MISSED IT" FROM "THE VLM MADE IT UP",
    AND THE TWO ARE INDISTINGUISHABLE IN THE TEXT. A run the VLM emitted and
    Paddle never saw has no box, because only Paddle produces boxes - so the
    obvious move, cropping the run's own coordinates, is impossible for exactly
    the runs where the question matters most.

    The agreed runs are the way in. They are the shared address space: both
    channels read them, and Paddle carries their pixels. Whatever the VLM saw
    between two agreed anchors must physically lie between their boxes, so the
    union of the anchors is a region guaranteed to contain it if it exists at
    all. Look there and the answer is immediate: the text is on the page and
    Paddle missed it, or it is not and the VLM invented it.

    A missing anchor (run at the very start or end of a page) yields no region
    rather than a guess - an unbounded crop would "contain" anything.
    """
    prev_b = next_b = None
    for j in range(idx - 1, -1, -1):
        if runs[j]["status"] == "agreed":
            prev_b, _ = locate_run(runs[j], ocr_name, items, owner, page_w, page_h)
            if prev_b:
                break
    for j in range(idx + 1, len(runs)):
        if runs[j]["status"] == "agreed":
            next_b, _ = locate_run(runs[j], ocr_name, items, owner, page_w, page_h)
            if next_b:
                break
    if not prev_b or not next_b:
        return None, "no_anchor"
    return [min(prev_b[0], next_b[0]), min(prev_b[1], next_b[1]),
            max(prev_b[2], next_b[2]), max(prev_b[3], next_b[3])], "anchored"


def locate_run(run, ocr_name, items, owner, page_w=None, page_h=None):
    """Turn one run's OCR token span into a pixel rectangle, or say why not."""
    span = (run.get("span") or {}).get(ocr_name)
    if not span or span[0] >= span[1]:
        # The OCR channel contributed nothing to this run - there is no box to
        # find. That is a real state (the VLM saw text Paddle missed entirely),
        # not a failure of this function.
        return None, "no_ocr_tokens"
    j1, j2 = span
    if j1 >= len(owner):
        return None, "span_past_end"
    ks = sorted(set(owner[j1:min(j2, len(owner))]))
    if not ks:
        return None, "no_items"
    used = [items[k] for k in ks]
    boxes, rotated = [], False
    for u in used:
        if not u.get("box"):
            continue
        ang = u.get("angle") or 0
        if ang:
            if not (page_w and page_h):
                # Without the ORIGINAL page size the mapping cannot be done,
                # and guessing it silently misplaces the crop.
                return None, "rotated_no_page_size"
            rotated = True
            boxes.append([list(unrotate(px, py, ang, page_w, page_h))
                          for px, py in u["box"]])
        else:
            boxes.append(u["box"])
    if not boxes:
        return None, "item_without_box"
    return bbox(boxes), ("ok_unrotated" if rotated else "ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--ocr", required=True,
                    help="pp_doc tag holding the .json items, e.g. ppbox/<doc>")
    ap.add_argument("--crops", action="store_true", help="write crop PNGs")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    rec = json.loads((EV / f"{a.doc}.json").read_text(encoding="utf-8"))
    ocr_name = rec["channels"]["ocr"]
    src = OUT / a.ocr
    if not src.is_dir():
        raise SystemExit(f"  no pp_doc output at {src}")

    cropdir = EV / f"{a.doc}_crops"
    if a.crops:
        cropdir.mkdir(exist_ok=True)
        from PIL import Image

    located, reasons, rows = 0, {}, []
    for p in rec["pages"]:
        ij = src / f"{p['page']}.json"
        if not ij.exists():
            reasons["no_items_file"] = reasons.get("no_items_file", 0) + 1
            continue
        items = json.loads(ij.read_text(encoding="utf-8"))["items"]
        owner = token_index(items)
        img = None
        # ⚠ NEEDED EVEN WHEN NOT CROPPING - the un-rotate mapping is
        # defined against the ORIGINAL page dimensions.
        pf0 = PAGES / a.doc / f"{p['page']}.png"
        pw = ph = None
        if pf0.exists():
            from PIL import Image as _I
            with _I.open(pf0) as _im:
                pw, ph = _im.size
        for i, run in enumerate(p["runs"]):
            if run["status"] in ("agreed", "unaligned"):
                continue
            box, why = locate_run(run, ocr_name, items, owner, pw, ph)
            if box is None and why in ("no_ocr_tokens",):
                # The VLM saw text Paddle never emitted. Bracket it instead.
                box, why = anchor_region(p["runs"], i, ocr_name, items, owner, pw, ph)
            reasons[why] = reasons.get(why, 0) + 1
            if box is None:
                continue
            located += 1
            row = {"page": p["page"], "run_index": i, "status": run["status"],
                   "n_tokens": run["n_tokens"], "box": box, "how": why,
                   "vlm": run.get(rec["channels"]["vlm"]),
                   "ocr": run.get(ocr_name)}
            rows.append(row)
            if a.crops and (not a.limit or located <= a.limit):
                pf = PAGES / a.doc / f"{p['page']}.png"
                if not pf.exists():
                    continue
                if img is None:
                    img = Image.open(pf)
                x0, y0, x1, y1 = box
                if y1 - y0 < MIN_H:
                    c = (y0 + y1) // 2
                    y0, y1 = c - MIN_H // 2, c + MIN_H // 2
                crop = img.crop((max(0, x0 - PAD), max(0, y0 - PAD),
                                 min(img.width, x1 + PAD),
                                 min(img.height, y1 + PAD)))
                name = f"{p['page']}_r{i:03d}_{run['status']}.png"
                crop.save(cropdir / name)
                row["crop"] = name

    (EV / f"{a.doc}.located.json").write_text(json.dumps(rows, indent=1),
                                              encoding="utf-8")
    total = sum(reasons.values())
    print(f"  {a.doc}   open runs {total}   located {located}"
          f" ({located/total:.0%})" if total else f"  {a.doc}  nothing open")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"    {k:24} {v:>5}")
    if a.crops:
        print(f"\n  crops -> {cropdir}")
    print(f"  rows  -> {EV / f'{a.doc}.located.json'}")


if __name__ == "__main__":
    main()
