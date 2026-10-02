# Phase B — DOE runtime isolation contract.
#
# optimization_router has been unregistered from main.py.
# All four customer-facing optimization routes MUST return HTTP 404.
#
# Purpose: assert route absence only.
# Authenticated headers are supplied so that a hypothetical 401/403
# from a middleware stub cannot mask a missing-route 404.


def test_doe_route_removed(client, auth_headers):
    """POST /api/v1/optimization/doe must return 404 — router unregistered."""
    r = client.post("/api/v1/optimization/doe", json={}, headers=auth_headers)
    assert r.status_code == 404


def test_model4_predict_route_removed(client, auth_headers):
    """POST /api/v1/optimization/model4/predict must return 404."""
    r = client.post("/api/v1/optimization/model4/predict", json={}, headers=auth_headers)
    assert r.status_code == 404


def test_model4_validate_route_removed(client, auth_headers):
    """POST /api/v1/optimization/model4/validate must return 404."""
    r = client.post("/api/v1/optimization/model4/validate", json={}, headers=auth_headers)
    assert r.status_code == 404


def test_ensemble_route_removed(client, auth_headers):
    """POST /api/v1/optimization/ensemble must return 404."""
    r = client.post("/api/v1/optimization/ensemble", json={}, headers=auth_headers)
    assert r.status_code == 404
