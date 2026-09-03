from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from egypt_compliance import (
    ETAAPIError,
    ETAAuthenticationError,
    GetSubmissionQuery,
    Token,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)

SUCCESS_BODY = {
    "uuid": "HJSD135P2S7D8IU",
    "documentCount": 234,
    "dateTimeReceived": "2015-02-13T14:20Z",
    "overallStatus": "valid",
    "documentSummary": [
        {
            "uuid": "F9D425P6DS7D8IU",
            "longId": "LIJAF97HJJKH",
            "internalId": "PZ-234-A",
            "typeName": "i",
            "typeVersionName": "1.0",
            "issuerId": "927398557",
            "issuerName": "My company",
            "receiverId": "087377381",
            "receiverName": "Their company",
            "dateTimeIssued": "2015-02-13T13:15Z",
            "total": 124.09,
            "status": "valid",
            "lateSubmissionRequestNumber": "927398557-23-1585",
        }
    ],
    "documentSummaryMetadata": {"totalPages": 23, "totalCount": 157},
}


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_get_submission_sends_paging_and_parses_result():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["query"] = parse_qs(urlparse(str(request.url)).query)
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    result = client.get_submission(TOKEN, "HJSD135P2S7D8IU", page_no=3, page_size=20)

    assert captured["method"] == "GET"
    assert captured["url"].startswith(
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documentsubmissions/HJSD135P2S7D8IU"
    )
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["query"]["pageNo"] == ["3"]
    assert captured["query"]["pageSize"] == ["20"]
    assert result.uuid == "HJSD135P2S7D8IU"
    assert result.document_count == 234
    assert result.overall_status == "valid"
    assert len(result) == 1
    doc = result.document_summary[0]
    assert doc.uuid == "F9D425P6DS7D8IU"
    assert doc.internal_id == "PZ-234-A"
    assert doc.status == "valid"
    assert result.document_summary_metadata is not None
    assert result.document_summary_metadata.total_count == 157
    assert result.document_summary_metadata.total_pages == 23


def test_get_submission_accepts_query_model_and_metadata_list():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["query"] = parse_qs(urlparse(str(request.url)).query)
        captured["accept_language"] = request.headers["Accept-Language"]
        return httpx.Response(
            200,
            json={
                **SUCCESS_BODY,
                "documentSummaryMetadata": [{"totalPages": 1, "totalCount": 1}],
            },
        )

    client = _client_with_handler(handler)
    result = client.get_submission(
        "raw-token",
        "HJSD135P2S7D8IU",
        GetSubmissionQuery(page_no=1, page_size=10),
        accept_language="ar",
    )
    assert captured["accept_language"] == "ar"
    assert captured["query"]["pageNo"] == ["1"]
    assert captured["query"]["pageSize"] == ["10"]
    assert result.document_summary_metadata is not None
    assert result.document_summary_metadata.total_count == 1
    assert [item.internal_id for item in result] == ["PZ-234-A"]


def test_get_submission_requires_uuid():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    with pytest.raises(ValueError, match="uuid is required"):
        client.get_submission(TOKEN, "  ")


def test_get_submission_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.get_submission(TOKEN, "HJSD135P2S7D8IU")
    assert exc_info.value.status_code == 401


def test_get_submission_raises_api_error_on_forbidden():
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
        client.get_submission(TOKEN, "HJSD135P2S7D8IU")
    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "Forbidden"
