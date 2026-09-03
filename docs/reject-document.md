# Reject document

Reject an invalid invoice that **you received**. Only the recipient can reject, and only once, inside the allowed window.

Official API: [Reject Document](https://sdk.invoicing.eta.gov.eg/einvoicingapi/03-reject-document/)

`PUT /api/v1.0/documents/state/{uuid}/state`

The window is a workflow parameter on the document type (`get_document_type()`). After that window, ask the issuer to send a credit note. Issuers cancel their own documents; receivers reject incoming ones.

## 1. Login

```python
from egypt_compliance import ETAClientFactory

client = ETAClientFactory.create("preprod")  # or "prod"
token = client.login(client_id="your-client-id", client_secret="your-client-secret")
```

## 2. Reject

`uuid` is the ETA document ID of the received invoice. Status must be `rejected`.

```python
result = client.reject_document(
    token,
    "F9D425P6DS7D8IU",
    "Received incorrect invoice from the seller",
)
print(result.success)
```

Or with the request model:

```python
from egypt_compliance import RejectDocumentRequest

result = client.reject_document(
    token,
    "F9D425P6DS7D8IU",
    RejectDocumentRequest(reason="Received incorrect invoice from the seller"),
)
```

HTTP **200** is success. The body is optional.

## Errors

| HTTP | Typical `error.code` | What it means |
| --- | --- | --- |
| 400 | `OperationPeriodOver` | Rejection window has expired; ask the issuer for a credit note |
| 400 | `IncorrectState` | Document is not Valid; reject is not allowed |
| 400 | `ActiveReferencingDocuments` | Reject referencing credit/debit notes first |
| 400 | `TryingToRejectFreezedDocument` | Document is frozen |
| 401 | — | Token missing or expired; call `login()` again |
| 403 | `Forbidden` | You are not the recipient, or ERP rejection is denied |

These raise `ETAAuthenticationError` (401) or `ETAAPIError` (other API errors).
