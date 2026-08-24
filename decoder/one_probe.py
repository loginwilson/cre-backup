"""ONE PROBE — the resume protocol's first stair (login 2026-08-24).
Exactly one request: the control check against the known edge crfn.
    live    -> the notice is gone; proceed to the METER test
    refused -> still flagged; return to FULL SILENCE, longer
Never more than this one request, never a retry."""
import json, pathlib, sys
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import acris_edge as AE                                        # noqa: E402

edge = int(json.loads((HERE / "_crfn_edge.json").read_text())["edge"])
try:
    state, did = AE.quick_crfn(edge)
    print("PROBE crfn %d -> %s%s" % (edge, state,
                                     (" (doc %s)" % did) if did else ""))
except Exception as e:
    print("PROBE crfn %d -> %s: %.120s" % (edge, type(e).__name__, e))
