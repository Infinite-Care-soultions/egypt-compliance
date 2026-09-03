import base64
from decimal import Decimal

import httpx
import pytest

from egypt_compliance import (
    DocumentTypeVersionDetail,
    ETAAPIError,
    ETAAuthenticationError,
    Token,
)
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)
JSON_SCHEMA = '{"type":"object"}'
XML_SCHEMA = "<xs:schema/>"

SUCCESS_BODY = {
    "typeName": "i",
    "name": "1.0",
    "description": "Invoice version 1.0",
    "versionNumber": 1.0,
    "status": "published",
    "activeFrom": "2015-02-13T13:15Z",
    "activeTo": None,
    "jsonSchema": base64.b64encode(JSON_SCHEMA.encode("utf-8")).decode("ascii"),
    "xmlSchema": base64.b64encode(XML_SCHEMA.encode("utf-8")).decode("ascii"),
}


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_get_document_type_version_sends_ids_and_parses_schemas():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["accept_language"] = request.headers["Accept-Language"]
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    version = client.get_document_type_version(TOKEN, 45, 454)

    assert captured["url"] == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documenttypes/45/versions/454"
    )
    assert captured["method"] == "GET"
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["accept_language"] == "en"
    assert isinstance(version, DocumentTypeVersionDetail)
    assert version.type_name == "i"
    assert version.name == "1.0"
    assert version.version_number == Decimal("1.0")
    assert version.status == "published"
    assert version.decode_json_schema() == JSON_SCHEMA
    assert version.decode_xml_schema() == XML_SCHEMA


def test_get_document_type_version_unwraps_result_wrapper():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": SUCCESS_BODY})

    client = _client_with_handler(handler)
    version = client.get_document_type_version("raw-token", 45, 454, accept_language="ar")
    assert version.type_name == "i"


def test_get_document_type_version_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.get_document_type_version(TOKEN, 45, 454)
    assert exc_info.value.status_code == 401


def test_get_document_type_version_raises_api_error_on_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={
                "error": {
                    "code": "NotFound",
                    "message": "Document type version not found",
                    "target": "vid",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.get_document_type_version(TOKEN, 45, 999)
    err = exc_info.value
    assert err.status_code == 404
    assert err.code == "NotFound"
    assert err.target == "vid"
