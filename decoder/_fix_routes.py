"""⚠ THE ROUTE IS NOW DECLARED, NOT GUESSED FROM MY OWN PROSE.

I wrote a classifier that keyword-matched the detail text to decide what would
close an open item. It mis-routed the air-rights question because the detail
says "NOT ONE ZLDA IS IN THE CORPUS" and the pattern looked for "NOT IN THE
CORPUS".

That is the SAME defect as the function-tag drift I fixed two hours ago:
meaning inferred from free text instead of carried as a field. I rebuilt it
from scratch without noticing. Recording the mechanism, not just the fix.
"""
import pathlib

ROUTES = {
 "the interest rate, at any point in 35 years": "OTHER_SOURCE",
 "how Chelsea 25 Hotel LLC acquired the fee": "FETCH",
 "what the air rights cost": "FETCH",
 "whether Marriott's ROFR sits ahead of or behind the lien": "UNRECORDED",
 "what the hotel earns": "OTHER_SOURCE",
 "when, and to what plan": "OTHER_SOURCE",
}
LABEL = {
 "FETCH":        "A FETCH — the instrument exists and I do not hold it",
 "OTHER_SOURCE": "ANOTHER SOURCE — DOF, DOB. Not an ACRIS gap at all",
 "UNRECORDED":   "⚠ NOTHING. The term was deliberately kept off the record",
 "READ":         "reading a page already on disk",
}

OLD_START = '            d = detail.upper()'
OLD_END = '            print(f"        -> {route}")'
NEW = '''            # ⚠ DECLARED, NOT INFERRED. See _fix_routes.py for why.
            route = LABEL.get(ROUTES.get(q, "READ"), LABEL["READ"])
            print(f"    [{fn}] {q}")
            print(f"        -> {route}")'''


def main():
    p = pathlib.Path("closure.py")
    t = p.read_text(encoding="utf-8")
    i, j = t.index(OLD_START), t.index(OLD_END) + len(OLD_END)
    t = t[:i] + NEW + t[j:]
    t = t.replace('    fetchable = sum(1 for qs in QUESTIONS.values() '
                  'for q, s, d in qs\n'
                  '                    if s == OPEN and ("NEVER PULLED" '
                  'in d.upper()\n'
                  '                                      or "NOT IN THE '
                  'CORPUS" in d.upper()))',
                  '    fetchable = sum(1 for qs in QUESTIONS.values() '
                  'for q, s, d in qs\n'
                  '                    if s == OPEN '
                  'and ROUTES.get(q) == "FETCH")')
    t = t.replace("import claims as K",
                  "import claims as K\nfrom _fix_routes import ROUTES, LABEL")
    p.write_text(t, encoding="utf-8")
    print("routes are declared now")


if __name__ == "__main__":
    main()
