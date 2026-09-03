# Get document

Retrieve the full source of one invoice (JSON) plus ETA metadata: status, validation results, and extra fields.

Official API: [Get Document](https://sdk.invoicing.eta.gov.eg/einvoicingapi/08-get-document/)

`GET /api/v1.0/documents/{uuid}/raw`

`uuid` comes from submit (`accepted_documents[].uuid`) or from [`get_recent_documents()`](recent-documents.md) / [`search_documents()`](search-documents.md). For a PDF, use [`get_document_printout()`](document-printout.md).

Receivers can only load `Valid`, `Rejected`, and `Cancelled`. If the document is still `submitted` or `invalid`, ETA returns not found. Issuers can load any status.

This SDK requests **JSON**. Transformed XML→JSON (or the reverse) sets `transformation_status` to `transformed` and the signature will not verify.

## 1. Login

```python
from egypt_compliance import ETAClientFactory

client = ETAClientFactory.create("preprod")  # or "prod"
token = client.login(client_id="your-client-id", client_secret="your-client-secret")
```

## 2. Get

```python
doc = client.get_document(token, "F9D425P6DS7D8IU")
print(doc.uuid, doc.internal_id, doc.status, doc.total)
print(doc.transformation_status)
print(doc.document["internalID"])
if doc.validation_results:
    print(doc.validation_results.status)
    for step in doc.validation_results.validation_steps:
        print(step.name, step.status)
```

## Errors

| HTTP | Typical `error.code` | What it means |
| --- | --- | --- |
| 401 | — | Token missing or expired; call `login()` again |
| 403 | `Forbidden` | ERP document retrieval is denied on the profile |
| 404 | — | Unknown uuid, or a receiver asked for a submitted/invalid document |

These raise `ETAAuthenticationError` (401) or `ETAAPIError` (other API errors).
