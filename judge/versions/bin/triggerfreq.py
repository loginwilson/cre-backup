"""triggerfreq.py — the R-9 trigger-frequency audit frame.

A owns this audit (RULINGS-v1.md R-9, R-8). For each rule with a conditional
trigger: how often does it actually fire? A rule that never fires and a rule
that always fires are both defects, and both are invisible from the rule's text.

    python triggerfreq.py --trigger "M-DEED:doc_type LIKE 'DEED%'" \
                          --trigger "multi-parcel:n_parcels > 1"
    python triggerfreq.py --file triggers.txt
    python triggerfreq.py --file triggers.txt --json

R-9'S STATED LIMIT, WHICH THIS TOOL PRINTS EVERY RUN
    Frequency catches vacuity and over-capture and says NOTHING about whether a
    boundary is drawn correctly, because a wrong classification fires at a
    perfectly plausible rate. It must never stand in for boundary testing.

WHY THIS TOOL REFUSES TO PRINT A CORPUS-WIDE RATE
    The orchestrator's constraint is built in rather than noted beside: the
    slate is a stratified sample, so facet counts are sample counts and never
    corpus proportions. A trigger figure that read as a population rate would be
    exactly the plausible-but-unfounded number this project exists to prevent —
    and it would be this audit that introduced it.

    It is worse than "a sample", and the slate's own meta says so. TWO DESIGNS
    LIVE IN ONE TABLE:

      acris      a sequential sweep that reached meta.last_id. Because the ACRIS
                 documentation floor sits around October 2003, that sweep is a
                 NEAR-CENSUS of the readable ACRIS window — so an acris row
                 share is meaningful, but only for that ~10-month window, and
                 never for ACRIS generally or for the corpus.
      richmond   a 500-rows-per-anchor cluster sample at anchors spread by id
      film_ft    namespace position, NOT proportionally to stratum size. The
      film_bk    inclusion probability is unknown and differs per stratum, so no
                 weighting to a population is possible. Counts only.

    Therefore: per-stratum figures, each labelled with what it is an estimate
    OF, and no pooled number anywhere.

ROW RATE IS NOT TRANSACTION RATE
    An ACRIS id is date(8) + sequence(5) + item(3): 2003010600019001..004 are
    four documents of one filing package (mean 1.57 rows per package). Each is
    extracted independently, so the ROW share is what a per-document trigger
    audit wants — but a share of *transactions* is a different number, and both
    are reported so neither can be mistaken for the other.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SLATE = pathlib.Path(r"D:\CRE Decoding System\04 Extractions\loop\ledger\slate.db")

# >> acris ids are date8+seq5+item3; the first 13 identify the filing package.
#    the other namespaces have no package structure in the id, so each row is
#    its own cluster and the package figure equals the row figure.
PKG = {"acris": "substr(id,1,13)"}

VACUOUS = 0.005          # fires on under 0.5% of a stratum
SATURATED = 0.95         # fires on over 95% of a stratum


def strata(c) -> list[tuple[str, int, int]]:
    return c.execute(
        "SELECT source, COUNT(*), COUNT(DISTINCT %s) FROM slate "
        "GROUP BY source ORDER BY COUNT(*) DESC"
        % "CASE source WHEN 'acris' THEN substr(id,1,13) ELSE id END"
    ).fetchall()


def provenance(c) -> dict:
    meta = dict(c.execute("SELECT k, v FROM meta").fetchall())
    lo, hi = c.execute(
        "SELECT MIN(recorded_date), MAX(recorded_date) FROM slate "
        "WHERE source='acris'").fetchone()
    return {"mode": meta.get("mode"), "per_anchor": meta.get("per_anchor"),
            "last_id": meta.get("last_id"),
            "acris_window": [lo, hi],
            "total": c.execute("SELECT COUNT(*) FROM slate").fetchone()[0]}


def run(c, name: str, where: str) -> dict:
    out = {"trigger": name, "where": where, "strata": {}, "eras": {}}
    for src, n_rows, n_pkgs in strata(c):
        pk = PKG.get(src, "id")
        try:
            r, p = c.execute(
                "SELECT COUNT(*), COUNT(DISTINCT %s) FROM slate "
                "WHERE source = ? AND (%s)" % (pk, where), (src,)).fetchone()
        except sqlite3.Error as e:
            sys.exit("trigger %r is not valid SQL against the slate: %s\n"
                     "  %s" % (name, e, where))
        out["strata"][src] = {
            "rows": r, "rows_total": n_rows,
            "row_share": (r / n_rows) if n_rows else None,
            "packages": p, "packages_total": n_pkgs,
            "package_share": (p / n_pkgs) if n_pkgs else None,
            # >> what the share is an estimate OF, carried with the number so it
            #    cannot be quoted away from its caveat
            "estimate_of": ("readable ACRIS window (near-census)" if src == "acris"
                            else "sampled rows only — inclusion probability "
                                 "unknown, NOT a population rate"),
        }
    # >> eras MUST be reported within stratum. Pooled era bands are confounded
    #    with stratum in this slate: the 1950s and 1990s are entirely richmond,
    #    the 2000s almost entirely acris. A pooled "era gap" would usually be a
    #    stratum gap wearing a date, which is the kind of plausible-but-wrong
    #    number this audit exists not to produce.
    for src, era, tot, hit in c.execute(
            "SELECT source, (recorded_year/10)*10, COUNT(*), "
            "SUM(CASE WHEN (%s) THEN 1 ELSE 0 END) FROM slate "
            "WHERE recorded_year IS NOT NULL "
            "GROUP BY source, (recorded_year/10)*10 ORDER BY source, 2" % where):
        out["eras"].setdefault(src, {})["%ds" % era] = {
            "rows": hit or 0, "rows_total": tot}
    return out


def verdicts(res: dict) -> list[str]:
    v = []
    for src, s in res["strata"].items():
        if s["rows_total"] < 200:
            continue
        share = s["row_share"]
        if share == 0:
            v.append("VACUOUS in %s — never fires in %d sampled rows"
                     % (src, s["rows_total"]))
        elif share < VACUOUS:
            v.append("NEAR-VACUOUS in %s — %.3f%% (%d rows)"
                     % (src, share * 100, s["rows"]))
        elif share > SATURATED:
            v.append("SATURATED in %s — %.1f%%; a trigger that always fires is "
                     "not a trigger" % (src, share * 100))
    fires = [s for s in res["strata"].values() if s["rows"]]
    if len(fires) == 1 and len(res["strata"]) > 1:
        only = [k for k, s in res["strata"].items() if s["rows"]][0]
        v.append("SINGLE-STRATUM — fires only in %s. This is the M-LEASE "
                 "failure shape: correct in principle, vacuous where the "
                 "corpus actually is." % only)
    # era gaps are only meaningful WITHIN a stratum (see run(); pooled bands are
    # confounded with stratum), and only where the trigger fires in that stratum
    for src, bands in res["eras"].items():
        if not res["strata"].get(src, {}).get("rows"):
            continue
        live = {e: d for e, d in bands.items() if d["rows_total"] >= 100}
        dead = sorted(e for e, d in live.items() if d["rows"] == 0)
        if not dead or not live:
            continue
        # >> ERA-CONFINED is the registry-vocabulary-switch signature, and an
        #    absolute share threshold will NOT catch it. Richmond relabelled
        #    SAT -> SATISFACTION OF MORTGAGE at 2020: the literal-string trigger
        #    fires on 319 rows and misses 8,067, but 319/44,823 = 0.71% clears
        #    any sane vacuity floor. What gives it away is that it fires in one
        #    era band out of ten.
        if len(dead) >= 0.7 * len(live):
            v.append("ERA-CONFINED within %s — fires in only %d of %d populated "
                     "era bands (%s). A trigger this era-bound is usually keyed "
                     "to a label the registry used for part of its history; "
                     "check for a renamed equivalent."
                     % (src, len(live) - len(dead), len(live),
                        ", ".join(e for e in sorted(live) if e not in dead)))
        elif len(dead) < len(live):
            v.append("ERA GAP within %s — never fires in %s (fires elsewhere "
                     "in the same stratum, so this is a date effect, not a "
                     "stratum effect)" % (src, ", ".join(dead)))
    return v


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trigger", action="append", default=[],
                    metavar="NAME:SQL_WHERE")
    ap.add_argument("--file", help="one NAME:SQL_WHERE per line, # comments")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    specs = list(a.trigger)
    if a.file:
        for line in pathlib.Path(a.file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                specs.append(line)
    if not specs:
        sys.exit("no triggers given. --trigger NAME:SQL_WHERE, or --file")

    if not SLATE.exists():
        sys.exit("slate not found at %s" % SLATE)
    c = sqlite3.connect("file:%s?mode=ro" % SLATE, uri=True)
    c.execute("PRAGMA busy_timeout=30000")

    prov = provenance(c)
    results = []
    for s in specs:
        if ":" not in s:
            sys.exit("bad trigger %r — expected NAME:SQL_WHERE" % s)
        name, where = s.split(":", 1)
        results.append(run(c, name.strip(), where.strip()))

    if a.json:
        print(json.dumps({"provenance": prov, "results": results,
                          "verdicts": {r["trigger"]: verdicts(r)
                                       for r in results},
                          "refusal": "no corpus-wide rate is computed; see "
                                     "module docstring"}, indent=2))
        return

    print("R-9 TRIGGER-FREQUENCY AUDIT")
    print("slate: mode=%s per_anchor=%s last_id=%s  (%d rows)"
          % (prov["mode"], prov["per_anchor"], prov["last_id"], prov["total"]))
    print("acris sweep window: %s .. %s" % tuple(prov["acris_window"]))
    print()
    print("NO CORPUS-WIDE RATE IS REPORTED. Two sampling designs share this")
    print("table; inclusion probabilities differ per stratum and are unknown")
    print("for richmond and film. Per-stratum figures only, each labelled with")
    print("what it estimates.")

    for r in results:
        print("\n" + "=" * 74)
        print("%s\n  WHERE %s" % (r["trigger"], r["where"]))
        print("  %-10s %9s %9s %8s   %9s %9s %8s"
              % ("stratum", "rows", "of", "share", "pkgs", "of", "share"))
        for src, s in r["strata"].items():
            print("  %-10s %9d %9d %7.2f%%   %9d %9d %7.2f%%"
                  % (src, s["rows"], s["rows_total"],
                     (s["row_share"] or 0) * 100,
                     s["packages"], s["packages_total"],
                     (s["package_share"] or 0) * 100))
        for src, bands in r["eras"].items():
            shown = ["%s %d/%d" % (e, d["rows"], d["rows_total"])
                     for e, d in bands.items() if d["rows_total"] >= 100]
            # >> suppression must be VISIBLE. A band under the floor is not
            #    tested, and a silently omitted band reads as a band that
            #    passed. ACRIS is the case: its recording dates reach 2025, but
            #    the 2010s hold 20 rows and the 2020s hold 1, so era analysis
            #    there is meaningless — which the reader must be told, not left
            #    to infer from an absent column.
            thin = [(e, d) for e, d in bands.items() if d["rows_total"] < 100]
            if shown:
                print("  eras[%s]: %s" % (src, "  ".join(shown)))
            if thin:
                print("    (%d band%s below the 100-row floor, %d rows total — "
                      "not tested: %s)"
                      % (len(thin), "" if len(thin) == 1 else "s",
                         sum(d["rows_total"] for _, d in thin),
                         ", ".join(e for e, _ in sorted(thin))))
        for v in verdicts(r):
            print("  ** %s" % v)

    print("\n" + "-" * 74)
    print("R-9 LIMIT: frequency catches vacuity and over-capture. It says")
    print("NOTHING about whether a boundary is drawn correctly — a wrong")
    print("classification fires at a perfectly plausible rate. This audit must")
    print("never stand in for boundary testing.")


if __name__ == "__main__":
    main()
