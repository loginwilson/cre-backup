# CRE backup refresh - banks the brain: py/md/json/cmd from both roots + the db
# (*.cmd added 2026-08-26: fleet_guard.cmd and run_update.cmd ARE process - a
#  launcher that is not banked is a lane nobody can restart after a rebuild.)
# schema/triggers, commits, pushes. Called nightly by routine_synchronization
# (guarded there); safe to run by hand any time. Never touches stores/lanes.
robocopy "C:\Users\smile\Downloads\Source Folder (Real Estate Data)\Decoder Prompt\decoder" "C:\dev\cre-backup\decoder" *.py *.md *.json *.cmd /S /XD __pycache__ keycache .git /NFL /NDL /NJH /NP | Out-Null
robocopy "D:\CRE Decoding System" "C:\dev\cre-backup\system" *.py *.md *.json *.cmd /S /XD "By Document" "By Parcel" "By Party" "_incoming" "_archive" ".git" /NFL /NDL /NJH /NP | Out-Null
robocopy "C:\Users\smile\.claude\skills" "C:\dev\cre-backup\skills" *.md /S /NFL /NDL /NJH /NP | Out-Null
# assistant memory: pointers + working preferences. NOT the system record
# (that is D:\...\Bootcamp\*.md) but cheap to bank and it sits on the same
# drive that everything else here exists to survive.
robocopy "C:\Users\smile\.claude\projects\C--Users-smile\memory" "C:\dev\cre-backup\memory" *.md /S /NFL /NDL /NJH /NP | Out-Null
# schema + triggers = the PROCESS inside the db; re-exported every run
& "C:\Users\smile\AppData\Local\Programs\Python\Python312\python.exe" -c "import sqlite3,pathlib;con=sqlite3.connect(r'file:D:/CRE Decoding System/Legal Instruments.db?mode=ro',uri=True,timeout=60);rows=con.execute('SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type DESC,name').fetchall();pathlib.Path(r'C:/dev/cre-backup/system/schema_legal_instruments.sql').write_text('\n\n'.join(f'-- {t}: {n}\n{s};' for t,n,s in rows),encoding='utf-8')"
Set-Location C:\dev\cre-backup
git add -A
$staged = git diff --cached --name-only
if ($staged) {
  git -c user.email="loginwilson88@gmail.com" -c user.name="Login Wilson" commit -q -m "backup refresh $(Get-Date -Format yyyy-MM-dd_HHmm)"
  $n = ($staged | Measure-Object).Count
  # ⚠ THIS SAID "pushed" WHETHER OR NOT IT PUSHED. Caught 2026-08-23 01:38:
  # `Could not resolve host: github.com` went to stderr, the script carried on
  # and printed "refreshed + pushed: 3 file(s) changed". The commit was local
  # only, and the one line anybody reads said it was banked.
  #
  # That is the same shape as every other defect found tonight - a failure that
  # renders as success because nothing checked the negative branch. It matters
  # more here than anywhere else: this script IS the thing that stops work being
  # lost, and login's instruction was explicit - "even the back up repo. I dont
  # want to lose the code."
  #
  # One retry, because the observed failure was transient DNS, then TELL THE
  # TRUTH either way and exit non-zero so a caller can see it.
  git push -q origin main 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Start-Sleep -Seconds 5
    git push -q origin main 2>&1 | Out-Null
  }
  if ($LASTEXITCODE -ne 0) {
    $behind = (git log origin/main..HEAD --oneline | Measure-Object).Count
    "COMMITTED LOCALLY BUT **PUSH FAILED**: $n file(s) changed, $behind commit(s) unpushed."
    "  The work is committed at $(git rev-parse --short HEAD) and is NOT on the remote."
    "  Re-run this script, or: git -C C:\dev\cre-backup push origin main"
    exit 1
  }
  "refreshed + pushed: $n file(s) changed  (remote $(git rev-parse --short origin/main))"
} else {
  "refreshed: no changes since last bank"
}
