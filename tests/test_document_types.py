from decimal import Decimal

import httpx
import pytest

from egypt_compliance import (
    DocumentType,
    ETAAPIError,
    ETAAuthenticationError,
    ETAError,
    Token,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

SUCCESS_BODY = {
    "result": [
        {
            "id": 45,
            "name": "i",
            "description": "Invoice",
            "activeFrom": "2015-02-13T13:15Z",
            "activeTo": None,
            "documentTypeVersions": [
                {
                    "id": 454,
                    "name": "1.0",
                    "description": "Invoice version 1.0",
                    "versionNumber": 1.0,
                    "status": "published",
                    "activeFrom": "2015-02-13T13:15Z",
                    "activeTo": "2027-03-01T00:00:00Z",
                }
            ],
        }
    ]
}

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_get_document_types_sends_bearer_token_and_parses_result():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["accept"] = request.headers["Accept"]
        captured["accept_language"] = request.headers["Accept-Language"]
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    result = client.get_document_types(TOKEN)

    assert captured["url"] == "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documenttypes"
    assert captured["method"] == "GET"
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["accept"] == "application/json"
    assert captured["accept_language"] == "en"
    assert len(result) == 1
    doc_type = result.result[0]
    assert isinstance(doc_type, DocumentType)
    assert doc_type.id == 45
    assert doc_type.name == "i"
    assert doc_type.description == "Invoice"
    assert doc_type.active_to is None
    version = doc_type.document_type_versions[0]
    assert version.id == 454
    assert version.version_number == Decimal("1.0")
    assert version.status == "published"


def test_get_document_types_accepts_raw_token_and_language():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers["Authorization"]
        captured["accept_language"] = request.headers["Accept-Language"]
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    client.get_document_types("raw-token", accept_language="ar")
    assert captured["authorization"] == "Bearer raw-token"
    assert captured["accept_language"] == "ar"


def test_get_document_types_parses_bare_list_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=SUCCESS_BODY["result"])

    client = _client_with_handler(handler)
    result = client.get_document_types(TOKEN)
    assert [item.name for item in result] == ["i"]


def test_get_document_types_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.get_document_types(TOKEN)
    assert exc_info.value.status_code == 401
    assert "Token expired" in str(exc_info.value)


def test_get_document_types_raises_api_error_on_standard_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "BadRequest",
                    "message": "Invalid request",
                    "target": "documenttypes",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.get_document_types(TOKEN)
    err = exc_info.value
    assert err.code == "BadRequest"
    assert err.target == "documenttypes"
    assert err.status_code == 400
    assert "Invalid request" in str(err)


def test_get_document_types_wraps_transport_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    client = _client_with_handler(handler)
    with pytest.raises(ETAError, match="Failed to reach ETA API"):
        client.get_document_types(TOKEN)
