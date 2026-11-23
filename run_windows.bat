@echo off
cd /d "%~dp0"
echo 1 - API dry run, no network traffic
 echo 2 - API real heatmap, may consume credits
 echo 3 - MCP, lists tools and asks before invoking
 echo 4 - Unit tests
set /p CHOICE=Select 1,2,3,4: 
if "%CHOICE%"=="1" py -3 -u main.py --dry-run
if "%CHOICE%"=="2" py -3 -u main.py
if "%CHOICE%"=="3" "%LOCALAPPDATA%\fortyguard-mcp-py313\Scripts\python.exe" -u test_mcp.py
if "%CHOICE%"=="4" py -3 -m unittest discover -s tests -v
pause
