"""FortyGuard API evaluation, standard-library version. Python 3.10+, no pip required.

The default AOI is a Phoenix polygon that succeeded in the recorded evaluation.
Coverage can vary over time by area, service, and date.
The script never sends requests in --dry-run mode.
"""
from __future__ import annotations
import argparse
from datetime import datetime
from getpass import getpass
import json
import os
from pathlib import Path
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://api.fortyguard.com/v1"
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def payload(date: str, hour: str, granularity: int) -> dict[str, Any]:
    return {
        "polygon_aoi": {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature", "properties": {},
                "geometry": {"type": "Polygon", "coordinates": [[
                    [-112.095, 33.470], [-112.080, 33.470],
                    [-112.080, 33.479], [-112.095, 33.479],
                    [-112.095, 33.470],
                ]]},
            }],
        },
        "date_time": {"start_date": date, "start_time": hour, "filter_type": 1},
        "granularity": granularity,
    }


def extract(data: dict[str, Any], key: str) -> str:
    block = data.get("data")
    value = block.get(key) if isinstance(block, dict) else None
    if not isinstance(value, (str, int)) or not str(value).strip():
        raise ValueError(f"Missing data.{key}: {str(data)[:400]}")
    return str(value).strip()


def save(filename: str, data: dict[str, Any]) -> None:
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / filename).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_key() -> str:
    """Read the private project .env first, then fall back to shell environment.

    The key is never echoed. An empty .env value is not a usable credential.
    """
    key = ""
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            if line.strip().startswith("FORTYGUARD_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not key:
        key = os.environ.get("FORTYGUARD_API_KEY", "").strip()
    if key == "REPLACE_WITH_YOUR_API_KEY":
        key = ""
    if not key:
        raise ValueError("Missing FortyGuard API key; paste it in the private .env file.")
    return key


def request_json(method: str, path: str, key: str, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = Request(BASE + path, data=data, method=method)
    req.add_header("api-key", key)
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=35) as resp:
            status, raw = resp.status, resp.read().decode("utf-8", "replace")
    except HTTPError as exc:
        status, raw = exc.code, exc.read().decode("utf-8", "replace")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"HTTP {status} response is not JSON: {raw[:350]}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected JSON object; got: {type(parsed).__name__}")
    return status, parsed


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FortyGuard heatmap API evaluation")
    p.add_argument("--dry-run", action="store_true", help="Show request only; no API key or credits used")
    p.add_argument("--yes", action="store_true", help="Skip credit-use confirmation")
    p.add_argument("--activity-id", help="Poll previously submitted task (avoid repeating POST)")
    p.add_argument("--start-date", default="2024-07-15")
    p.add_argument("--start-time", default="14:00")
    p.add_argument("--granularity", type=int, default=100)
    p.add_argument("--max-polls", type=int, default=24)
    p.add_argument("--poll-interval", type=float, default=5.0)
    return p


def main() -> int:
    args = make_parser().parse_args()
    try:
        datetime.strptime(args.start_date, "%Y-%m-%d")
        datetime.strptime(args.start_time, "%H:%M")
    except ValueError as exc:
        print(f"Invalid date/time: {exc}", file=sys.stderr)
        return 2
    if args.granularity <= 0 or args.max_polls <= 0 or args.poll_interval < 0:
        print("granularity, max-polls must be positive; poll-interval >= 0", file=sys.stderr)
        return 2

    body = payload(args.start_date, args.start_time, args.granularity)
    if args.dry_run:
        print("DRY RUN - no network request, no credits used.", flush=True)
        print(f"POST {BASE}/heatmap", flush=True)
        print("Headers: api-key: [HIDDEN], Content-Type: application/json", flush=True)
        print(json.dumps(body, indent=2, ensure_ascii=False), flush=True)
        print(f"Then GET {BASE}/status/{{activity_id}}", flush=True)
        return 0

    if not args.activity_id and not args.yes:
        print("WARNING: POST can consume FortyGuard API credits.", flush=True)
        if input("Submit heatmap request? [y/N]: ").strip().lower() not in {"y", "yes", "o", "oui"}:
            print("Cancelled.")
            return 0

    try:
        key = get_key()
        if args.activity_id:
            task = args.activity_id
            print("Checking existing task:", task, flush=True)
        else:
            print("Sending POST /v1/heatmap ...", flush=True)
            code, result = request_json("POST", "/heatmap", key, body)
            print("POST HTTP", code, flush=True)
            save("last_submission.json", result)
            if not 200 <= code < 300:
                print("API error:", json.dumps(result, ensure_ascii=False)[:1200], file=sys.stderr)
                return 1
            task = extract(result, "activity_id")
            print("activity_id:", task, flush=True)
            print("Saved: results/last_submission.json", flush=True)

        for i in range(args.max_polls):
            code, result = request_json("GET", "/status/" + task, key)
            print(f"Poll {i+1}/{args.max_polls} - HTTP {code}", flush=True)
            if code == 404 and i < 3:
                print("Task not available yet; retrying.", flush=True)
            elif code < 200 or code >= 300:
                print("API error:", json.dumps(result, ensure_ascii=False)[:1200], file=sys.stderr)
                return 1
            else:
                save("last_status.json", result)
                status = extract(result, "status").lower()
                print("Status:", status, flush=True)
                if status in {"completed", "succeeded"}:
                    print("DONE. See results/last_status.json", flush=True)
                    return 0
                if status in {"failed", "error"}:
                    print("Task failed; see results/last_status.json", file=sys.stderr)
                    return 1
            if i + 1 < args.max_polls:
                time.sleep(args.poll_interval)
        print("Still processing. Recheck using --activity-id " + task, flush=True)
        return 2
    except (ValueError, HTTPError, URLError, OSError, TimeoutError, EOFError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    print("Starting FortyGuard evaluation...", flush=True)
    raise SystemExit(main())
