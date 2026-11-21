@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto run
echo Chua cai dat. Hay chay 1_CAI_DAT.bat truoc.
pause
exit /b 1

:run
rem Model DINO tai tu muc Releases: dat file .safetensors vao thu muc models, file nay tu xep vao dung cho
if exist "models\dino_chi_xa_lach.safetensors" move /y "models\dino_chi_xa_lach.safetensors" "models\dino_chi_xa_lach\model.safetensors" >nul
if exist "models\dino_xa_lach_co_dai.safetensors" move /y "models\dino_xa_lach_co_dai.safetensors" "models\dino_xa_lach_co_dai\model.safetensors" >nul
if not exist "models\dino_chi_xa_lach\model.safetensors" echo [!] Chua co model DINO chi xa lach - xem README, muc Tai model DINO. YOLO van dung duoc.
if not exist "models\dino_xa_lach_co_dai\model.safetensors" echo [!] Chua co model DINO xa lach + co dai - xem README, muc Tai model DINO.
echo Dang khoi dong server nhan dien... trinh duyet se tu mo sau vai giay.
echo De TAT: dong cua so nay.
start "" /min cmd /c "timeout /t 8 /nobreak >nul & start "" http://127.0.0.1:8001/"
".venv\Scripts\python.exe" server\detect_server.py %*
pause
