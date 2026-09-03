from decimal import Decimal

import httpx
import pytest

from egypt_compliance import DocumentType, ETAAPIError, ETAAuthenticationError, Token, WorkflowParameter
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)

SUCCESS_BODY = {
    "id": 45,
    "name": "i",
    "description": "Invoice",
    "activeFrom": "2015-02-13T13:15Z",
    "activeTo": None,
    "documentTypeVersions": [
        {
            "id": 454,
            "name": "1.0",
            "description": "Invoice version 1.0",
            "versionNumber": 1.0,
            "status": "published",
            "activeFrom": "2015-02-13T13:15Z",
            "activeTo": "2027-03-01T00:00:00Z",
        }
    ],
    "workflowParameters": [
        {
            "id": 124,
            "parameter": "Rejection time limit in hours",
            "value": 72,
            "activeFrom": "2015-02-13T13:15Z",
            "activeTo": None,
        }
    ],
}


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_get_document_type_sends_id_in_url_and_parses_workflow_parameters():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["accept_language"] = request.headers["Accept-Language"]
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    document_type = client.get_document_type(TOKEN, 45)

    assert captured["url"] == "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documenttypes/45"
    assert captured["method"] == "GET"
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["accept_language"] == "en"
    assert isinstance(document_type, DocumentType)
    assert document_type.id == 45
    assert document_type.name == "i"
    assert len(document_type.document_type_versions) == 1
    assert len(document_type.workflow_parameters) == 1
    param = document_type.workflow_parameters[0]
    assert isinstance(param, WorkflowParameter)
    assert param.id == 124
    assert param.parameter == "Rejection time limit in hours"
    assert param.value == Decimal("72")


def test_get_document_type_unwraps_result_wrapper():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": SUCCESS_BODY})

    client = _client_with_handler(handler)
    document_type = client.get_document_type("raw-token", 45, accept_language="ar")
    assert document_type.id == 45


def test_get_document_type_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.get_document_type(TOKEN, 45)
    assert exc_info.value.status_code == 401


def test_get_document_type_raises_api_error_on_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={
                "error": {
                    "code": "NotFound",
                    "message": "Document type not found",
                    "target": "id",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.get_document_type(TOKEN, 999)
    err = exc_info.value
    assert err.status_code == 404
    assert err.code == "NotFound"
    assert err.target == "id"
