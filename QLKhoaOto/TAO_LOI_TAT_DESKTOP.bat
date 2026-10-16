@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Quan ly khoa o to.lnk'); $s.TargetPath='%~dp0CHAY_TOOL.bat'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='shell32.dll,43'; $s.WindowStyle=7; $s.Save()"
echo Da tao loi tat "Quan ly khoa o to" tren Desktop.
pause
