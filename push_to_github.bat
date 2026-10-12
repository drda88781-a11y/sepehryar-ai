@echo off
cd /d "%~dp0"
echo ===================================================
echo Pushing Sepehryar AI to GitHub...
echo ===================================================
git config --global --add safe.directory "*"
git push -u origin main
echo.
echo ===================================================
echo Done! Code pushed successfully.
echo ===================================================
pause
