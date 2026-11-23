# Run from this project directory in PowerShell.
# Creates the MCP environment outside OneDrive to avoid file locking.
$ErrorActionPreference = "Stop"
$venv = Join-Path $env:LOCALAPPDATA "fortyguard-mcp-py313"
py -3.13 -m venv $venv
if ($LASTEXITCODE -ne 0) { throw "Install Python 3.13 first." }
& "$venv\Scripts\python.exe" -m pip install --no-cache-dir -r (Join-Path $PSScriptRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Could not install MCP dependencies." }
& "$venv\Scripts\python.exe" -c "import mcp, pydantic_core, httpx2; print('MCP OK')"
