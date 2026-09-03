from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from egypt_compliance import (
    ETAAPIError,
    ETAAuthenticationError,
    RecentDocumentsQuery,
    Token,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)

SUCCESS_BODY = {
    "result": [
        {
            "uuid": "42S512YACQBRSRHYKBXBTGQG22",
            "submissionUUID": "XYE60M8ENDWA7V9TKBXBTGQG10",
            "longId": "YQH73576FY9VR57B",
            "internalId": "PZ-234-A",
            "typeName": "i",
            "typeVersionName": "1.0",
            "issuerId": "927398557",
            "issuerName": "My company",
            "issuerType": "B",
            "receiverId": "087377381",
            "receiverName": "Their company",
            "receiverType": "B",
            "dateTimeIssued": "2015-02-13T13:15Z",
            "dateTimeReceived": "2015-02-13T14:20Z",
            "totalSales": 10.10,
            "totalDiscount": 50.00,
            "netAmount": 100.70,
            "total": 124.09,
            "status": "Valid",
            "freezeStatus": {"frozen": False, "type": 0, "scope": 0},
        }
    ],
    "metadata": {
        "totalPages": 23,
        "totalCount": 157,
        "queryContainsCompleteResultSet": True,
        "remainingRecordsCount": 0,
    },
}


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_get_recent_documents_sends_filters_and_parses_result():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["query"] = parse_qs(urlparse(str(request.url)).query)
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    result = client.get_recent_documents(
        TOKEN,
        page_no=3,
        page_size=20,
        submission_date_from=datetime(2022, 11, 25, 1, 59, 10, tzinfo=timezone.utc),
        submission_date_to="2022-12-22T23:59:59Z",
        direction="Sent",
        status="Valid",
        document_type="i",
        receiver_type="B",
        receiver_id="327389457",
    )

    assert captured["method"] == "GET"
    assert captured["url"].startswith(
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documents/recent"
    )
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["query"]["pageNo"] == ["3"]
    assert captured["query"]["pageSize"] == ["20"]
    assert captured["query"]["submissionDateFrom"] == ["2022-11-25T01:59:10Z"]
    assert captured["query"]["submissionDateTo"] == ["2022-12-22T23:59:59Z"]
    assert captured["query"]["direction"] == ["Sent"]
    assert captured["query"]["status"] == ["Valid"]
    assert captured["query"]["documentType"] == ["i"]
    assert captured["query"]["receiverType"] == ["B"]
    assert captured["query"]["receiverId"] == ["327389457"]

    assert len(result) == 1
    doc = result.result[0]
    assert doc.uuid == "42S512YACQBRSRHYKBXBTGQG22"
    assert doc.internal_id == "PZ-234-A"
    assert doc.status == "Valid"
    assert doc.total == 124.09
    assert doc.freeze_status is not None
    assert doc.freeze_status.frozen is False
    assert result.metadata.total_count == 157
    assert result.metadata.query_contains_complete_result_set is True


def test_get_recent_documents_accepts_query_model():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["query"] = parse_qs(urlparse(str(request.url)).query)
        captured["accept_language"] = request.headers["Accept-Language"]
        return httpx.Response(200, json={"result": []})

    client = _client_with_handler(handler)
    result = client.get_recent_documents(
        "raw-token",
        RecentDocumentsQuery(direction="Received", issuer_type="B", page_no=1),
        accept_language="ar",
    )
    assert captured["accept_language"] == "ar"
    assert captured["query"]["direction"] == ["Received"]
    assert captured["query"]["issuerType"] == ["B"]
    assert captured["query"]["pageNo"] == ["1"]
    assert list(result) == []


def test_get_recent_documents_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.get_recent_documents(TOKEN)
    assert exc_info.value.status_code == 401


def test_get_recent_documents_raises_api_error_on_forbidden():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "error": {
                    "code": "forbidden",
                    "message": "B2B Deny ERP Document Retrieval",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.get_recent_documents(TOKEN)
    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "forbidden"
