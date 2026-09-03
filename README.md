# egypt-compliance

Python SDK for Egyptian Tax Authority (ETA) eInvoicing integration.

Phase 1 supports **login as a taxpayer system**. Phase 2 supports **get document types**. Phase 3 supports **get document type**. Phase 4 supports **get document type version**. Phase 5 supports **get notifications**. Phase 6 supports **create EGS code usage**. Phase 7 supports **search my EGS code usage requests**. Phase 8 supports **request code reuse**. Phase 9 supports **get code details by item code**. Phase 10 supports **update code**.

## Install

The project folder name contains a space (`egypt compliance`). Run commands **from this folder**, and quote the path if you install from a parent directory.

```powershell
python -m pip install .
```

Editable install for development (PowerShell: use single quotes so `[dev]` is not treated as a glob):

```powershell
python -m pip install -e '.[dev]'
```

From a parent folder, quote the full path:

```powershell
python -m pip install -e "Packag Path"
```


## Login

```python
from egypt_compliance import ETAClientFactory

client = ETAClientFactory.create("preprod")
token = client.login(client_id="client_id", client_secret="client_secret")
print(token.access_token)
print(token.expires_in)

types = client.get_document_types(token)
for document_type in types:
    print(document_type.name, document_type.description)
    for version in document_type.document_type_versions:
        print(version.name, version.status)
```

Production:

```python
client = ETAClientFactory.create("prod")
```

Intermediary login (optional `onbehalfof` header):

```python
token = client.login(
    client_id="your-client-id",
    client_secret="your-client-secret",
    on_behalf_of="100015840",
)
```

## Get document types

Requires a token from `login()`. Calls `GET /api/v1.0/documenttypes`.

```python
types = client.get_document_types(token, accept_language="en")
for document_type in types:
    print(document_type.id, document_type.name, document_type.description)
```

Use `accept_language="ar"` for Arabic descriptions when the API supports it.

## Get document type

Requires a token from `login()` and a document type `id` from `get_document_types()`. Calls `GET /api/v1.0/documenttypes/{id}`.

```python
document_type = client.get_document_type(token, 45)
print(document_type.name, document_type.description)
for parameter in document_type.workflow_parameters:
    print(parameter.parameter, parameter.value)
```

## Get document type version

Requires a token, a document type `id`, and a version `id` (`vid`) from `get_document_types()` or `get_document_type()`. Calls `GET /api/v1.0/documenttypes/{id}/versions/{vid}`.

```python
version = client.get_document_type_version(token, 45, 454)
print(version.type_name, version.name, version.status)
json_schema = version.decode_json_schema()
```

`jsonSchema` and `xmlSchema` are Base64-encoded in the API response. Use `decode_json_schema()` / `decode_xml_schema()` to get the raw schema text.

## Get notifications

Requires a token from `login()`. Calls `GET /api/v1.0/notifications/taxpayer` with optional filters and paging.

```python
from egypt_compliance import NotificationType

notifications = client.get_notifications(
    token,
    type=NotificationType.DOCUMENT_RECEIVED,
    status="delivered",
    page_no=1,
    page_size=20,
)
print(notifications.metadata.total_count)
for notification in notifications:
    print(notification.notification_id, notification.type_name, notification.final_message)
```

Optional filters: `date_from`, `date_to`, `type`, `language` (`en`/`ar`), `status` (`pending`, `batched`, `delivered`, `error`), `channel` (`sms`, `email`, `push`, `system`), `page_no`, `page_size`.

## Create EGS code usage

Requires a token from `login()`. Calls `POST /api/v1.0/codetypes/requests/codes` to register taxpayer internal codes. ETA must approve the request before the code can be used on invoices.

`itemCode` format: `EG-TaxpayerID-InternalCode`. `parentCode` is a level-4 GPC code.

```python
from datetime import datetime, timezone
from egypt_compliance import EGSCodeUsageItem

result = client.create_egs_code_usage(
    token,
    [
        EGSCodeUsageItem(
            parent_code="10000051",
            item_code="EG-674859545-123456784",
            code_name="bottle of water",
            code_name_ar="قارورة ماء",
            active_from=datetime(2025, 2, 21, tzinfo=timezone.utc),
            description="Glass bottle",
        )
    ],
)
print(result.success)
```

## Search my EGS code usage requests

Requires a token from `login()`. Calls `GET /api/v1.0/codetypes/requests/my` to list create-new-code and code-reuse requests.

```python
from egypt_compliance import EGSRequestStatus, EGSRequestType

requests = client.search_egs_code_usage_requests(
    token,
    status=EGSRequestStatus.SUBMITTED,
    request_type=EGSRequestType.NEW,
    page_no=1,
    page_size=20,
)
for request in requests:
    print(request.code_usage_request_id, request.item_code, request.status)
```

Optional filters: `item_code`, `code_name`, `code_description`, `parent_level_name`, `parent_item_code`, `active_from`, `active_to`, `active`, `status` (`Submitted`, `Approved`, `Rejected`), `request_type` (`New`, `Reusage`), `order_directions` (`Descending`, `Ascending`), `page_no`, `page_size`.

## Request code reuse

Requires a token from `login()`. Calls `PUT /api/v1.0/codetypes/requests/codeusages` to request reuse of an existing EGS or GS1 code. ETA must approve the request before you can use the code on invoices.

```python
from egypt_compliance import CodeReuseItem

result = client.request_code_reuse(
    token,
    [
        CodeReuseItem(
            code_type="EGS",
            item_code="EG-100000053-10011",
            comment="Code that I already use in my factory",
        )
    ],
)
print(result.success)
```

## Get code details by item code

Requires a token from `login()`. Calls `GET /api/v1.0/codetypes/{codeType}/codes/{itemCode}` for a published EGS or GS1 code.

```python
details = client.get_code_details(token, "EG-113317713-1234", code_type="EGS")
print(details.code_id, details.code_name, details.parent_item_code)
```

## Update code

Requires a token from `login()`. Calls `PUT /api/v1.0/codetypes/{codeType}/codes/{itemCode}` to update an **Approved** published code.

Optional body fields: English/Arabic description, `active_to`, and `linked_code`.

```python
from datetime import datetime, timezone

result = client.update_code(
    token,
    "EG-113317713-1234",
    code_type="EGS",
    code_description_primary_lang="Water bottle, 600 mg, plastic bottle",
    code_description_secondary_lang="قاروره مياه يلاستيكية",
    active_to=datetime(2021, 5, 21, 23, 59, tzinfo=timezone.utc),
    linked_code="EG-674859545-9875",
)
print(result.success)
```

## Environments

| Environment | Identity service | API base |
| --- | --- | --- |
| `preprod` | `https://id.preprod.eta.gov.eg` | `https://api.preprod.invoicing.eta.gov.eg` |
| `prod` | `https://id.eta.gov.eg` | `https://api.invoicing.eta.gov.eg` |

Tokens are typically valid for 3600 seconds. Request a new token before expiry.
