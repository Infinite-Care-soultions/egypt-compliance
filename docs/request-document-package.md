# Request document package

Ask ETA to prepare a downloadable package of invoices you sent or received. The job is **asynchronous**: this call returns a `packageId`. Poll status with [`get_package_requests()`](package-requests.md). A later API downloads the file.

Official API: [Request Document Package](https://sdk.invoicing.eta.gov.eg/einvoicingapi/05-request-document-package/)

`POST /api/v1.0/documentpackages/requests`

HTTP **201** is success. Use Search Documents for interactive paging; use this when you need a bulk extract (JSON, XML, or summary CSV).

Receivers do not get `invalid` or `submitted` documents in the package. If the date range matches too many documents, ETA returns `OperationExceedsLimit` unless you set `truncate_if_exceeded=True` (then the package is cut to the system limit).

## 1. Login

```python
from egypt_compliance import ETAClientFactory

client = ETAClientFactory.create("preprod")  # or "prod"
token = client.login(client_id="your-client-id", client_secret="your-client-secret")
```

## 2. Request

`date_from` and `date_to` are required (UTC). `type` is `full` or `summary`. `format` is `JSON`, `XML`, or `CSV` (`CSV` only with `summary`).

```python
result = client.request_document_package(
    token,
    type="full",
    format="JSON",
    date_from="2015-02-13T14:20Z",
    date_to="2015-02-20T21:30Z",
    document_type_names=["i"],     # i, c, d
    statuses=["valid"],            # valid, invalid, rejected, cancelled
)
print(result.package_id)
```

Optional filters: `products_internal_codes`, `receiver_sender_type` (`0` business, `1` person, `2` foreign), `receiver_sender_id`, `branch_number`, `item_codes`, `truncate_if_exceeded`.

```python
from egypt_compliance import DocumentPackageItemCode

result = client.request_document_package(
    token,
    type="summary",
    format="CSV",
    date_from="2015-02-13T14:20Z",
    date_to="2015-02-20T21:30Z",
    item_codes=[DocumentPackageItemCode(code_value="1000000000003", code_type="GS1")],
    truncate_if_exceeded=True,
)
```

Intermediaries requesting on behalf of a taxpayer:

```python
from egypt_compliance import (
    DocumentPackageQueryParameters,
    RequestDocumentPackageRequest,
)

result = client.request_document_package(
    token,
    RequestDocumentPackageRequest(
        type="full",
        format="JSON",
        query_parameters=DocumentPackageQueryParameters(
            date_from="2015-02-13T14:20Z",
            date_to="2015-02-20T21:30Z",
        ),
        represented_taxpayer_filter_type=2,  # 1 all, 2 specific, 3 me
        representee_rin="100015840",
    ),
)
```

## Errors

| HTTP | Typical `error.code` | What it means |
| --- | --- | --- |
| 400 | `OperationExceedsLimit` | Too many matching documents; narrow the dates or set `truncate_if_exceeded=True` |
| 400 | `BadArgument` | Invalid filters, or `full` with `CSV` |
| 401 | — | Token missing or expired; call `login()` again |
| 403 | `Forbidden` | ERP document retrieval is denied on the profile |

These raise `ETAAuthenticationError` (401) or `ETAAPIError` (other API errors).
