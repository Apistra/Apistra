"""Build once, archive, inventory, and identify an immutable local CAP-00 candidate."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts" / "cap00-candidate"


def run(*command: str, capture: bool = False) -> str:
    result = subprocess.run(
        command, cwd=ROOT, check=True, text=True, capture_output=capture
    )
    return result.stdout.strip() if capture else ""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def assert_clean_commit() -> str:
    if run("git", "status", "--porcelain", capture=True):
        raise SystemExit("Candidate builds require a clean committed worktree.")
    commit = run("git", "rev-parse", "HEAD", capture=True)
    if len(commit) != 40:
        raise SystemExit("Could not resolve a full commit SHA.")
    return commit


def packages(image: str, runtime: str) -> list[dict[str, str]]:
    if runtime == "python":
        code = "import importlib.metadata as m,json;print(json.dumps(sorted([{'name':d.metadata['Name'],'version':d.version} for d in m.distributions()],key=lambda x:(x['name'] or '').lower())))"
        raw = run(
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "python",
            image,
            "-c",
            code,
            capture=True,
        )
    else:
        code = "const fs=require('fs'),p=require('path'),out=[];function w(d){if(!fs.existsSync(d))return;for(const n of fs.readdirSync(d)){const q=p.join(d,n);if(n==='package.json'){try{const x=JSON.parse(fs.readFileSync(q));if(x.name&&x.version)out.push({name:x.name,version:x.version})}catch{}}else if(!n.startsWith('.')){try{if(fs.statSync(q).isDirectory())w(q)}catch{}}}}w('/app/node_modules');console.log(JSON.stringify(out.sort((a,b)=>a.name.localeCompare(b.name))))"
        raw = run(
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "node",
            image,
            "-e",
            code,
            capture=True,
        )
    unique = {(item["name"], item["version"]): item for item in json.loads(raw)}
    return list(unique.values())


def main() -> int:
    commit = assert_clean_commit()
    version = "0.0.0+" + commit[:12]
    if ARTIFACTS.exists():
        shutil.rmtree(ARTIFACTS)
    ARTIFACTS.mkdir(parents=True)
    images = {
        "api": f"apistra-api:cap00-{commit}",
        "worker": f"apistra-worker:cap00-{commit}",
        "web": f"apistra-web:cap00-{commit}",
    }
    common = (
        "--build-arg",
        f"APISTRA_VERSION={version}",
        "--build-arg",
        f"APISTRA_COMMIT={commit}",
    )
    run(
        "docker",
        "build",
        "--file",
        "backend/Dockerfile",
        "--target",
        "api",
        "--tag",
        images["api"],
        *common,
        ".",
    )
    run(
        "docker",
        "build",
        "--file",
        "backend/Dockerfile",
        "--target",
        "worker",
        "--tag",
        images["worker"],
        *common,
        ".",
    )
    run(
        "docker",
        "build",
        "--file",
        "apps/web/Dockerfile",
        "--tag",
        images["web"],
        *common,
        ".",
    )
    manifest_images: dict[str, object] = {}
    for service, image in images.items():
        archive = ARTIFACTS / f"{service}.tar"
        run("docker", "image", "save", "--output", str(archive), image)
        manifest_images[service] = {
            "reference": image,
            "image_id": run(
                "docker", "image", "inspect", "--format", "{{.Id}}", image, capture=True
            ),
            "archive": archive.name,
            "archive_sha256": sha256(archive),
        }
    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"apistra-cap00-{commit}",
        "documentNamespace": f"https://apistra.dev/sbom/cap00/{commit}",
        "creationInfo": {
            "created": datetime.now(UTC).isoformat(),
            "creators": ["Tool: Apistra-CAP00-SBOM"],
        },
        "packages": [
            {
                "name": item["name"],
                "versionInfo": item["version"],
                "SPDXID": f"SPDXRef-Package-{index}",
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
            }
            for index, item in enumerate(
                packages(images["api"], "python") + packages(images["web"], "node"), 1
            )
        ],
    }
    sbom_path = ARTIFACTS / "sbom.spdx.json"
    sbom_path.write_text(
        json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema_version": "1.0",
        "capability": "CAP-00",
        "source_commit": commit,
        "version": version,
        "created_at": datetime.now(UTC).isoformat(),
        "images": manifest_images,
        "base_images": {
            "python": "python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e",
            "node": "node:24.19.0-bookworm-slim@sha256:a9f5f7c91a432850b2a8a7797adf5eadb6c733ceed61167806cee7ea7fbc29df",
        },
        "contracts": [
            "contracts/openapi/cap00-health.openapi.json",
            "contracts/events/cap00-result-bundle.schema.json",
        ],
        "migration": {
            "command": "python -m apistra.entrypoints.migration",
            "schema_version": "cap00-none",
        },
        "rules": ["ARCH-001", "ARCH-010", "ARCH-011", "ARCH-013"],
        "test_definitions": [
            "tests/bdd/features/cap00-bootstrap.feature",
            "tests/manual/CAP00-MAN-001.md",
        ],
        "sbom": {"path": sbom_path.name, "sha256": sha256(sbom_path)},
    }
    manifest_path = ARTIFACTS / "candidate-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (ARTIFACTS / "candidate-manifest.sha256").write_text(
        f"{sha256(manifest_path)}  {manifest_path.name}\n", encoding="utf-8"
    )
    print(f"Candidate written to {ARTIFACTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
