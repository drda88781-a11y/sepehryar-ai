"""
Tests for Sepehryar Web Application static assets and web endpoints.
"""
from fastapi.testclient import TestClient
from app.api.server import create_api_app


def test_web_static_index_serving():
    """Verify that root URL serves the single-page web app index.html."""
    app = create_api_app()
    client = TestClient(app)

    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "Sepehryar AI Enterprise" in res.text
    assert "spotlightModal" in res.text
    assert "btnSend" in res.text


def test_web_static_assets_serving():
    """Verify CSS and JavaScript assets are properly served with correct MIME types."""
    app = create_api_app()
    client = TestClient(app)

    # CSS
    res_css = client.get("/css/style.css")
    assert res_css.status_code == 200
    assert "text/css" in res_css.headers.get("content-type", "")
    assert "--accent-cyan" in res_css.text

    # JS API
    res_api = client.get("/js/api.js")
    assert res_api.status_code == 200
    assert "javascript" in res_api.headers.get("content-type", "").lower()
    assert "SepehryarApiClient" in res_api.text

    # JS App
    res_app = client.get("/js/app.js")
    assert res_app.status_code == 200
    assert "javascript" in res_app.headers.get("content-type", "").lower()
    assert "SepehryarApp" in res_app.text
