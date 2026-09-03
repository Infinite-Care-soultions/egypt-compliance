# Get submission

Check a batch you already submitted: overall status and a paged list of documents in that submission. **Issuers only** (including intermediaries who submitted on behalf of the taxpayer).

Official API: [Get Submission](https://sdk.invoicing.eta.gov.eg/einvoicingapi/09-get-submission/)

`GET /api/v1.0/documentsubmissions/{uuid}`

`uuid` is `submission_uuid` from [`submit_documents()`](submit-documents.md).

`overall_status`: `in progress`, `valid`, `partially valid`, `invalid`.

## 1. Login

```python
from egypt_compliance import ETAClientFactory

client = ETAClientFactory.create("preprod")  # or "prod"
token = client.login(client_id="your-client-id", client_secret="your-client-secret")
```

## 2. Get

```python
submission = client.get_submission(
    token,
    "HJSD135P2S7D8IU",
    page_no=1,
    page_size=20,
)
print(submission.overall_status, submission.document_count)
print(submission.document_summary_metadata.total_pages)
for doc in submission:
    print(doc.uuid, doc.internal_id, doc.status, doc.total)
```

Or with the query model:

```python
from egypt_compliance import GetSubmissionQuery

submission = client.get_submission(
    token,
    "HJSD135P2S7D8IU",
    GetSubmissionQuery(page_no=3, page_size=20),
)
```

Then load a single invoice with [`get_document()`](get-document.md) using `doc.uuid`.

## Errors

| HTTP | Typical `error.code` | What it means |
| --- | --- | --- |
| 401 | — | Token missing or expired; call `login()` again |
| 403 | `Forbidden` | ERP document retrieval is denied on the profile |

These raise `ETAAuthenticationError` (401) or `ETAAPIError` (other API errors).
