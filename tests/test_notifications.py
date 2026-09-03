from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from egypt_compliance import (
    ETAAPIError,
    ETAAuthenticationError,
    Notification,
    NotificationQuery,
    NotificationType,
    Token,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)

SUCCESS_BODY = {
    "result": [
        {
            "notificationId": "73DKLJHH78NJUHQ",
            "receivedDateTime": "2015-02-13T14:20Z",
            "deliveredDateTime": "2015-02-13T14:23Z",
            "typeId": 6,
            "typeName": "Document Received",
            "finalMessage": "Taxpayer 893838273 has received new documents",
            "channel": "system",
            "address": "test@test.eg",
            "language": "en",
            "status": "delivered",
            "deliveryAttempts": [
                {
                    "attemptDateTime": "2015-02-13T14:20Z",
                    "status": "delivered",
                    "statusDetails": None,
                }
            ],
        }
    ],
    "metadata": {"totalPages": 23, "totalCount": 157},
}


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_get_notifications_sends_filters_and_parses_result():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["query"] = parse_qs(urlparse(str(request.url)).query)
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    result = client.get_notifications(
        TOKEN,
        date_from=datetime(2015, 2, 13, 14, 20, tzinfo=timezone.utc),
        date_to="2015-02-14T14:20Z",
        type=NotificationType.DOCUMENT_RECEIVED,
        language="en",
        status="delivered",
        channel="system",
        page_no=3,
        page_size=20,
    )

    assert captured["method"] == "GET"
    assert captured["url"].startswith(
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/notifications/taxpayer"
    )
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["query"]["dateFrom"] == ["2015-02-13T14:20:00Z"]
    assert captured["query"]["dateTo"] == ["2015-02-14T14:20Z"]
    assert captured["query"]["type"] == ["6"]
    assert captured["query"]["language"] == ["en"]
    assert captured["query"]["status"] == ["delivered"]
    assert captured["query"]["channel"] == ["system"]
    assert captured["query"]["pageNo"] == ["3"]
    assert captured["query"]["pageSize"] == ["20"]

    assert len(result) == 1
    assert result.metadata is not None
    assert result.metadata.total_pages == 23
    assert result.metadata.total_count == 157
    notification = result.result[0]
    assert isinstance(notification, Notification)
    assert notification.notification_id == "73DKLJHH78NJUHQ"
    assert notification.type_id == "6"
    assert notification.type_name == "Document Received"
    assert notification.status == "delivered"
    assert notification.delivery_attempts[0].status == "delivered"


def test_get_notifications_accepts_query_model_and_metadata_list():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "result": SUCCESS_BODY["result"],
                "metadata": [{"totalPages": 1, "totalCount": 1}],
            },
        )

    client = _client_with_handler(handler)
    result = client.get_notifications(
        "raw-token",
        NotificationQuery(page_no=1, page_size=10, type=2),
        accept_language="ar",
    )
    assert result.metadata is not None
    assert result.metadata.total_count == 1
    assert [item.notification_id for item in result] == ["73DKLJHH78NJUHQ"]


def test_get_notifications_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.get_notifications(TOKEN)
    assert exc_info.value.status_code == 401


def test_get_notifications_raises_api_error_on_bad_request():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "BadArgument",
                    "message": "Invalid page size",
                    "target": "pageSize",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.get_notifications(TOKEN, page_size=9999)
    err = exc_info.value
    assert err.status_code == 400
    assert err.code == "BadArgument"
    assert err.target == "pageSize"
