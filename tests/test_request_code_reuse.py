import json

import httpx
import pytest

from egypt_compliance import (
    CodeReuseItem,
    ETAAPIError,
    ETAAuthenticationError,
    RequestCodeReuseRequest,
    Token,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)

ITEM = CodeReuseItem(
    code_type="EGS",
    item_code="EG-100000053-10011",
    comment="Code that I already use in my factory",
)


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_request_code_reuse_puts_items_payload():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["content_type"] = request.headers["Content-Type"]
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, content=b"")

    client = _client_with_handler(handler)
    result = client.request_code_reuse(TOKEN, [ITEM])

    assert captured["url"] == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/codetypes/requests/codeusages"
    )
    assert captured["method"] == "PUT"
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["content_type"] == "application/json"
    assert captured["body"] == {
        "items": [
            {
                "codetype": "EGS",
                "itemCode": "EG-100000053-10011",
                "comment": "Code that I already use in my factory",
            }
        ]
    }
    assert result.success is True
    assert result.payload is None


def test_request_code_reuse_accepts_request_model_and_json_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "Submitted"})

    client = _client_with_handler(handler)
    result = client.request_code_reuse(
        "raw-token",
        RequestCodeReuseRequest(items=[ITEM]),
        accept_language="ar",
    )
    assert result.success is True
    assert result.payload == {"status": "Submitted"}


def test_request_code_reuse_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.request_code_reuse(TOKEN, [ITEM])
    assert exc_info.value.status_code == 401


def test_request_code_reuse_raises_api_error_when_usage_already_exists():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "ValidationError",
                    "message": "User already has usage on this code",
                    "target": "itemCode",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.request_code_reuse(TOKEN, [ITEM])
    err = exc_info.value
    assert err.status_code == 400
    assert err.code == "ValidationError"
    assert err.target == "itemCode"
