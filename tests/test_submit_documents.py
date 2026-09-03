import json

import httpx
import pytest

from egypt_compliance import (
    DocumentSignature,
    ETAAPIError,
    ETAAuthenticationError,
    SubmitDocumentsRequest,
    SubmittedDocument,
    Token,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)

SIGNED_DOCUMENT = {
    "issuer": {"type": "B", "id": "100015840", "name": "Issuer Co"},
    "receiver": {"type": "B", "id": "200015840", "name": "Buyer Co"},
    "documentType": "i",
    "documentTypeVersion": "1.0",
    "dateTimeIssued": "2024-02-13T13:15:00Z",
    "internalID": "PZ-234-A",
    "invoiceLines": [{"description": "Water", "itemCode": "EG-100015840-1"}],
    "signatures": [{"type": "I", "value": "cades-bes-base64"}],
}

SUCCESS_BODY = {
    "submissionUUID": "TZRKK8MFZCPSTW9XCYWBMKME10",
    "acceptedDocuments": [
        {
            "uuid": "TZRKK8MFZCPSTW9XCYWBMKME11",
            "longId": "TZRKK8MFZCPSTW9XCYWBMKME10ABC1231602681697",
            "internalId": "PZ-234-A",
        }
    ],
    "rejectedDocuments": [
        {
            "internalId": "P-234",
            "error": {
                "code": "BadArgument",
                "message": "Invalid document structure",
                "target": "invoiceLines",
                "details": [],
            },
        }
    ],
}


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_submit_documents_posts_signed_json_unchanged():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["content_type"] = request.headers["Content-Type"]
        captured["accept_language"] = request.headers["Accept-Language"]
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(202, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    result = client.submit_documents(TOKEN, [SIGNED_DOCUMENT], accept_language="ar")

    assert captured["url"] == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documentsubmissions"
    )
    assert captured["method"] == "POST"
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["content_type"] == "application/json"
    assert captured["accept_language"] == "ar"
    assert captured["body"] == {"documents": [SIGNED_DOCUMENT]}
    assert result.submission_uuid == "TZRKK8MFZCPSTW9XCYWBMKME10"
    assert result.accepted_documents[0].uuid == "TZRKK8MFZCPSTW9XCYWBMKME11"
    assert result.accepted_documents[0].long_id == "TZRKK8MFZCPSTW9XCYWBMKME10ABC1231602681697"
    assert result.accepted_documents[0].internal_id == "PZ-234-A"
    assert result.rejected_documents[0].internal_id == "P-234"
    assert result.rejected_documents[0].error.code == "BadArgument"
    assert result.rejected_documents[0].error.target == "invoiceLines"


def test_submit_documents_accepts_http_200():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"submissionUUID": "ABC123"})

    client = _client_with_handler(handler)
    result = client.submit_documents("raw-token", [SIGNED_DOCUMENT])
    assert result.submission_uuid == "ABC123"
    assert result.accepted_documents == []
    assert result.rejected_documents == []


def test_submit_documents_accepts_request_model():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(202, json={"submissionUUID": "SUB-1"})

    document = SubmittedDocument(
        document_type="i",
        document_type_version="1.0",
        internal_id="INV-1",
        signatures=[DocumentSignature(type="I", value="cades")],
        issuer={"id": "100015840"},
    )
    client = _client_with_handler(handler)
    result = client.submit_documents(TOKEN, SubmitDocumentsRequest(documents=[document]))

    assert captured["body"]["documents"][0]["documentType"] == "i"
    assert captured["body"]["documents"][0]["internalID"] == "INV-1"
    assert captured["body"]["documents"][0]["issuer"] == {"id": "100015840"}
    assert captured["body"]["documents"][0]["signatures"] == [{"type": "I", "value": "cades"}]
    assert result.submission_uuid == "SUB-1"


def test_submit_documents_rejects_empty_list():
    client = ETAClient(config=PREPROD, http_client=httpx.Client())
    with pytest.raises(ValueError, match="at least one document"):
        client.submit_documents(TOKEN, [])


def test_submit_documents_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.submit_documents(TOKEN, [SIGNED_DOCUMENT])
    assert exc_info.value.status_code == 401


def test_submit_documents_raises_api_error_on_bad_structure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "BadStructure",
                    "message": "Submission is missing documents",
                    "target": "documents",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.submit_documents(TOKEN, [SIGNED_DOCUMENT])
    err = exc_info.value
    assert err.status_code == 400
    assert err.code == "BadStructure"
    assert err.target == "documents"
