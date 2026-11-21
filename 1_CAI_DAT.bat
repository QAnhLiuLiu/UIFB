@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo   CAI DAT MOI TRUONG CHO FARMBOT UI  - chi can chay 1 lan
echo ============================================================
echo.

rem ---- 1. Tim Python 3.14 ----
set "PY="
py -3.14 -c "import sys" >nul 2>&1
if %errorlevel%==0 set "PY=py -3.14"
if defined PY goto havepy
python -c "import sys; sys.exit(0 if sys.version_info[:2]==(3,14) else 1)" >nul 2>&1
if %errorlevel%==0 set "PY=python"
if defined PY goto havepy
echo [LOI] Chua co Python 3.14.
echo   Tai tai: https://www.python.org/downloads/
echo   Khi cai nho tick o "Add python.exe to PATH", cai xong chay lai file nay.
pause
exit /b 1

:havepy
echo Dung Python: %PY%

rem ---- 2. Tao moi truong rieng .venv ----
if exist ".venv\Scripts\python.exe" goto venvok
%PY% -m venv .venv
if errorlevel 1 goto fail
:venvok
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto fail

rem ---- 3. PyTorch: ban CUDA neu co GPU NVIDIA, ban CPU neu khong ----
set "TORCH_URL=https://download.pytorch.org/whl/cpu"
where nvidia-smi >nul 2>&1
if %errorlevel%==0 set "TORCH_URL=https://download.pytorch.org/whl/cu126"
if "%TORCH_URL%"=="https://download.pytorch.org/whl/cu126" echo Thay GPU NVIDIA: cai PyTorch ban CUDA 12.6, khoang 2.5 GB, hoi lau...
if "%TORCH_URL%"=="https://download.pytorch.org/whl/cpu" echo Khong thay GPU NVIDIA: cai PyTorch ban CPU. YOLO dung duoc, DINO se rat cham.
".venv\Scripts\python.exe" -m pip install torch==2.14.1 torchvision==0.29.1 --index-url %TORCH_URL%
if errorlevel 1 goto fail

rem ---- 4. Cac thu vien con lai ----
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail

rem ---- 5. Kiem tra ----
".venv\Scripts\python.exe" -c "import torch, transformers, ultralytics, fastapi, cv2; print('OK - torch', torch.__version__, '- GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'khong (chay CPU)')"
if errorlevel 1 goto fail
echo.
echo ===== CAI DAT XONG. Bay gio mo 2_CHAY.bat =====
pause
exit /b 0

:fail
echo.
echo [LOI] Cai dat bi loi o buoc tren. Kiem tra ket noi mang roi chay lai file nay.
pause
exit /b 1
