# Cancel document

Cancel a previously issued invoice (or other eInvoicing document) within the allowed cancellation window.

Official API: [Cancel Document](https://sdk.invoicing.eta.gov.eg/einvoicingapi/02-cancel-document/)

`PUT /api/v1.0/documents/state/{uuid}/state`

Use this when a mistake is noticed soon after submit. The window is a workflow parameter on the document type (`get_document_type()`). After that window, issue a credit note instead of cancelling. Recipients [reject](reject-document.md) incoming invoices; issuers cancel their own.

## 1. Login

```python
from egypt_compliance import ETAClientFactory

client = ETAClientFactory.create("preprod")  # or "prod"
token = client.login(client_id="your-client-id", client_secret="your-client-secret")
```

## 2. Cancel

`uuid` is the ETA document ID returned in `accepted_documents[].uuid` from [`submit_documents()`](submit-documents.md). Status must be `cancelled`.

ETA reasons: **Wrong buyer details** or **Wrong invoice details**.

```python
result = client.cancel_document(
    token,
    "F9D425P6DS7D8IU",
    "Wrong invoice details",
)
print(result.success)
```

Or with the request model:

```python
from egypt_compliance import CancelDocumentRequest

result = client.cancel_document(
    token,
    "F9D425P6DS7D8IU",
    CancelDocumentRequest(reason="Wrong buyer details"),
)
```

HTTP **200** is success. The body is optional.

## Errors

| HTTP | Typical `error.code` | What it means |
| --- | --- | --- |
| 400 | `OperationPeriodOver` | Cancellation window has expired; use a credit note |
| 400 | `IncorrectState` | Document is already rejected/invalid; cancel is not allowed |
| 400 | `ActiveReferencingDocuments` | Cancel referencing credit/debit notes first |
| 400 | `TryingToCancelFreezedDocument` | Document is frozen |
| 401 | — | Token missing or expired; call `login()` again |
| 403 | `Forbidden` | Not the issuer, or ERP cancellation is denied |

These raise `ETAAuthenticationError` (401) or `ETAAPIError` (other API errors).
