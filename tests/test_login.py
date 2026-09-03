import base64
from urllib.parse import parse_qs

import httpx
import pytest

from egypt_compliance import ETAAuthenticationError, ETAError, Token
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

SUCCESS_BODY = {
    "access_token": "jwt-token-value",
    "token_type": "Bearer",
    "expires_in": 3600,
    "scope": "InvoicingAPI",
}


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_login_sends_basic_auth_and_client_credentials_body():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["content_type"] = request.headers["Content-Type"]
        captured["onbehalfof"] = request.headers.get("onbehalfof")
        captured["body"] = parse_qs(request.content.decode("utf-8"))
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    token = client.login(client_id="my-id", client_secret="my-secret")

    expected_basic = base64.b64encode(b"my-id:my-secret").decode("ascii")
    assert captured["url"] == "https://id.preprod.eta.gov.eg/connect/token"
    assert captured["method"] == "POST"
    assert captured["authorization"] == f"Basic {expected_basic}"
    assert captured["content_type"] == "application/x-www-form-urlencoded"
    assert captured["onbehalfof"] is None
    assert captured["body"]["grant_type"] == ["client_credentials"]
    assert captured["body"]["scope"] == ["InvoicingAPI"]
    assert token == Token(
        access_token="jwt-token-value",
        token_type="Bearer",
        expires_in=3600,
        scope="InvoicingAPI",
    )


def test_login_adds_onbehalfof_header_for_intermediary():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["onbehalfof"] = request.headers.get("onbehalfof")
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    client.login(
        client_id="my-id",
        client_secret="my-secret",
        on_behalf_of="100015840",
    )
    assert captured["onbehalfof"] == "100015840"


def test_login_raises_authentication_error_on_400():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": "invalid_client",
                "error_description": "User blocked",
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.login(client_id="bad", client_secret="bad")

    err = exc_info.value
    assert err.error == "invalid_client"
    assert err.error_description == "User blocked"
    assert err.status_code == 400
    assert "User blocked" in str(err)


def test_login_wraps_transport_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    client = _client_with_handler(handler)
    with pytest.raises(ETAError, match="Failed to reach ETA identity service"):
        client.login(client_id="my-id", client_secret="my-secret")
