# egypt-compliance

Python SDK for Egyptian Tax Authority (ETA) eInvoicing integration.

Phase 1 supports **login as a taxpayer system**. Phase 2 supports **get document types**. Phase 3 supports **get document type**. Phase 4 supports **get document type version**. Phase 5 supports **get notifications**. Phase 6 supports **create EGS code usage**. Phase 7 supports **search my EGS code usage requests**. Phase 8 supports **request code reuse**. Phase 9 supports **get code details by item code**. Phase 10 supports **update code**. V1 also supports **submit documents**, **invoice JSON modules**, **CAdES-BES signatures**, **cancel document**, **reject document**, **get recent documents**, **search documents**, **request document package**, **get package requests**, and **get document package**.

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

## Invoice documents

Build typed invoice JSON (`to_json()`), sign it, then pass it to `submit_documents()`. Full walkthrough: [docs/invoices.md](docs/invoices.md).

| Class | `documentType` |
| --- | --- |
| `Invoice` | `i` |
| `CreditNote` | `c` |
| `DebitNote` | `d` |
| `ExportInvoice` | `ei` |
| `ExportCreditNote` | `ec` |
| `ExportDebitNote` | `ed` |

```python
from datetime import datetime, timezone
from egypt_compliance import Address, Invoice, InvoiceLine, Issuer, Receiver, UnitValue

invoice = Invoice(
    issuer=Issuer(
        id="100015840",
        name="Issuer Co",
        address=Address(
            branch_id="0",
            country="EG",
            governate="Cairo",
            region_city="Nasr City",
            street="Street 1",
            building_number="10",
        ),
    ),
    receiver=Receiver(
        type="B",
        id="200015840",
        name="Buyer Co",
        address=Address(
            country="EG",
            governate="Giza",
            region_city="Dokki",
            street="Street 2",
            building_number="17",
        ),
    ),
    date_time_issued=datetime(2024, 2, 13, 13, 15, tzinfo=timezone.utc),
    taxpayer_activity_code="4620",
    internal_id="INV-1",
    invoice_lines=[
        InvoiceLine(
            description="Bottle of water",
            item_type="EGS",
            item_code="EG-100015840-1",
            unit_type="EA",
            quantity=1,
            unit_value=UnitValue(amount_egp=100),
            sales_total=100,
            total=114,
            net_total=100,
        )
    ],
    total_sales_amount=100,
    net_amount=100,
    total_amount=114,
)
payload = invoice.to_json()
```

`InvoiceFactory.create("invoice"|"credit_note"|"debit_note"|"export_invoice"|...)` builds the same models.

## Sign documents

Canonicalize invoice JSON and create a Base64 CAdES-BES value. Full walkthrough: [docs/signing.md](docs/signing.md).

```python
from egypt_compliance import SignatureFactory

signer = SignatureFactory.create("pem", certificate="cert.pem", private_key="key.pem")
# Production USB token:
# signer = SignatureFactory.create("pkcs11", pin="12345678", library="eps2003csp11.dll")

result = signer.sign_file("invoice.json")  # or signer.sign_document(invoice.to_json())
print(result.canonical)
print(result.signature)
client.submit_documents(token, result.submission["documents"])
```

## Submit documents

Requires a token from `login()` and signed document JSON (CAdES-BES). Calls `POST /api/v1.0/documentsubmissions`. HTTP **200** and **202** are both success.

Build JSON with the invoice modules, sign with `SignatureFactory`, then submit. Walkthroughs: [docs/invoices.md](docs/invoices.md), [docs/signing.md](docs/signing.md), [docs/submit-documents.md](docs/submit-documents.md).

```python
result = client.submit_documents(
    token,
    [
        {
            "documentType": "i",
            "documentTypeVersion": "1.0",
            "internalID": "PZ-234-A",
            "signatures": [{"type": "I", "value": "<cades-bes-base64>"}],
            # issuer, receiver, invoiceLines, totals, ...
        }
    ],
)
print(result.submission_uuid)
for accepted in result.accepted_documents:
    print(accepted.internal_id, accepted.uuid, accepted.long_id)
for rejected in result.rejected_documents:
    print(rejected.internal_id, rejected.error.message)
```

## Cancel document

Requires a token from `login()` and the ETA document `uuid` from submit. Calls `PUT /api/v1.0/documents/state/{uuid}/state`. Full walkthrough: [docs/cancel-document.md](docs/cancel-document.md).

```python
result = client.cancel_document(token, "F9D425P6DS7D8IU", "Wrong invoice details")
print(result.success)
```

## Reject document

Requires a token from `login()`. The **recipient** rejects a received document by ETA `uuid`. Calls `PUT /api/v1.0/documents/state/{uuid}/state` with `status: rejected`. Full walkthrough: [docs/reject-document.md](docs/reject-document.md).

```python
result = client.reject_document(
    token,
    "F9D425P6DS7D8IU",
    "Received incorrect invoice from the seller",
)
print(result.success)
```

## Get recent documents

Requires a token from `login()`. Calls `GET /api/v1.0/documents/recent`. Full walkthrough: [docs/recent-documents.md](docs/recent-documents.md).

```python
docs = client.get_recent_documents(
    token,
    page_no=1,
    page_size=20,
    direction="Sent",
    status="Valid",
)
for doc in docs:
    print(doc.uuid, doc.internal_id, doc.status)
```

## Search documents

Requires a token from `login()`. Calls `GET /api/v1.0/documents/search`. Prefer this over Get Recent Documents. Full walkthrough: [docs/search-documents.md](docs/search-documents.md).

```python
docs = client.search_documents(
    token,
    page_size=100,
    submission_date_from="2022-11-25T01:59:10Z",
    submission_date_to="2022-12-22T23:59:59Z",
    direction="Sent",
    status="Valid",
)
for doc in docs:
    print(doc.uuid, doc.internal_id, doc.status)
if docs.has_more():
    next_page = client.search_documents(
        token,
        page_size=100,
        submission_date_from="2022-11-25T01:59:10Z",
        submission_date_to="2022-12-22T23:59:59Z",
        direction="Sent",
        status="Valid",
        continuation_token=docs.continuation_token,
    )
```

## Request document package

Requires a token from `login()`. Calls `POST /api/v1.0/documentpackages/requests`. Returns a `packageId` for later download. Full walkthrough: [docs/request-document-package.md](docs/request-document-package.md).

```python
result = client.request_document_package(
    token,
    type="full",
    format="JSON",
    date_from="2015-02-13T14:20Z",
    date_to="2015-02-20T21:30Z",
)
print(result.package_id)
```

## Get package requests

Requires a token from `login()`. Calls `GET /api/v1.0/documentpackages/requests`. Full walkthrough: [docs/package-requests.md](docs/package-requests.md).

```python
packages = client.get_package_requests(token, page_no=1, page_size=20)
for package in packages:
    print(package.package_id, package.status, package.is_expired)
```

## Get document package

Requires a token from `login()` and a `packageId`. Calls `GET /api/v1.0/documentpackages/{rid}` and returns ZIP bytes when ready. Full walkthrough: [docs/document-package.md](docs/document-package.md).

```python
download = client.get_document_package(token, "45KJHHA62D")
if download.ready:
    download.save("invoices.zip")
```

## Environments

| Environment | Identity service | API base |
| --- | --- | --- |
| `preprod` | `https://id.preprod.eta.gov.eg` | `https://api.preprod.invoicing.eta.gov.eg` |
| `prod` | `https://id.eta.gov.eg` | `https://api.invoicing.eta.gov.eg` |

Tokens are typically valid for 3600 seconds. Request a new token before expiry.
