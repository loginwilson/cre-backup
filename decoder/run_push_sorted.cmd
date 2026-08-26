@echo off
REM Push the REMAINING rows, SORTED BY document_id.
REM
REM Measured 2026-08-13 on the same endpoint, same instance, same IO budget:
REM     scattered key order   0 of 2,000 rows landed - every batch timed out
REM     sorted key order      2,500 rows in 0.70s = 3,555 rows/s
REM The map file is in ACRIS's arbitrary order, so every insert hit a RANDOM
REM B-tree page: random disk IO, page splits, and the IO budget spent on
REM seeking. Sorted, inserts append near-sequentially and the same index pages
REM stay in cache. Nothing else changed.
cd /d "%~dp0"
set ACRIS_MAPS=%~dp0_remaining_sorted.jsonl
if exist "_push_selection_DONE" del "_push_selection_DONE"
:retry
python -u push_selection.py --batch 2500 --conc 2 >> _push_sorted.log 2>&1
if exist "_push_selection_DONE" goto done
echo [wrapper] no completion marker - resuming in 20s >> _push_sorted.log
timeout /t 20 /nobreak > nul
goto retry
:done
echo [wrapper] COMPLETED - marker present >> _push_sorted.log
