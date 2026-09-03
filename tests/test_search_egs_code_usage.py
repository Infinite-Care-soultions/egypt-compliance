from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from egypt_compliance import (
    EGSRequestStatus,
    EGSRequestType,
    ETAAPIError,
    ETAAuthenticationError,
    OrderDirection,
    SearchEGSCodeUsageQuery,
    Token,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)

SUCCESS_ITEM = {
    "codeUsageRequestID": 58985,
    "codeTypeName": "EGS",
    "codeID": 942982,
    "itemCode": "EG-113317713-1234",
    "codeName": "water bottle",
    "description": "Water bottle, 600 mg, plastic bottle",
    "parentCodeID": 302982,
    "parentItemCode": "10006358",
    "parentLevelName": "EGS Level 4 Code - Brick",
    "levelName": "EGS Level 5 Code",
    "requestCreationDateTimeUtc": "2021-02-02T00:12:43.00Z",
    "codeCreationDateTimeUtc": "2021-02-02T00:12:43.900Z",
    "activeFrom": "2021-02-02T00:12:43.00Z",
    "activeTo": "2021-06-02T00:12:43.00Z",
    "active": True,
    "status": "Approved",
    "ownerTaxpayer": {"rin": "113317713", "name": "Samsung", "nameAr": "سامسونج"},
    "requesterTaxpayer": {"rin": "113317713", "name": "Apple", "nameAr": "أبل"},
    "codeCategorization": {"name": "Food/Beverage/Tobacco", "nameAr": "الأطعمة/المشروبات/التبغ"},
}


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_search_egs_code_usage_requests_sends_filters_and_parses_array():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["query"] = parse_qs(urlparse(str(request.url)).query)
        return httpx.Response(200, json=[SUCCESS_ITEM])

    client = _client_with_handler(handler)
    result = client.search_egs_code_usage_requests(
        TOKEN,
        item_code="EG-113317713-1234",
        code_name="water bottle",
        status=EGSRequestStatus.APPROVED,
        request_type=EGSRequestType.NEW,
        order_directions=OrderDirection.DESCENDING,
        active=True,
        active_from=datetime(2021, 3, 21, tzinfo=timezone.utc),
        page_no=3,
        page_size=20,
    )

    assert captured["method"] == "GET"
    assert captured["url"].startswith(
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/codetypes/requests/my"
    )
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["query"]["ItemCode"] == ["EG-113317713-1234"]
    assert captured["query"]["CodeName"] == ["water bottle"]
    assert captured["query"]["Status"] == ["Approved"]
    assert captured["query"]["RequestType"] == ["New"]
    assert captured["query"]["OrderDirections"] == ["Descending"]
    assert captured["query"]["Active"] == ["true"]
    assert captured["query"]["ActiveFrom"] == ["2021-03-21T00:00:00Z"]
    assert captured["query"]["Pn"] == ["3"]
    assert captured["query"]["Ps"] == ["20"]

    assert len(result) == 1
    item = result.result[0]
    assert item.code_usage_request_id == 58985
    assert item.item_code == "EG-113317713-1234"
    assert item.status == "Approved"
    assert item.owner_taxpayer is not None
    assert item.owner_taxpayer.rin == "113317713"
    assert item.code_categorization is not None
    assert item.code_categorization.name == "Food/Beverage/Tobacco"


def test_search_egs_code_usage_requests_accepts_query_model_and_result_wrapper():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": [SUCCESS_ITEM]})

    client = _client_with_handler(handler)
    result = client.search_egs_code_usage_requests(
        "raw-token",
        SearchEGSCodeUsageQuery(status="Submitted", page_no=1),
        accept_language="ar",
    )
    assert [item.code_usage_request_id for item in result] == [58985]


def test_search_egs_code_usage_requests_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.search_egs_code_usage_requests(TOKEN)
    assert exc_info.value.status_code == 401


def test_search_egs_code_usage_requests_raises_api_error_on_bad_request():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "BadArgument",
                    "message": "Invalid page size",
                    "target": "Ps",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.search_egs_code_usage_requests(TOKEN, page_size=9999)
    err = exc_info.value
    assert err.status_code == 400
    assert err.code == "BadArgument"
    assert err.target == "Ps"
