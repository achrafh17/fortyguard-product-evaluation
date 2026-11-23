"""Explore the FortyGuard remote MCP server and optionally query env_params.

Uses the official Streamable HTTP transport. Reads credentials from .env.
No MCP tool is invoked without interactive confirmation.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import httpx2
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
MCP_URL = "https://tos-mcp.app.fortyguard.com/mcp"

ENV_PARAMS_ARGUMENTS = {
    "latitude": 33.4484,
    "longitude": -112.074,
    "temperature": 35,
    "date_time": {
        "start_date": "2025-09-20",
        "filter_type": 3,  # one calendar day
    },
    "analysis": [
        "heat_index_celsius",
        "apparent_temperature_celsius",
        "relative_humidity_percent",
        "aqi_us",
    ],
}


async def main() -> None:
    load_dotenv(BASE_DIR / ".env", override=True)
    api_key = os.getenv("FORTYGUARD_API_KEY", "").strip()
    if not api_key or api_key == "REPLACE_WITH_YOUR_API_KEY":
        print("ERROR: Configure FORTYGUARD_API_KEY in .env or your environment.")
        return

    print("Starting FortyGuard MCP evaluation...")
    print("Connecting to FortyGuard MCP...")
    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx2.AsyncClient(
        headers=headers,
        timeout=httpx2.Timeout(30, read=300),
    ) as client:
        async with streamable_http_client(
            MCP_URL, http_client=client
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("MCP connection successful!")

                response = await session.list_tools()
                print(f"\nDiscovered {len(response.tools)} tools:")
                for tool in response.tools:
                    print(f" - {tool.name}")

                env_tool = next(
                    (tool for tool in response.tools if tool.name == "env_params"),
                    None,
                )
                if env_tool is None:
                    print("ERROR: env_params not available on this server.")
                    return
                print("\nenv_params input schema:")
                print(json.dumps(env_tool.input_schema, indent=2))

                print("\nProposed env_params arguments:")
                print(json.dumps(ENV_PARAMS_ARGUMENTS, indent=2))
                print("\nWARNING: An env_params call may consume API credits.")
                confirm = input("Call env_params? [y/N]: ").strip().lower()
                if confirm != "y":
                    print("Request cancelled; tool catalog was still verified.")
                    return

                result = await session.call_tool(
                    "env_params", arguments=ENV_PARAMS_ARGUMENTS
                )
                data = result.model_dump(mode="json")
                RESULTS_DIR.mkdir(parents=True, exist_ok=True)
                destination = RESULTS_DIR / "mcp_env_params.json"
                destination.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

                # The MCP server can return structured results in addition to text.
                structured = data.get("structured_content")
                if isinstance(structured, dict):
                    summary = structured.get("result", {}).get("value", {}).get("parameters", {})
                    print("\nEnvironmental parameters (provider result):")
                    print(json.dumps(summary, indent=2, ensure_ascii=False))
                else:
                    print("\nMCP response:")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:4000])
                print("\nSaved complete response to results/mcp_env_params.json")
                if result.is_error:
                    print("MCP tool returned an error; review the saved response.")
                else:
                    print("DONE: MCP tool call completed without a reported error.")


if __name__ == "__main__":
    asyncio.run(main())
