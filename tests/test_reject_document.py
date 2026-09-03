import json

import httpx
import pytest

from egypt_compliance import (
    ETAAPIError,
    ETAAuthenticationError,
    RejectDocumentRequest,
    Token,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)
UUID = "F9D425P6DS7D8IU"


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_reject_document_puts_rejected_status_and_reason():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["content_type"] = request.headers["Content-Type"]
        captured["accept_language"] = request.headers["Accept-Language"]
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, content=b"")

    client = _client_with_handler(handler)
    result = client.reject_document(
        TOKEN,
        UUID,
        "Received incorrect invoice from the seller",
        accept_language="ar",
    )

    assert captured["url"] == (
        f"https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documents/state/{UUID}/state"
    )
    assert captured["method"] == "PUT"
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["content_type"] == "application/json"
    assert captured["accept_language"] == "ar"
    assert captured["body"] == {
        "status": "rejected",
        "reason": "Received incorrect invoice from the seller",
    }
    assert result.success is True
    assert result.payload is None


def test_reject_document_accepts_request_model():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={"status": "rejected"})

    client = _client_with_handler(handler)
    result = client.reject_document(
        "raw-token",
        UUID,
        RejectDocumentRequest(reason="Received incorrect invoice from the seller"),
    )
    assert captured["body"] == {
        "status": "rejected",
        "reason": "Received incorrect invoice from the seller",
    }
    assert result.success is True
    assert result.payload == {"status": "rejected"}


def test_reject_document_requires_uuid_and_reason():
    client = ETAClient(config=PREPROD, http_client=httpx.Client())
    with pytest.raises(ValueError, match="uuid"):
        client.reject_document(TOKEN, "  ", "Received incorrect invoice from the seller")
    with pytest.raises(ValueError, match="reason"):
        client.reject_document(TOKEN, UUID, "   ")


def test_reject_document_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.reject_document(TOKEN, UUID, "Received incorrect invoice from the seller")
    assert exc_info.value.status_code == 401


def test_reject_document_raises_api_error_when_period_over():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "OperationPeriodOver",
                    "message": "Rejection period has expired",
                    "target": "uuid",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.reject_document(TOKEN, UUID, "Received incorrect invoice from the seller")
    err = exc_info.value
    assert err.status_code == 400
    assert err.code == "OperationPeriodOver"
    assert err.target == "uuid"
