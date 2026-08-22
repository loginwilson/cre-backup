"""THE MATRIX: accuracy x time x scaling, per scan class, measured.

⚠ EVERY TIME HERE IS WALL CLOCK ON 8 CORES OF THIS LAPTOP, so it is converted
to CORE-SECONDS PER PAGE before any corpus projection. Wall clock on one machine
does not transfer; core-seconds does. Tesseract genuinely occupies all 8 cores
(8 OS processes), so wall x 8 is honest for it.

⚠ THAT CONVERSION IS A LIE FOR RAPIDOCR AND THE TABLE SAYS SO. Rapid measured
13.7 s/page at 1 process and 7.1 at 8 - it does NOT use the cores it is given,
so multiplying its wall clock by 8 overstates what it would cost on a bigger
box, while ALSO understating how badly it scales. It is shown separately and
never folded into a projection.

⚠ AND THE TIMINGS CARRY A ~2.5x SPREAD run to run on this machine (same config
measured 0.80 and 1.96 s/page). These are the right ORDER, not a budget. A quiet
dedicated box is needed before anyone commits money to these numbers.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CORES = 8

# class -> (share of corpus PAGES, tesseract psm4 s/page, best extra pass s/page,
#           rapidocr s/page @8proc, accuracy at each stage)
CLASSES = {
    "book  BK_": dict(share=0.040, t4=0.48, extra=0.19, rapid=9.63,
                      acc_t4=0.69, acc_extra=0.92, acc_rapid=0.98,
                      extra_name="rot 90/270"),
    "film  FT_": dict(share=0.255, t4=0.72, extra=0.41, rapid=7.14,
                      acc_t4=0.80, acc_extra=0.97, acc_rapid=0.99,
                      extra_name="psm 11"),
    "digital  ": dict(share=0.705, t4=0.21, extra=0.41, rapid=3.94,
                      acc_t4=0.95, acc_extra=0.98, acc_rapid=1.00,
                      extra_name="psm11+rot"),
}
PAGES = 148_238_970

print("  ══ ACCURACY x TIME, per scan class (CRITICAL-tier pointing) ══\n")
print(f"  {'class':<11}{'share':>7}{'  T psm4':>10}{'':>6}{'+ extra pass':>15}{'':>6}"
      f"{'+ RapidOCR':>13}{'':>6}")
print(f"  {'':<11}{'':>7}{'acc':>6}{'s/pg':>8}{'acc':>7}{'s/pg':>8}{'acc':>9}{'s/pg':>8}")
print("  " + "-" * 74)
for k, v in CLASSES.items():
    print(f"  {k:<11}{v['share']*100:>6.1f}%"
          f"{v['acc_t4']*100:>6.0f}%{v['t4']:>8.2f}"
          f"{v['acc_extra']*100:>7.0f}%{v['t4']+v['extra']:>8.2f}"
          f"{v['acc_rapid']*100:>9.0f}%{v['t4']+v['extra']+v['rapid']:>8.2f}")

print("\n  ══ CORE-SECONDS PER PAGE (hardware-independent) ══\n")
print(f"  {'class':<11}{'T psm4':>9}{'+extra':>9}{'  RapidOCR (does not scale)':>30}")
for k, v in CLASSES.items():
    print(f"  {k:<11}{v['t4']*CORES:>9.1f}{(v['t4']+v['extra'])*CORES:>9.1f}"
          f"{v['rapid']*CORES:>16.0f}  <- see caveat")

# ── blended corpus projections, Tesseract only (the part that scales) ──
def project(label, per_class_secs, acc):
    blend = sum(CLASSES[k]["share"] * per_class_secs[k] * CORES for k in CLASSES)
    a = sum(CLASSES[k]["share"] * acc[k] for k in CLASSES)
    total_core_h = blend * PAGES / 3600
    print(f"\n  {label}")
    print(f"    blended {blend:>6.2f} core-s/page   ·   blended accuracy {a*100:>4.1f}%")
    print(f"    {total_core_h:>12,.0f} core-hours for {PAGES/1e6:.1f}M pages")
    for cores in (32, 64, 128):
        sh = total_core_h / cores
        print(f"      {cores:>3}-core box: {sh:>8,.0f} box-hours  ->  "
              f"{sh/720:>5.1f} boxes for 30 days   |   {sh/(720*3):>4.1f} for 90 days")

print("\n  ══ CORPUS PROJECTIONS (Tesseract only - the tier that scales) ══")
project("A. psm4 everywhere",
        {k: v["t4"] for k, v in CLASSES.items()},
        {k: v["acc_t4"] for k, v in CLASSES.items()})
project("B. psm4 + class-specific extra pass on FILM and BOOK only",
        {"book  BK_": CLASSES["book  BK_"]["t4"] + CLASSES["book  BK_"]["extra"],
         "film  FT_": CLASSES["film  FT_"]["t4"] + CLASSES["film  FT_"]["extra"],
         "digital  ": CLASSES["digital  "]["t4"]},
        {"book  BK_": 0.92, "film  FT_": 0.97, "digital  ": 0.95})
project("C. psm4 + extra pass everywhere",
        {k: v["t4"] + v["extra"] for k, v in CLASSES.items()},
        {k: v["acc_extra"] for k, v in CLASSES.items()})

print("\n  ⚠ RapidOCR is deliberately absent from every projection. It does not")
print("    scale with cores (13.7 s/page at 1 process, 7.1 at 8), so it belongs")
print("    only on the residue the trigger escalates - a small slice whose")
print("    volume has NOT yet been measured on a real sample.")
