from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from egypt_compliance import (
    ETAAPIError,
    ETAAuthenticationError,
    PackageRequestsQuery,
    Token,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)

SUCCESS_BODY = {
    "result": [
        {
            "packageId": "KLJHH78NJUHQ",
            "submissionDate": "2015-02-13T14:20Z",
            "status": 2,
            "type": 1,
            "format": 3,
            "requestorTypeId": 2,
            "requestorTaxpayerRIN": "115519213",
            "requestorTaxpayerName": "Company Name",
            "deletionDate": "2015-02-23T14:20Z",
            "isExpired": False,
            "queryParameters": {
                "dateFrom": "2015-02-13T14:20Z",
                "dateTo": "2015-02-20T21:30Z",
                "documentTypeName": "i",
                "statuses": "valid,rejected",
                "productsInternalCodes": "8383S",
                "receiverSenderType": 0,
                "receiverSenderId": "345987378",
                "branchNumber": "0",
                "itemCodes": '{"ItemCodes": [{"CodeValue": "1000000000003","CodeType": "GS1"}]}',
            },
        }
    ],
    "metadata": {"totalPages": 23, "totalCount": 157},
}


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_get_package_requests_sends_paging_and_parses_result():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["query"] = parse_qs(urlparse(str(request.url)).query)
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    result = client.get_package_requests(TOKEN, page_no=3, page_size=20)

    assert captured["method"] == "GET"
    assert captured["url"].startswith(
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documentpackages/requests"
    )
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["query"]["pageNo"] == ["3"]
    assert captured["query"]["pageSize"] == ["20"]

    assert len(result) == 1
    package = result.result[0]
    assert package.package_id == "KLJHH78NJUHQ"
    assert package.status == 2
    assert package.type == 1
    assert package.format == 3
    assert package.requestor_taxpayer_rin == "115519213"
    assert package.is_expired is False
    assert package.query_parameters is not None
    assert package.query_parameters.document_type_name == "i"
    assert package.query_parameters.statuses == ["valid", "rejected"]
    assert package.query_parameters.products_internal_codes == ["8383S"]
    assert package.query_parameters.item_codes[0].code_value == "1000000000003"
    assert package.query_parameters.item_codes[0].code_type == "GS1"
    assert result.metadata.total_count == 157
    assert result.metadata.total_pages == 23


def test_get_package_requests_accepts_query_model_and_metadata_list():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["query"] = parse_qs(urlparse(str(request.url)).query)
        captured["accept_language"] = request.headers["Accept-Language"]
        return httpx.Response(
            200,
            json={
                "result": SUCCESS_BODY["result"],
                "metadata": [{"totalPages": 1, "totalCount": 1}],
            },
        )

    client = _client_with_handler(handler)
    result = client.get_package_requests(
        "raw-token",
        PackageRequestsQuery(page_no=1, page_size=10),
        accept_language="ar",
    )
    assert captured["accept_language"] == "ar"
    assert captured["query"]["pageNo"] == ["1"]
    assert captured["query"]["pageSize"] == ["10"]
    assert result.metadata is not None
    assert result.metadata.total_count == 1
    assert [item.package_id for item in result] == ["KLJHH78NJUHQ"]


def test_get_package_requests_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.get_package_requests(TOKEN)
    assert exc_info.value.status_code == 401


def test_get_package_requests_raises_api_error_on_forbidden():
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
        client.get_package_requests(TOKEN)
    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "Forbidden"
