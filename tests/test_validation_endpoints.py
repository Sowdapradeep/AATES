import os
import pytest
from fastapi.testclient import TestClient


def test_validation_api_status_and_run(client: TestClient) -> None:
    """Verifies the FAT validation endpoints report properly compiled metrics."""
    # 1. Check GET status
    status_res = client.get("/v1/validation/status")
    assert status_res.status_code == 200
    assert "summary" in status_res.json()
    assert "health_score" in status_res.json()["summary"]

    # 2. Check POST run
    run_res = client.post("/v1/validation/run")
    assert run_res.status_code == 200
    assert run_res.json()["status"] == "success"
    assert "results" in run_res.json()
    assert run_res.json()["results"]["summary"]["health_score"] >= 80


def test_staging_reports_compilation() -> None:
    """Verifies that AWS staging reports and config maps compile properly."""
    from scripts.run_staging_validation import run_staging_checks
    res = run_staging_checks()
    assert res["summary"]["staging_readiness_score"] == 100
    assert os.path.exists("./docs/deployment/staging_status.json")
    assert os.path.exists("./docs/deployment/infrastructure_report.md")


def test_live_deployment_verification() -> None:
    """Verifies that live AWS deployment verification reports compile successfully."""
    from scripts.run_live_deployment_validation import run_live_deployment_checks
    res = run_live_deployment_checks()
    assert res["summary"]["live_readiness_score"] == 100
    assert os.path.exists("./docs/deployment/live/live_status.json")
    assert os.path.exists("./docs/deployment/live/final_live_deployment_readiness.md")


def test_production_activation_reports() -> None:
    """Verifies that production activation reports compile and write successfully."""
    from scripts.generate_final_production_reports import generate_production_reports
    generate_production_reports()
    assert os.path.exists("./docs/production/deployment_report.md")
    assert os.path.exists("./docs/production/production_report.md")
    assert os.path.exists("./docs/production/cost_report.md")
