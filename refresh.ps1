# CRE backup refresh - copies the brain (py/md/json) + schema, commits.
# Run any time; safe while lanes run (never touches stores or dbs beyond
# a read-only schema query). One command: powershell -File C:\dev\cre-backup\refresh.ps1
robocopy "C:\Users\smile\Downloads\Source Folder (Real Estate Data)\Decoder Prompt\decoder" "C:\dev\cre-backup\decoder" *.py *.md *.json /S /XD __pycache__ keycache .git /NFL /NDL /NJH /NP | Out-Null
robocopy "D:\CRE Decoding System" "C:\dev\cre-backup\system" *.py *.md *.json /S /XD "By Document" "By Parcel" "By Party" "_incoming" "_archive" ".git" /NFL /NDL /NJH /NP | Out-Null
Set-Location C:\dev\cre-backup
git add -A
git -c user.email="loginwilson88@gmail.com" -c user.name="Login Wilson" commit -m "backup refresh $(Get-Date -Format yyyy-MM-dd_HHmm)"
if (git remote | Select-String origin) { git push origin main }
