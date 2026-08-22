import pathlib, re
NEW = '''
 C("c2013-plane-RESOLVED", "2013052101674002", "p010", "easement",
   subject="1008000020", num=130.0, unit="ft",
   text="RESOLVED BY LOOKING AT THE PAGE. Lot 20 heading, then: 'ALL that "
        "portion of the below described parcel LYING BELOW AN UPPER LIMITING "
        "PLANE drawn at an elevation of 130 feet above the datum level used "
        "by the topographical bureau, Borough of Manhattan, which is 2.78 "
        "feet above National Geodetic Survey vertical datum 1929 (United "
        "Coast and Geodetic Survey), mean sea level Sandy Hook, New Jersey.' "
        "LOT 49 TOOK THE DEVELOPMENT RIGHTS OF THE PORTION OF LOT 20 BELOW "
        "130 FEET",
   eff="2013-05-17", vto=130.0,
   vdatum="Topographical Bureau, Borough of Manhattan = NGVD 1929 + 2.78 ft",
   hext="lot 20 footprint: 125 ft on West 24th Street beginning 425 ft "
        "westerly of Sixth Avenue, 116 ft 5 in deep",
   ans=["ENVELOPE", "ENCUMBRANCE"],
   note="⚠ I ASSERTED THE OPPOSITE. I wrote that lot 49 'owns air ABOVE an "
        "elevation'. It is BELOW. 130 feet is the UPPER limit of the volume "
        "conveyed, and the three instruments never disagreed - the 2019 "
        "Lower Parcel / Air Space split says the same thing from the other "
        "side, and the 2012 mortgage's bare '(lower limiting plane)' is a "
        "shorthand parenthetical in an exhibit. ⚠ AND THE CITE WAS WRONG: "
        "the agent reported p009, which is Lot 56's metes and bounds. The "
        "quote was accurate and the page was off by one - a discrepancy no "
        "amount of re-reading my notes could surface, because my notes were "
        "the thing in doubt. PROOF CROP proofs/9534509cfd4986d7.png, 16.7 KB, "
        "cut wide enough to include the 'Lot 20' heading so the plane cannot "
        "be misattributed to another lot"),
'''
p = pathlib.Path("claims.py"); t = p.read_text(encoding="utf-8")
m = re.search(r"^ # ---- 2014.*$", t, re.M)
t = t.replace(m.group(0), NEW + m.group(0), 1)
p.write_text(t, encoding="utf-8")
print("recorded the resolution")
