@echo off
title Sistem Pengurusan Unit Kokurikulum SK Sungai Dendang
echo ========================================================
echo SISTEM PENGURUSAN UNIT KOKURIKULUM
echo SEKOLAH KEBANGSAAN SUNGAI DENDANG (ABA6034)
echo ========================================================
echo Memulakan pelayan FastAPI dan membuka pelayar web...
echo.
start http://127.0.0.1:8000
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
