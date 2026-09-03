import httpx
import pytest

from egypt_compliance import ETAAPIError, ETAAuthenticationError, Token
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)
PDF_BYTES = b"%PDF-1.4 fake-printout"


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_get_document_printout_downloads_pdf_bytes():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["accept"] = request.headers["Accept"]
        captured["accept_language"] = request.headers["Accept-Language"]
        return httpx.Response(
            200,
            content=PDF_BYTES,
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(PDF_BYTES)),
            },
        )

    client = _client_with_handler(handler)
    result = client.get_document_printout(TOKEN, "SG4SSD5KJHHA62D", accept_language="ar")

    assert captured["method"] == "GET"
    assert captured["url"] == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documents/SG4SSD5KJHHA62D/pdf"
    )
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["accept"] == "application/pdf"
    assert captured["accept_language"] == "ar"
    assert result.uuid == "SG4SSD5KJHHA62D"
    assert result.content == PDF_BYTES
    assert result.content_type == "application/octet-stream"
    assert result.content_length == len(PDF_BYTES)
    assert result.size == len(PDF_BYTES)


def test_get_document_printout_saves_pdf(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=PDF_BYTES)

    client = _client_with_handler(handler)
    result = client.get_document_printout("raw-token", "SG4SSD5KJHHA62D")
    path = result.save(tmp_path / "invoice.pdf")
    assert path.read_bytes() == PDF_BYTES


def test_get_document_printout_requires_uuid():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=PDF_BYTES)

    client = _client_with_handler(handler)
    with pytest.raises(ValueError, match="uuid is required"):
        client.get_document_printout(TOKEN, "  ")


def test_get_document_printout_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.get_document_printout(TOKEN, "SG4SSD5KJHHA62D")
    assert exc_info.value.status_code == 401


def test_get_document_printout_raises_api_error_when_not_ready():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "NotReady",
                    "message": "Document is still in processing",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.get_document_printout(TOKEN, "SG4SSD5KJHHA62D")
    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "NotReady"


def test_get_document_printout_raises_api_error_on_forbidden():
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
        client.get_document_printout(TOKEN, "SG4SSD5KJHHA62D")
    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "Forbidden"
