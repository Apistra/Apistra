"""Deterministic CI resource contracts; this is deliberately not a load test."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
COMPOSE = ROOT / "deploy/compose/compose.staging.yml"


def test_candidate_services_have_bounded_resource_contracts() -> None:
    compose = COMPOSE.read_text(encoding="utf-8")

    assert 'cpus: "0.50"' in compose
    assert "memory: 256M" in compose
    assert "pids: 100" in compose
    assert 'tmpfs: ["/tmp:size=16m,mode=1777"]' in compose


def test_candidate_exposure_and_runtime_privileges_are_bounded() -> None:
    compose = COMPOSE.read_text(encoding="utf-8")

    assert 'ports: ["127.0.0.1:${APISTRA_API_PORT:?set APISTRA_API_PORT}:8080"]' in compose
    assert 'ports: ["127.0.0.1:${APISTRA_WEB_PORT:?set APISTRA_WEB_PORT}:3000"]' in compose
    assert 'user: "10001:10001"' in compose
    assert "read_only: true" in compose
    assert 'cap_drop: ["ALL"]' in compose
    assert 'security_opt: ["no-new-privileges:true"]' in compose


def test_resource_gate_does_not_claim_shared_runner_performance() -> None:
    delivery = (ROOT / "docs/planning/05-delivery-ci-contract.md").read_text(encoding="utf-8")

    assert "does not measure latency, throughput, or concurrent load" in delivery
    assert "no running representative candidate" in delivery
