import json
from datetime import datetime, timezone

import httpx
import pytest

from egypt_compliance import (
    ETAAPIError,
    ETAAuthenticationError,
    Token,
    UpdateCodeRequest,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_update_code_puts_optional_fields():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["content_type"] = request.headers["Content-Type"]
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, content=b"")

    client = _client_with_handler(handler)
    result = client.update_code(
        TOKEN,
        "EG-113317713-1234",
        code_type="EGS",
        code_description_primary_lang="Water bottle, 600 mg, plastic bottle",
        code_description_secondary_lang="قاروره مياه يلاستيكية",
        active_to=datetime(2021, 5, 21, 23, 59, tzinfo=timezone.utc),
        linked_code="EG-674859545-9875",
    )

    assert captured["url"] == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/codetypes/EGS/codes/EG-113317713-1234"
    )
    assert captured["method"] == "PUT"
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["content_type"] == "application/json"
    assert captured["body"] == {
        "codeDescriptionPrimaryLang": "Water bottle, 600 mg, plastic bottle",
        "codeDescriptionSecondaryLang": "قاروره مياه يلاستيكية",
        "activeTo": "2021-05-21T23:59:00Z",
        "linkedCode": "EG-674859545-9875",
    }
    assert result.success is True
    assert result.payload is None


def test_update_code_accepts_request_model_and_json_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "Updated"})

    client = _client_with_handler(handler)
    result = client.update_code(
        "raw-token",
        "EG-113317713-1234",
        UpdateCodeRequest(linked_code="EG-674859545-9875"),
        accept_language="ar",
    )
    assert result.success is True
    assert result.payload == {"status": "Updated"}


def test_update_code_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.update_code(TOKEN, "EG-113317713-1234", linked_code="EG-1")
    assert exc_info.value.status_code == 401


def test_update_code_raises_api_error_on_bad_request():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "BadRequest",
                    "message": "Code is not in Approved state",
                    "target": "itemCode",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.update_code(TOKEN, "EG-113317713-1234", linked_code="EG-1")
    err = exc_info.value
    assert err.status_code == 400
    assert err.code == "BadRequest"
    assert err.target == "itemCode"
