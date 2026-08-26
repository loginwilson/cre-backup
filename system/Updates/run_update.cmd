@echo off
rem one pass of the update board - fired by Task Scheduler every 5 minutes
cd /d "D:\CRE Decoding System\Updates"
"C:\Users\smile\AppData\Local\Programs\Python\Python312\python.exe" -u routine_update.py >> update_board.log 2>&1
