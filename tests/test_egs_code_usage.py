import json
from datetime import datetime, timezone

import httpx
import pytest

from egypt_compliance import (
    CreateEGSCodeUsageRequest,
    EGSCodeUsageItem,
    ETAAPIError,
    ETAAuthenticationError,
    Token,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)

ITEM = EGSCodeUsageItem(
    code_type="EGS",
    parent_code="10000051",
    item_code="EG-674859545-123456784",
    code_name="bottle of water",
    code_name_ar="قارورة ماء",
    active_from=datetime(2021, 2, 21, tzinfo=timezone.utc),
    description="Glass bottle",
    description_ar="قارورة زجاجية",
    request_reason="New product line item",
)


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_create_egs_code_usage_posts_items_payload():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["content_type"] = request.headers["Content-Type"]
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, content=b"")

    client = _client_with_handler(handler)
    result = client.create_egs_code_usage(TOKEN, [ITEM])

    assert captured["url"] == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/codetypes/requests/codes"
    )
    assert captured["method"] == "POST"
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["content_type"] == "application/json"
    assert captured["body"] == {
        "items": [
            {
                "codeType": "EGS",
                "parentCode": "10000051",
                "itemCode": "EG-674859545-123456784",
                "codeName": "bottle of water",
                "codeNameAr": "قارورة ماء",
                "activeFrom": "2021-02-21T00:00:00Z",
                "description": "Glass bottle",
                "descriptionAr": "قارورة زجاجية",
                "requestReason": "New product line item",
            }
        ]
    }
    assert result.success is True
    assert result.payload is None


def test_create_egs_code_usage_accepts_request_model_and_json_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "Submitted"})

    client = _client_with_handler(handler)
    result = client.create_egs_code_usage(
        "raw-token",
        CreateEGSCodeUsageRequest(items=[ITEM]),
        accept_language="ar",
    )
    assert result.success is True
    assert result.payload == {"status": "Submitted"}


def test_create_egs_code_usage_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.create_egs_code_usage(TOKEN, [ITEM])
    assert exc_info.value.status_code == 401


def test_create_egs_code_usage_raises_api_error_when_code_exists():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "BadRequest",
                    "message": "Code already exists",
                    "target": "itemCode",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.create_egs_code_usage(TOKEN, [ITEM])
    err = exc_info.value
    assert err.status_code == 400
    assert err.code == "BadRequest"
    assert err.target == "itemCode"


def test_create_egs_code_usage_raises_api_error_when_parent_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={
                "error": {
                    "code": "NotFound",
                    "message": "Parent code ID is not found",
                    "target": "parentCode",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.create_egs_code_usage(TOKEN, [ITEM])
    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "NotFound"
