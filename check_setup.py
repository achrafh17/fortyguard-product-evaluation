"""Offline environment diagnostics; never displays or sends credentials."""
from pathlib import Path
import sys, os
r = Path(__file__).resolve().parent
p = r / ".env"
print("Python:", sys.version.split()[0])
print("Project folder:", r)
print(".env present:", p.is_file())
print(".env contains a key:", bool(next((line.partition("=")[2].strip() for line in p.read_text(encoding="utf-8-sig").splitlines() if line.startswith("FORTYGUARD_API_KEY=")), "")) if p.exists() else False)
try:
 import mcp, pydantic_core, httpx2
 print("MCP dependencies: OK")
except ImportError:
 print("MCP dependencies: not installed in this Python interpreter (run setup_windows.ps1)")
print("This command does not make an API request.")
