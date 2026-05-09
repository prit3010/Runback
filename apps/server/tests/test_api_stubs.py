"""Every endpoint in openapi.yaml must respond."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from openapi_spec_validator import validate
from runback_server.main import app

OPENAPI_PATH = Path(__file__).resolve().parents[3] / "docs" / "contracts" / "openapi.yaml"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_openapi_yaml_is_valid():
    spec = yaml.safe_load(OPENAPI_PATH.read_text())
    validate(spec)


def test_every_documented_endpoint_responds(client):
    spec = yaml.safe_load(OPENAPI_PATH.read_text())
    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            url = path
            for param in operation.get("parameters", []):
                if param.get("in") == "path":
                    url = url.replace("{" + param["name"] + "}", "dummy")
            resp = client.request(method.upper(), url, headers={"x-runback-run-id": "dummy"})
            assert resp.status_code != 405, f"{method.upper()} {path} not registered"
            assert resp.status_code in {200, 201, 202, 400, 404, 422, 501}
