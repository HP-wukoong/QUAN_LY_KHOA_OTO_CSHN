@echo off
chcp 65001 >nul
title QUAN LY KHOA O TO CSHN - MAY CHU (dung tat cua so nay khi dang dung tool)
cd /d "%~dp0"
set "PY="
where py >nul 2>nul && py -3.11 -c "import sys" >nul 2>nul && set "PY=py -3.11"
if not defined PY ( where py >nul 2>nul && py -3 -c "import sys" >nul 2>nul && set "PY=py -3" )
if not defined PY ( where python >nul 2>nul && python -c "import sys" >nul 2>nul && set "PY=python" )
if not defined PY (
  echo.
  echo  KHONG TIM THAY PYTHON. Hay cai Python 3.11 tu python.org ^(tick "Add python.exe to PATH"^).
  echo.
  pause
  exit /b 1
)
%PY% server.py
if errorlevel 1 (
  echo.
  echo  May chu dung do loi. Xem file data\server.log
  pause
)
