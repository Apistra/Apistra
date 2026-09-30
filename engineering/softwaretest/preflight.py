"""Verify the public contract and optionally the protected project binding."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def validate_openapi(
    document: dict[str, object], contract: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    info = document.get("info", {})
    if document.get("openapi") != contract["openapi_version"]:
        errors.append("OpenAPI version changed")
    if not isinstance(info, dict) or info.get("title") != contract["api_title"]:
        errors.append("API title changed")
    if not isinstance(info, dict) or info.get("version") != contract["api_version"]:
        errors.append("API version changed")
    paths = document.get("paths", {})
    if not isinstance(paths, dict):
        return [*errors, "paths is not an object"]
    for name, operation in contract["operations"].items():
        method, path = operation
        if path not in paths or method.lower() not in paths[path]:
            errors.append(f"required operation {name} is absent")
    schemes = document.get("components", {}).get("securitySchemes", {})
    if contract["authentication"]["scheme"] not in schemes:
        errors.append("ProjectBearer security scheme is absent")
    return errors


def get_json(url: str, token: str | None = None) -> dict[str, object]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(
        urllib.request.Request(url, headers=headers), timeout=15
    ) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=HERE / "contract.json")
    parser.add_argument("--openapi-file", type=Path)
    parser.add_argument("--require-auth", action="store_true")
    parser.add_argument("--require-reporting", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    base_url = (os.getenv("SOFTWARETEST_BASE_URL") or contract["base_url"]).rstrip("/")
    try:
        document = (
            json.loads(args.openapi_file.read_text(encoding="utf-8"))
            if args.openapi_file
            else get_json(base_url + contract["openapi_path"])
        )
        errors = validate_openapi(document, contract)
        if errors:
            print("; ".join(errors))
            return 1
        project_id = os.getenv("SOFTWARETEST_PROJECT_ID")
        token = os.getenv("SOFTWARETEST_TOKEN")
        if args.require_auth or args.require_reporting:
            if not project_id or not token:
                print(
                    "BLOCKED: SOFTWARETEST_PROJECT_ID and SOFTWARETEST_TOKEN are required"
                )
                return 2
            project = get_json(f"{base_url}/api/v1/projects/{project_id}", token)
            if project.get("id") != project_id:
                print("Authenticated project round-trip returned a different project")
                return 1
        if args.require_reporting:
            cycles = get_json(f"{base_url}/api/v1/projects/{project_id}/cycles", token)
            reports = get_json(
                f"{base_url}/api/v1/projects/{project_id}/ci-reports", token
            )
            if not isinstance(cycles.get("results"), list):
                print("Authenticated cycle listing has an unexpected shape")
                return 1
            if not isinstance(reports.get("results"), list):
                print("Authenticated CI-report listing has an unexpected shape")
                return 1
        print("Softwaretest.it contract preflight passed.")
        return 0
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        print(f"Softwaretest.it preflight failed safely: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
