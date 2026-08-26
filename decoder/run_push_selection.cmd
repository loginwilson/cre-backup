@echo off
REM Resume the selection push until it GENUINELY completes.
REM
REM (1) NOT "errorlevel". A Ctrl+C kill exits 0xC000013A, which cmd compares as
REM     a NEGATIVE number, so "if errorlevel 1" was FALSE and a KILLED run
REM     printed "push completed cleanly" with 2.7M rows unsent. Completion is a
REM     POSITIVE signal: push_selection.py writes _push_selection_DONE only
REM     after its read loop reaches end of file.
REM
REM (2) "python -u". Python BLOCK-buffers stdout when redirected to a file, so a
REM     healthy run looked DEAD for 8 minutes while its checkpoint advanced the
REM     whole time. To answer "is it alive", read _push_selection_state.json,
REM     not this log.
REM
REM (3) batch 500 x conc 2 is MEASURED, not chosen: on genuinely new rows
REM     against the depleted instance, 500 succeeded in 0.72s and 1,000 timed
REM     out. ASCII ONLY IN THIS FILE - a patch script that wrote a unicode
REM     comment here raised UnicodeEncodeError AFTER truncating the file, left
REM     it at 0 bytes, and reported success.
cd /d "%~dp0"
if exist "_push_selection_DONE" del "_push_selection_DONE"
:retry
python -u push_selection.py --batch 500 --conc 2 >> _push_selection_run.log 2>&1
if exist "_push_selection_DONE" goto done
echo [wrapper] no completion marker - resuming in 30s >> _push_selection_run.log
timeout /t 30 /nobreak > nul
goto retry
:done
echo [wrapper] COMPLETED - marker present >> _push_selection_run.log
