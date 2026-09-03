import json
from datetime import datetime, timezone

import httpx
import pytest

from egypt_compliance import (
    DocumentPackageItemCode,
    DocumentPackageQueryParameters,
    ETAAPIError,
    ETAAuthenticationError,
    RequestDocumentPackageRequest,
    Token,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_request_document_package_posts_filters_and_parses_package_id():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["content_type"] = request.headers["Content-Type"]
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(201, json={"packageId": "KLJHH78NJUHQ"})

    client = _client_with_handler(handler)
    result = client.request_document_package(
        TOKEN,
        type="full",
        format="JSON",
        date_from=datetime(2015, 2, 13, 14, 20, tzinfo=timezone.utc),
        date_to="2015-02-20T21:30Z",
        document_type_names=["i"],
        statuses=["valid"],
        products_internal_codes=["8383S"],
        receiver_sender_type=0,
        receiver_sender_id="345987378",
        branch_number="0",
        item_codes=[DocumentPackageItemCode(code_value="1000000000003", code_type="GS1")],
        truncate_if_exceeded=False,
    )

    assert captured["url"] == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documentpackages/requests"
    )
    assert captured["method"] == "POST"
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["content_type"] == "application/json"
    assert captured["body"] == {
        "type": "full",
        "format": "JSON",
        "queryParameters": {
            "dateFrom": "2015-02-13T14:20:00Z",
            "dateTo": "2015-02-20T21:30Z",
            "documentTypeNames": ["i"],
            "statuses": ["valid"],
            "productsInternalCodes": ["8383S"],
            "receiverSenderType": "0",
            "receiverSenderId": "345987378",
            "branchNumber": "0",
            "itemCodes": [{"codeValue": "1000000000003", "codeType": "GS1"}],
            "truncateifexceeded": False,
        },
    }
    assert result.package_id == "KLJHH78NJUHQ"


def test_request_document_package_accepts_request_model_and_http_200():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode("utf-8"))
        captured["accept_language"] = request.headers["Accept-Language"]
        return httpx.Response(200, json={"result": {"packageId": "ABC123PACKAGE"}})

    client = _client_with_handler(handler)
    result = client.request_document_package(
        "raw-token",
        RequestDocumentPackageRequest(
            type="summary",
            format="CSV",
            query_parameters=DocumentPackageQueryParameters(
                date_from="2015-02-13T14:20Z",
                date_to="2015-02-20T21:30Z",
            ),
            represented_taxpayer_filter_type=2,
            representee_rin="100015840",
        ),
        accept_language="ar",
    )
    assert captured["accept_language"] == "ar"
    assert captured["body"]["type"] == "summary"
    assert captured["body"]["format"] == "CSV"
    assert captured["body"]["representedTaxpayerFilterType"] == 2
    assert captured["body"]["representeeRin"] == "100015840"
    assert result.package_id == "ABC123PACKAGE"


def test_request_document_package_requires_date_range():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json={"packageId": "KLJHH78NJUHQ"})

    client = _client_with_handler(handler)
    with pytest.raises(ValueError, match="date_from and date_to are required"):
        client.request_document_package(TOKEN, type="full")


def test_request_document_package_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.request_document_package(
            TOKEN,
            date_from="2015-02-13T14:20Z",
            date_to="2015-02-20T21:30Z",
        )
    assert exc_info.value.status_code == 401


def test_request_document_package_raises_api_error_on_limit():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "OperationExceedsLimit",
                    "message": "Query matches more documents than allowed",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.request_document_package(
            TOKEN,
            date_from="2015-02-13T14:20Z",
            date_to="2015-02-20T21:30Z",
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "OperationExceedsLimit"


def test_request_document_package_raises_api_error_on_forbidden():
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
        client.request_document_package(
            TOKEN,
            date_from="2015-02-13T14:20Z",
            date_to="2015-02-20T21:30Z",
        )
    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "Forbidden"
