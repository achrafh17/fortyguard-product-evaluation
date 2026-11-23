# FortyGuard Product Evaluation — API, MCP and Dashboard

**Independent technical evaluation for a Software Development Internship (PFE 2027).** Not an official FortyGuard SDK.

This project contains a runnable Python REST API client, a runnable MCP client, reproducible tests, screenshots from the real dashboard walkthrough, sanitized results, and a 17-page evaluation PDF.

## What was actually tested

| Product | Verified outcome |
|---|---|
| Temperature API | `POST /v1/heatmap` HTTP 200 for Phoenix, followed by 6 GET polls until `completed`; GeoJSON and summary statistics received |
| Temperature MCP | Streamable HTTP with Bearer authentication; 11 tools discovered; `env_params` returned hourly environmental parameters |
| Temperature Dashboard | Fresno County (California) heatmap successfully generated and displayed; user inspected a cell with temperature **91.87 °F** and coordinates |

### Screenshots and analysis

- [Evaluation report (PDF)](docs/FortyGuard_Product_Evaluation_Report.pdf) — detailed findings and evidence.
- [Full screenshot gallery](evidence/screenshots/) — redacted registration, email, mapping, account coverage, map, and inspection screenshots.
- [Verified API summary](evidence/results/api_heatmap_summary.json) and [MCP summary](evidence/results/mcp_env_params_summary.json).

![Completed map](evidence/screenshots/image(20261123-002636).jpg)

The provider email screenshot has credentials and personal email address **redacted**. Do not publish a secret or a raw API response.

## Project contents

```text
main.py                 REST Heatmap API client; HTTP POST + status polling
 test_mcp.py             MCP Streamable HTTP client; tool discovery + env_params
 check_setup.py          Offline environment diagnostic
 setup_windows.ps1       Optional Python 3.13 virtual environment setup
 run_windows.bat         Interactive Windows quick-start menu
 tests/test_main.py      Unit tests
 requirements.txt        MCP dependencies only
 .env.example            Versioned template without credentials
 .env                    LOCAL ONLY; paste API key here (Git-ignored)
 docs/                   Public PDF evaluation report
 evidence/screenshots/   19 redacted product-evaluation screenshots
 evidence/results/       Sanitized successful-response summaries
 results/                LOCAL ONLY; saved raw API/MCP output (Git-ignored)
 private/                LOCAL ONLY; full-resolution report (Git-ignored)
```

## 1. Set your API key in `.env` (required)

The **private** `.env` file is not included in the public ZIP. Create one from `.env.example`:

```dotenv
FORTYGUARD_API_KEY=PASTE_YOUR_REAL_KEY_HERE
```

Copy `.env.example` to `.env` and replace the placeholder with **your real FortyGuard API key**, save the file, and keep it private. **No actual credential is embedded in this project**, even in the private download. The API client prefers this `.env` key over a stale shell variable; the MCP client also reloads it.

Do **not** add `.env` to Git. For public clones, copy `.env.example` to `.env` first.

## 2. REST API quick start (Python 3.13 or 3.14)

Standard library only; no dependencies or virtual environment required.

```powershell
py -3 -u check_setup.py
py -3 -u main.py --dry-run
```

`--dry-run` makes **zero network requests**. After setting the key in `.env`, to submit a real Heatmap request:

```powershell
py -3 -u main.py
```

The script prompts before sending a potentially billable POST. The successful test area is a polygon near **Phoenix, AZ** on `2024-07-15` at `14:00`, `100 m` granularity. Availability can vary by region and date. Responses are stored in `results/last_submission.json` and `results/last_status.json`. To query a previous job without consuming credits on another POST:

```powershell
py -3 -u main.py --activity-id YOUR_EXISTING_ID
```

## 3. MCP quick start (Python 3.13 on Windows)

To avoid the Python 3.14 `pydantic_core` DLL error and OneDrive pip file locking observed during the evaluation, install dependencies in an environment outside OneDrive:

```powershell
$venv = "$env:LOCALAPPDATA\fortyguard-mcp-py313"
py -3.13 -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --no-cache-dir -r requirements.txt
& "$venv\Scripts\python.exe" -u test_mcp.py
```

Or run `setup_windows.ps1` and then use option `3` from `run_windows.bat`.

The client will:

1. Read `FORTYGUARD_API_KEY` from `.env`.
2. Connect to `https://tos-mcp.app.fortyguard.com/mcp` with a Bearer token.
3. Discover tools and show the real `env_params` JSON input schema.
4. Ask before making a potentially credit-consuming request to Phoenix.
5. Save the full response locally to `results/mcp_env_params.json` (ignored by Git).

## 4. Automated tests

```powershell
py -3 -m unittest discover -s tests -v
```

## Assessment and improvement opportunities

The product experience was **strong, coherent, modern and aligned with useful UI/UX principles**. API-key delivery by email was quick. Temperature Dashboard data is intuitive to explore. REST output was structured and its asynchronous task workflow was easy to understand. MCP exposed AI-compatible structured environmental capabilities.

Constructive recommendations: improve regional coverage and subscribed-state explanations; provide validated sample polygons and a preflight coverage-check endpoint; improve credit transparency and feedback on processing; keep MCP documentation aligned with live capabilities (11 tools observed vs 9 advertised); improve heatmap legends and data export affordances.

## Security warning

`.env`, `results/`, `private/`, Python environments and local logs are ignored by `.gitignore`. Always run `git status` **before pushing** to GitHub. Only the pre-redacted screenshots, sanitized summaries and report in `docs/` are intended for public distribution. Never publish your real key.
