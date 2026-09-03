import httpx
import pytest

from egypt_compliance import ETAAPIError, ETAAuthenticationError, Token
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)
ZIP_BYTES = b"PK\x03\x04fake-zip-content"


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_get_document_package_downloads_zip_bytes():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["accept"] = request.headers["Accept"]
        captured["accept_language"] = request.headers["Accept-Language"]
        return httpx.Response(
            200,
            content=ZIP_BYTES,
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(ZIP_BYTES)),
            },
        )

    client = _client_with_handler(handler)
    result = client.get_document_package(TOKEN, "45KJHHA62D", accept_language="ar")

    assert captured["method"] == "GET"
    assert captured["url"] == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documentpackages/45KJHHA62D"
    )
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["accept"] == "application/octet-stream"
    assert captured["accept_language"] == "ar"
    assert result.ready is True
    assert result.package_id == "45KJHHA62D"
    assert result.content == ZIP_BYTES
    assert result.content_type == "application/octet-stream"
    assert result.content_length == len(ZIP_BYTES)
    assert result.size == len(ZIP_BYTES)


def test_get_document_package_saves_zip(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=ZIP_BYTES)

    client = _client_with_handler(handler)
    result = client.get_document_package("raw-token", "45KJHHA62D")
    path = result.save(tmp_path / "package.zip")
    assert path.read_bytes() == ZIP_BYTES


def test_get_document_package_sends_range_header():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["range"] = request.headers.get("Range")
        return httpx.Response(206, content=ZIP_BYTES[:4])

    client = _client_with_handler(handler)
    result = client.get_document_package(TOKEN, "45KJHHA62D", byte_range="bytes=0-3")
    assert captured["range"] == "bytes=0-3"
    assert result.ready is True
    assert result.content == ZIP_BYTES[:4]


def test_get_document_package_not_ready_on_204():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    client = _client_with_handler(handler)
    result = client.get_document_package(TOKEN, "45KJHHA62D")
    assert result.ready is False
    assert result.content is None
    with pytest.raises(ValueError, match="not ready"):
        result.save("package.zip")


def test_get_document_package_requires_package_id():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=ZIP_BYTES)

    client = _client_with_handler(handler)
    with pytest.raises(ValueError, match="package_id is required"):
        client.get_document_package(TOKEN, "  ")


def test_get_document_package_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.get_document_package(TOKEN, "45KJHHA62D")
    assert exc_info.value.status_code == 401


def test_get_document_package_raises_api_error_on_forbidden():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "error": {
                    "code": "Forbidden",
                    "message": "B2B Deny ERP Document Retrieval",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.get_document_package(TOKEN, "45KJHHA62D")
    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "Forbidden"
