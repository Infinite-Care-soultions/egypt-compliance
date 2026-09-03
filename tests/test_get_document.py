import httpx
import pytest

from egypt_compliance import (
    DocumentExtended,
    ETAAPIError,
    ETAAuthenticationError,
    Token,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)

SUCCESS_BODY = {
    "uuid": "F9D425P6DS7D8IU",
    "submissionUUID": "JU7GH07JNA23N",
    "longId": "LIJAF97HJJKH",
    "internalId": "PZ-234-A",
    "typeName": "i",
    "typeVersionName": "1.0",
    "issuerId": "927398557",
    "issuerName": "My company",
    "receiverId": "087377381",
    "receiverName": "Their company",
    "dateTimeIssued": "2015-02-13T13:15Z",
    "dateTimeReceived": "2015-02-13T14:20Z",
    "totalSales": 10.10,
    "totalDiscount": 50.00,
    "netAmount": 100.70,
    "total": 124.09,
    "status": "valid",
    "lateSubmissionRequestNumber": "927398557-23-1585",
    "transformationStatus": "original",
    "document": {
        "issuer": {"id": "927398557", "name": "My company"},
        "internalID": "PZ-234-A",
        "documentType": "i",
    },
    "validationResults": {
        "status": "Valid",
        "validationSteps": [
            {
                "name": "GS1 code validator",
                "status": "Valid",
            },
            {
                "name": "Signature validator",
                "status": "Invalid",
                "error": {
                    "code": "InvalidSignature",
                    "message": "Document signature is invalid",
                },
            },
        ],
    },
    "additionalMetadata": [
        {
            "fieldName": "PaymentNo",
            "fieldValue": "12-55-889",
            "fieldType": "Text",
            "fieldNameDescEn": "Payment Number",
            "fieldNameDescAr": "الرقم الالكتروني",
        }
    ],
}


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_get_document_fetches_raw_json_and_parses_extended():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["accept_language"] = request.headers["Accept-Language"]
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    result = client.get_document(TOKEN, "F9D425P6DS7D8IU")

    assert captured["method"] == "GET"
    assert captured["url"] == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documents/F9D425P6DS7D8IU/raw"
    )
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["accept_language"] == "en"
    assert isinstance(result, DocumentExtended)
    assert result.uuid == "F9D425P6DS7D8IU"
    assert result.internal_id == "PZ-234-A"
    assert result.status == "valid"
    assert result.transformation_status == "original"
    assert result.document["internalID"] == "PZ-234-A"
    assert result.validation_results is not None
    assert result.validation_results.status == "Valid"
    assert result.validation_results.validation_steps[1].error.code == "InvalidSignature"
    assert result.additional_metadata[0].field_name == "PaymentNo"


def test_get_document_unwraps_result_wrapper():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": SUCCESS_BODY})

    client = _client_with_handler(handler)
    result = client.get_document("raw-token", "F9D425P6DS7D8IU", accept_language="ar")
    assert result.uuid == "F9D425P6DS7D8IU"


def test_get_document_requires_uuid():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    with pytest.raises(ValueError, match="uuid is required"):
        client.get_document(TOKEN, "  ")


def test_get_document_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.get_document(TOKEN, "F9D425P6DS7D8IU")
    assert exc_info.value.status_code == 401


def test_get_document_raises_api_error_on_forbidden():
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
        client.get_document(TOKEN, "F9D425P6DS7D8IU")
    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "Forbidden"
