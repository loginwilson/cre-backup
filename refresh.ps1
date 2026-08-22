# CRE backup refresh - banks the brain: py/md/json from both roots + the db
# schema/triggers, commits, pushes. Called nightly by routine_synchronization
# (guarded there); safe to run by hand any time. Never touches stores/lanes.
robocopy "C:\Users\smile\Downloads\Source Folder (Real Estate Data)\Decoder Prompt\decoder" "C:\dev\cre-backup\decoder" *.py *.md *.json /S /XD __pycache__ keycache .git /NFL /NDL /NJH /NP | Out-Null
robocopy "D:\CRE Decoding System" "C:\dev\cre-backup\system" *.py *.md *.json /S /XD "By Document" "By Parcel" "By Party" "_incoming" "_archive" ".git" /NFL /NDL /NJH /NP | Out-Null
# schema + triggers = the PROCESS inside the db; re-exported every run
& "C:\Users\smile\AppData\Local\Programs\Python\Python312\python.exe" -c "import sqlite3,pathlib;con=sqlite3.connect(r'file:D:/CRE Decoding System/Legal Instruments.db?mode=ro',uri=True,timeout=60);rows=con.execute('SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type DESC,name').fetchall();pathlib.Path(r'C:/dev/cre-backup/system/schema_legal_instruments.sql').write_text('\n\n'.join(f'-- {t}: {n}\n{s};' for t,n,s in rows),encoding='utf-8')"
Set-Location C:\dev\cre-backup
git add -A
$staged = git diff --cached --name-only
if ($staged) {
  git -c user.email="loginwilson88@gmail.com" -c user.name="Login Wilson" commit -q -m "backup refresh $(Get-Date -Format yyyy-MM-dd_HHmm)"
  git push -q origin main
  "refreshed + pushed: $(($staged | Measure-Object).Count) file(s) changed"
} else {
  "refreshed: no changes since last bank"
}
