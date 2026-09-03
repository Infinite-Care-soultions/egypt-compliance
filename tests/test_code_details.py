import httpx
import pytest

from egypt_compliance import ETAAPIError, ETAAuthenticationError, PublishedCodeDetails, Token
from egypt_compliance.client import ETAClient
from egypt_compliance.config import PREPROD

TOKEN = Token(access_token="jwt-token-value", token_type="Bearer", expires_in=3600)

SUCCESS_BODY = {
    "codeID": 942982,
    "itemCode": "EG-113317713-1234",
    "codeName": "Water bottle",
    "codeNameAr": "زجاجة ماء",
    "description": "Water bottle",
    "descriptionAr": "زجاجة ماء",
    "activeFrom": "2021-02-02T00:12:43.00Z",
    "activeTo": "2021-06-02T00:12:43.00Z",
    "ParentCodeLookupValue": "10001400",
    "codeTypeID": 2,
    "CodeTypeLevelID": 8,
    "codeTypeLevelNamePrimaryLang": "Soft Drinks",
    "codeTypeLevelNameSecondaryLang": "لمشروبات الغازية",
    "parentItemCode": "10005854",
    "ParentCodeID": 5942,
}


def _client_with_handler(handler):
    transport = httpx.MockTransport(handler)
    return ETAClient(config=PREPROD, http_client=httpx.Client(transport=transport))


def test_get_code_details_sends_path_params_and_parses_object():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["authorization"] = request.headers["Authorization"]
        captured["accept_language"] = request.headers["Accept-Language"]
        return httpx.Response(200, json=SUCCESS_BODY)

    client = _client_with_handler(handler)
    details = client.get_code_details(TOKEN, "EG-113317713-1234", code_type="EGS")

    assert captured["url"] == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/codetypes/EGS/codes/EG-113317713-1234"
    )
    assert captured["method"] == "GET"
    assert captured["authorization"] == "Bearer jwt-token-value"
    assert captured["accept_language"] == "en"
    assert isinstance(details, PublishedCodeDetails)
    assert details.code_id == 942982
    assert details.item_code == "EG-113317713-1234"
    assert details.code_name == "Water bottle"
    assert details.code_name_ar == "زجاجة ماء"
    assert details.parent_code_lookup_value == "10001400"
    assert details.code_type_id == 2
    assert details.code_type_level_id == 8
    assert details.parent_item_code == "10005854"
    assert details.parent_code_id == 5942


def test_get_code_details_unwraps_result_wrapper():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": SUCCESS_BODY})

    client = _client_with_handler(handler)
    details = client.get_code_details("raw-token", "EG-113317713-1234", accept_language="ar")
    assert details.code_id == 942982


def test_get_code_details_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "Unauthorized", "message": "Token expired"}},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAuthenticationError) as exc_info:
        client.get_code_details(TOKEN, "EG-113317713-1234")
    assert exc_info.value.status_code == 401


def test_get_code_details_raises_api_error_when_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={
                "error": {
                    "code": "NotFound",
                    "message": "Code not found",
                    "target": "itemCode",
                }
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(ETAAPIError) as exc_info:
        client.get_code_details(TOKEN, "EG-missing")
    err = exc_info.value
    assert err.status_code == 404
    assert err.code == "NotFound"
    assert err.target == "itemCode"
