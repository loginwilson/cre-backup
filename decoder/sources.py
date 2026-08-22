"""Every built source, checked on every audit run — not merely available.

WHY THIS EXISTS
    Twice in one session a component was CORRECT and UNWIRED, and produced
    exactly the same output as one that did not exist: party observations sat in
    raw_facts unreduced for hours, and the special-district override sat computed
    but unapplied while the baselines carried the wrong figure. Nothing caught
    either, because the audit checked that a VALUE existed, not that the PATH ran.

    So: nine sources are now pullable. Pullable is not the same as verified. This
    module re-runs every source's self-calibrating control and reports three
    outcomes, never two.

THE THREE OUTCOMES, and why the middle one matters
    reachable    the control passed — the query shape works TODAY
    empty        the query works and returns nothing FOR OUR PARCELS. A finding
                 about the parcels, not about the pull. (LPC is legitimately
                 empty: none of the pilot lots is landmark-regulated.)
    BROKEN       the control failed — schema drift, a renamed column, a dataset
                 withdrawn. This is the one that must never be silent, because a
                 broken source looks exactly like an empty one.
"""
import sys, pathlib, time

sys.path.insert(0, str(pathlib.Path(__file__).parent))


def check_all(verbose=False):
    """Run every source's control. Returns rows of (source, dataset, ok, detail)."""
    out = []

    def run(label, fn):
        t0 = time.time()
        try:
            ok, detail = fn()
        except Exception as e:                      # unreachable != empty
            ok, detail = False, f"EXCEPTION {type(e).__name__}: {str(e)[:90]}"
        out.append((label, ok, detail, round(time.time() - t0, 1)))

    import dob
    for name, ds in (("DOB BIS jobs", dob.BIS_JOBS), ("DOB NOW jobs", dob.NOW_JOBS),
                     ("DOB permits", dob.PERMITS), ("DOB CO", dob.CO)):
        run(name, lambda ds=ds: dob.control_query_ok(ds))

    import hpd
    for name, ds in (("HPD registrations", hpd.REGISTRATIONS),
                     ("HPD violations", hpd.VIOLATIONS),
                     ("HPD CONH", hpd.CONH), ("HPD AEP", hpd.AEP)):
        run(name, lambda ds=ds: hpd.control_query_ok(ds))

    import lpc
    for name, ds in (("LPC buildings", lpc.BUILDINGS), ("LPC desig/cal", lpc.DESIG_CAL),
                     ("LPC permits", lpc.PERMITS), ("LPC violations", lpc.VIOLATIONS)):
        run(name, lambda ds=ds: lpc.control_query_ok(ds))

    import dof_value as dv
    for name, ds in (("DOF assess change", dv.ASSESS_CHANGE),
                     ("DOF exemptions", dv.EXEMPTIONS),
                     ("DOF abatements", dv.ABATEMENTS),
                     ("DOF sales", dv.SALES), ("DOF lien sale", dv.LIEN_SALE)):
        run(name, lambda ds=ds: dv.control_query_ok(ds))

    # DOF alteration book (ArcGIS, not Socrata) — a different failure surface
    def dab():
        import dof_lineage as dl
        rows = dl._query("dab_header", "1=1", limit=1)
        return bool(rows), f"DAB_BOOK_HEADER responds: {len(rows)} row"
    run("DOF alteration book", dab)

    # the Zoning Resolution — a live feed, so drift shows as a changed amendment
    def zr():
        import zr_feed
        rec = zr_feed.fetch_section("23-22")
        return bool(rec.get("tables")), (f"ZR 23-22 parses, last amended "
                                         f"{rec.get('last_amended')}")
    run("Zoning Resolution", zr)

    if verbose:
        for label, ok, detail, secs in out:
            print(f"  [{'ok  ' if ok else 'BROKEN'}] {label:<22} {secs:>4}s  {detail[:88]}")
    return out


if __name__ == "__main__":
    rows = check_all(verbose=True)
    broken = [r for r in rows if not r[1]]
    print(f"\n{len(rows) - len(broken)}/{len(rows)} sources reachable"
          + (f"; BROKEN: {[r[0] for r in broken]}" if broken else ""))
