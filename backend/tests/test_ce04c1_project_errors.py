import pytest
from fastapi.testclient import TestClient
from app.models import Project, WeldPoint
from app.models.error_codes import ApiErrorCode, ResourceType


def test_create_project_duplicate_code_returns_resource_conflict(client: TestClient, db_session):
    Project(code="P001", name="Project 1").save(db_session)
    response = client.post("/api/v1/projects", json={"code": "P001", "name": "Duplicate"})
    assert response.status_code == 409
    assert response.json()["error_code"] == ApiErrorCode.RESOURCE_CONFLICT
    assert response.json()["context"]["resource_type"] == ResourceType.PROJECT


def test_get_project_nonexistent_returns_resource_not_found(client: TestClient):
    response = client.get("/api/v1/projects/9999")
    assert response.status_code == 404
    assert response.json()["error_code"] == ApiErrorCode.RESOURCE_NOT_FOUND
    assert response.json()["context"]["resource_type"] == ResourceType.PROJECT
    assert response.json()["context"]["resource_id"] == 9999


def test_create_weld_point_duplicate_code_returns_resource_conflict(client: TestClient, db_session):
    project = Project(code="P001", name="Project 1").save(db_session)
    WeldPoint(code="W001", project_id=project.id).save(db_session)
    response = client.post(f"/api/v1/projects/{project.id}/weld-points", json={"code": "W001"})
    assert response.status_code == 409
    assert response.json()["error_code"] == ApiErrorCode.RESOURCE_CONFLICT
    assert response.json()["context"]["resource_type"] == ResourceType.WELD_POINT


def test_get_weld_point_nonexistent_returns_resource_not_found(client: TestClient, db_session):
    project = Project(code="P001", name="Project 1").save(db_session)
    response = client.get(f"/api/v1/projects/{project.id}/weld-points/9999")
    assert response.status_code == 404
    assert response.json()["error_code"] == ApiErrorCode.RESOURCE_NOT_FOUND
    assert response.json()["context"]["resource_type"] == ResourceType.WELD_POINT
    assert response.json()["context"]["resource_id"] == 9999
