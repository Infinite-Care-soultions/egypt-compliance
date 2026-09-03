# Submit documents

Submit one or more **already signed** invoices, credit notes, or debit notes to ETA eInvoicing.

Official API: [Submit Documents](https://sdk.invoicing.eta.gov.eg/einvoicingapi/01-submit-documents/)

`POST /api/v1.0/documentsubmissions`

This SDK sends **JSON** (`Content-Type: application/json`). Sign each document with [`SignatureFactory`](signing.md) (CAdES-BES), then pass the signed JSON objects to `submit_documents()`.

## 1. Login

```python
from egypt_compliance import ETAClientFactory

client = ETAClientFactory.create("preprod")  # or "prod"
token = client.login(client_id="your-client-id", client_secret="your-client-secret")
```

Intermediary login (optional):

```python
token = client.login(
    client_id="your-client-id",
    client_secret="your-client-secret",
    on_behalf_of="100015840",
)
```

## 2. Sign documents

Use [`SignatureFactory`](signing.md) (PEM, PFX, or PKCS#11 USB token). The signer canonicalizes the JSON (no `signatures`), creates CAdES-BES, and attaches `signatures`.

## 3. Submit

```python
result = client.submit_documents(
    token,
    [
        {
            "issuer": {"type": "B", "id": "100015840", "name": "Issuer Co"},
            "receiver": {"type": "B", "id": "200015840", "name": "Buyer Co"},
            "documentType": "i",
            "documentTypeVersion": "1.0",
            "dateTimeIssued": "2024-02-13T13:15:00Z",
            "internalID": "PZ-234-A",
            "invoiceLines": [...],
            "signatures": [{"type": "I", "value": "<cades-bes-base64>"}],
        }
    ],
)
```

The request body is `{ "documents": [ ... ] }`. The list must contain at least one document. Dict payloads are posted as-is so the signed structure is preserved.

## 4. Map ETA IDs back to your ERP

ETA may return **202** (accepted for further processing) or **200**. Both are treated as success.

```python
print(result.submission_uuid)

for accepted in result.accepted_documents:
    print(accepted.internal_id, accepted.uuid, accepted.long_id)

for rejected in result.rejected_documents:
    print(rejected.internal_id, rejected.error.code, rejected.error.message)
```

| Field | Meaning |
| --- | --- |
| `submission_uuid` | Submission ID (`submissionUUID`) |
| `accepted_documents[].uuid` | ETA document ID |
| `accepted_documents[].long_id` | Public/print long ID |
| `accepted_documents[].internal_id` | Your `internalID` from the submitted document |
| `rejected_documents[].error` | Why that document was not accepted |

Store `uuid` / `long_id` against the ERP invoice number (`internal_id`). Use them later to retrieve, [cancel](cancel-document.md), or follow validation results. Poll the batch with [`get_submission()`](get-submission.md) using `submission_uuid`.

A 202 response only means synchronous checks passed for the accepted documents. Full validation can still fail later.

## Errors

| HTTP | Typical `error.code` | What it means |
| --- | --- | --- |
| 400 | `BadStructure` | Submission JSON is not a valid `documents` payload |
| 400 | `MaximumSizeExceeded` | Batch too large; submit smaller groups |
| 401 | — | Token missing or expired; call `login()` again |
| 403 | `IncorrectSubmitter` / `Forbidden` | Wrong taxpayer or ERP submission denied |
| 422 | `DuplicateSubmission` | Same payload sent within ~10 minutes; honor `Retry-After` |

These raise `ETAAuthenticationError` (401) or `ETAAPIError` (other API errors).

## Environments

| Environment | API base |
| --- | --- |
| `preprod` | `https://api.preprod.invoicing.eta.gov.eg` |
| `prod` | `https://api.invoicing.eta.gov.eg` |
