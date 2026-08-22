"""DEVR validator — runs BEFORE any parse is accepted (validator-first principle).

Input: the decoder's JSON for one document (schema in decoder-contract.md).
Output: (tier, checks) where every check is {name, arithmetic, result} and
result is pass | fail | not_applicable. A fail is a first-class finding; the
document is stored as failed_validation, never silently repaired.
"""
from math import isclose, ceil

TOL = 1.0  # square feet; charts round to whole feet, some to 2dp


def _get(quantities, name_contains, lot=None):
    for q in quantities:
        if name_contains.lower() in (q.get("name") or "").lower():
            if lot is None or str(q.get("applies_to_lot") or "") == str(lot):
                return q.get("value")
    return None


def check_conservation(env):
    """env: {bbl: {lot_area, generated, retained, excess, after_transfer, far}}
    Yields the internal-arithmetic battery for chart-bearing documents."""
    checks = []
    lots = list(env)
    tot_gen = sum(v.get("generated") or 0 for v in env.values())
    tot_after = sum(v.get("after_transfer") or 0 for v in env.values())
    if all(v.get("generated") is not None for v in env.values()) and tot_gen:
        checks.append(dict(
            name="sum(after_transfer)==sum(generated)",
            arithmetic=f"{tot_after}=={tot_gen}",
            result="pass" if isclose(tot_after, tot_gen, abs_tol=TOL) else "fail"))
    for bbl, v in env.items():
        g, r, x = v.get("generated"), v.get("retained"), v.get("excess")
        if None not in (g, r, x):
            checks.append(dict(
                name=f"retained+excess==generated [{bbl}]",
                arithmetic=f"{r}+{x}=={g}",
                result="pass" if isclose(r + x, g, abs_tol=TOL) else "fail"))
        la, far = v.get("lot_area"), v.get("far")
        if None not in (la, far, g):
            checks.append(dict(
                name=f"lot_area*FAR==generated [{bbl}]",
                arithmetic=f"{la}*{far}=={g}",
                result="pass" if isclose(la * far, g, abs_tol=TOL) else "fail"))
        pr, ta = v.get("pro_rata"), v.get("after_transfer")
        if None not in (pr, ta) and tot_gen:
            checks.append(dict(
                name=f"pro_rata==after/total [{bbl}]",
                arithmetic=f"{pr}=={ta}/{tot_gen}",
                result="pass" if isclose(pr, ta / tot_gen, abs_tol=0.0005) else "fail"))
    return checks


def check_taxes(consideration, rptt, rett, commercial=True):
    """Cover-page transfer taxes vs stated consideration. One-directional:
    a zero tax line is not_applicable (tax may sit on a sibling document)."""
    checks = []
    if consideration and rptt:
        rate = 0.026 if False else (0.02625 if commercial and consideration >= 500000
                                    else 0.01425)
        expect = round(consideration * rate, 2)
        checks.append(dict(
            name="NYC RPTT == consideration × rate",
            arithmetic=f"{consideration}×{rate}={expect} vs {rptt}",
            result="pass" if isclose(expect, rptt, abs_tol=1.0) else "fail"))
    else:
        checks.append(dict(name="NYC RPTT == consideration × rate",
                           arithmetic="tax absent on this sibling",
                           result="not_applicable"))
    if consideration and rett:
        expect = ceil(consideration / 500.0) * 2.0
        checks.append(dict(
            name="NYS RETT == ceil(consideration/500)×$2",
            arithmetic=f"ceil({consideration}/500)×2={expect} vs {rett}",
            result="pass" if isclose(expect, rett, abs_tol=2.0) else "fail"))
    else:
        checks.append(dict(name="NYS RETT == ceil(consideration/500)×$2",
                           arithmetic="tax absent on this sibling",
                           result="not_applicable"))
    return checks


def tier(checks):
    ran = [c for c in checks if c["result"] != "not_applicable"]
    if any(c["result"] == "fail" for c in ran):
        return "failed_validation"
    internal = [c for c in ran if "==" in c["name"] and "RPTT" not in c["name"]
                and "RETT" not in c["name"]]
    if internal:
        return "arithmetic"
    if ran:
        return "external"
    return "structural"
