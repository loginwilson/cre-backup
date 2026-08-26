@echo off
rem FLEET GUARD - restart anything in the roster that is not running.
rem
rem WHY THIS EXISTS (2026-08-26): the lanes were being launched as children of
rem a Claude Code session. When Claude crashed at 05:08 the whole process tree
rem went with it and richmond sat dead for hours with nobody watching. A lane
rem that only survives while a chat window is open is not a fleet.
rem
rem Idempotent by construction: `fleet.py start all` skips every process it
rem finds already running (SINGLETON matches on script name) and skips PAUSED
rem lanes, so acris stays paused. Safe to fire every 5 minutes forever.
cd /d "C:\Users\smile\Downloads\Source Folder (Real Estate Data)\Decoder Prompt\decoder"
"C:\Users\smile\AppData\Local\Programs\Python\Python312\python.exe" -u fleet.py start all >> fleet_guard.log 2>&1
