@echo off
REM Jalankan backend RTConnect yang terhubung ke Supabase.
REM Butuh: Python 3.10+ dan backend\.env berisi kredensial Supabase.
cd /d "%~dp0backend"

echo === [1/3] Install library Python ===
python -m pip install -r requirements.txt
if errorlevel 1 goto gagal

echo.
echo === [2/3] Hubungkan ke Supabase (koneksi, migrasi, data awal, bucket) ===
python setup_supabase.py
if errorlevel 1 goto gagal

echo.
echo === [3/3] Menjalankan backend di http://localhost:5000 ===
echo Biarkan jendela ini tetap terbuka selama aplikasi dipakai.
python app.py
goto selesai

:gagal
echo.
echo [X] Ada langkah yang gagal. Baca pesan error di atas.

:selesai
pause
