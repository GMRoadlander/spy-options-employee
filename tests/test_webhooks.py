"""Tests for TradingView webhook endpoint.

Validates FastAPI endpoint behavior: payload parsing, HMAC-SHA256 signature
verification, malformed request handling, and alert queueing.
"""

import asyncio
import hashlib
import hmac
import json
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from src.config import config
from src.webhook.app import app
from src.webhook.tradingview import TradingViewAlert, alert_queue


def _sign(body: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 hex digest for a request body."""
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture(autouse=True)
def _clear_queue():
    """Drain the alert queue before each test."""
    while not alert_queue.empty():
        try:
            alert_queue.get_nowait()
        except asyncio.QueueEmpty:
            break
    yield
    while not alert_queue.empty():
        try:
            alert_queue.get_nowait()
        except asyncio.QueueEmpty:
            break


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


def test_health_endpoint(client):
    """GET /health returns 200 with status ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Valid payloads
# ---------------------------------------------------------------------------


def test_valid_tradingview_payload(client):
    """POST /webhook/tradingview with valid JSON returns 200."""
    payload = {
        "action": "alert",
        "ticker": "SPX",
        "price": 5950.25,
    }
    resp = client.post("/webhook/tradingview", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "received"
    assert data["action"] == "alert"
    assert data["ticker"] == "SPX"


def test_full_tradingview_payload(client):
    """POST with all fields populates the alert correctly."""
    payload = {
        "action": "buy_call",
        "ticker": "SPY",
        "price": 595.50,
        "time": "2026-02-21T14:30:00Z",
        "interval": "5",
        "volume": 1234567.0,
        "strategy": "GEX Bounce",
        "message": "Strong bullish signal detected",
    }
    resp = client.post("/webhook/tradingview", json=payload)
    assert resp.status_code == 200


def test_minimal_payload(client):
    """Only action and ticker are required."""
    payload = {"action": "alert", "ticker": "SPX"}
    resp = client.post("/webhook/tradingview", json=payload)
    assert resp.status_code == 200


def test_extra_fields_accepted(client):
    """Unknown fields from Pine Script are accepted (extra='allow')."""
    payload = {
        "action": "alert",
        "ticker": "SPX",
        "custom_indicator": 42.5,
        "pine_script_var": "hello",
    }
    resp = client.post("/webhook/tradingview", json=payload)
    assert resp.status_code == 200


def test_alert_queued(client):
    """Valid POST queues the alert for Discord delivery."""
    payload = {"action": "alert", "ticker": "SPX", "price": 5900.0}
    client.post("/webhook/tradingview", json=payload)

    assert not alert_queue.empty()
    alert = alert_queue.get_nowait()
    assert isinstance(alert, TradingViewAlert)
    assert alert.ticker == "SPX"
    assert alert.price == 5900.0


# ---------------------------------------------------------------------------
# HMAC-SHA256 signature validation
# ---------------------------------------------------------------------------


def test_no_secret_configured_allows_all(client, monkeypatch):
    """When WEBHOOK_SECRET is empty, no signature header is needed."""
    mock_config = replace(config, webhook_secret="")
    monkeypatch.setattr("src.webhook.tradingview.config", mock_config)
    payload = {"action": "alert", "ticker": "SPX"}
    resp = client.post("/webhook/tradingview", json=payload)
    assert resp.status_code == 200


def test_valid_hmac_signature_passes(client, monkeypatch):
    """When WEBHOOK_SECRET is set, a valid HMAC-SHA256 signature passes."""
    secret = "my-secret-123"
    mock_config = replace(config, webhook_secret=secret)
    monkeypatch.setattr("src.webhook.tradingview.config", mock_config)

    body = json.dumps({"action": "alert", "ticker": "SPX"}).encode()
    signature = _sign(body, secret)

    resp = client.post(
        "/webhook/tradingview",
        content=body,
        headers={
            "X-Webhook-Signature": signature,
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 200


def test_invalid_hmac_signature_returns_401(client, monkeypatch):
    """When WEBHOOK_SECRET is set and signature is wrong, 401 is returned."""
    secret = "my-secret-123"
    mock_config = replace(config, webhook_secret=secret)
    monkeypatch.setattr("src.webhook.tradingview.config", mock_config)

    body = json.dumps({"action": "alert", "ticker": "SPX"}).encode()

    resp = client.post(
        "/webhook/tradingview",
        content=body,
        headers={
            "X-Webhook-Signature": "bad-signature",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 401


def test_missing_signature_returns_401(client, monkeypatch):
    """When WEBHOOK_SECRET is set and no signature header, 401 is returned."""
    mock_config = replace(config, webhook_secret="my-secret-123")
    monkeypatch.setattr("src.webhook.tradingview.config", mock_config)

    payload = {"action": "alert", "ticker": "SPX"}
    resp = client.post("/webhook/tradingview", json=payload)
    assert resp.status_code == 401


def test_tampered_body_fails_hmac(client, monkeypatch):
    """Signature computed for one body does not validate a different body."""
    secret = "my-secret-123"
    mock_config = replace(config, webhook_secret=secret)
    monkeypatch.setattr("src.webhook.tradingview.config", mock_config)

    original_body = json.dumps({"action": "alert", "ticker": "SPX"}).encode()
    signature = _sign(original_body, secret)

    tampered_body = json.dumps({"action": "alert", "ticker": "AAPL"}).encode()

    resp = client.post(
        "/webhook/tradingview",
        content=tampered_body,
        headers={
            "X-Webhook-Signature": signature,
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Malformed payloads
# ---------------------------------------------------------------------------


def test_missing_required_field_returns_422(client):
    """Missing 'action' or 'ticker' returns 422."""
    payload = {"price": 5950.25}
    resp = client.post("/webhook/tradingview", json=payload)
    assert resp.status_code == 422


def test_invalid_json_returns_422(client):
    """Non-JSON body returns 422."""
    resp = client.post(
        "/webhook/tradingview",
        content="not json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422


def test_empty_body_returns_422(client):
    """Empty body returns 422."""
    resp = client.post(
        "/webhook/tradingview",
        content="",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Pydantic model
# ---------------------------------------------------------------------------


def test_tradingview_alert_model():
    """TradingViewAlert Pydantic model validates correctly."""
    alert = TradingViewAlert(action="buy_call", ticker="SPX", price=5950.0)
    assert alert.action == "buy_call"
    assert alert.ticker == "SPX"
    assert alert.price == 5950.0
    assert alert.time is None
    assert alert.message is None


def test_tradingview_alert_extra_fields():
    """Extra fields are stored via model_config extra='allow'."""
    alert = TradingViewAlert(
        action="alert",
        ticker="SPY",
        custom_field="test",
    )
    assert alert.action == "alert"
    # Extra fields accessible via model_extra
    assert alert.model_extra is not None
    assert alert.model_extra.get("custom_field") == "test"
