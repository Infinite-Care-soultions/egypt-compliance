# Get recent documents

List invoices you recently **sent** or **received**.

Official API: [Get Recent Documents](https://sdk.invoicing.eta.gov.eg/einvoicingapi/04-get-recent-documents/)

`GET /api/v1.0/documents/recent`

ETA recommends [Search Documents](docs/search-documents.md) (`client.search_documents()`) for new integrations. This endpoint is limited to about **30 days** and **10,000** matching records.

## 1. Login

```python
from egypt_compliance import ETAClientFactory

client = ETAClientFactory.create("preprod")  # or "prod"
token = client.login(client_id="your-client-id", client_secret="your-client-secret")
```

## 2. Query

```python
docs = client.get_recent_documents(
    token,
    page_no=1,
    page_size=20,
    direction="Sent",          # or "Received"
    status="Valid",            # Valid, Invalid, Rejected, Cancelled, Submitted
    document_type="i",         # i, c, d, ei, ec, ed, ii
)
print(docs.metadata.total_count, docs.metadata.total_pages)
for doc in docs:
    print(doc.uuid, doc.internal_id, doc.status, doc.total)
```

Date filters (UTC). If you send `*_from`, also send `*_to`, and the other way around:

```python
from datetime import datetime, timezone

docs = client.get_recent_documents(
    token,
    submission_date_from=datetime(2022, 11, 25, 1, 59, 10, tzinfo=timezone.utc),
    submission_date_to="2022-12-22T23:59:59Z",
    issue_date_from="2021-02-25T23:55:10Z",
    issue_date_to="2021-03-10T01:59:10Z",
)
```

`direction="Sent"` can add `receiver_type` / `receiver_id`.  
`direction="Received"` can add `issuer_type` / `issuer_id`.

Receivers only see `Valid`, `Rejected`, and `Cancelled`. Issuers can see every status.

`metadata.query_contains_complete_result_set` is `false` when the filter matches more than the API maximum; tighten the dates or other filters.

## Errors

| HTTP | Typical `error.code` | What it means |
| --- | --- | --- |
| 401 | — | Token missing or expired; call `login()` again |
| 403 | `forbidden` | ERP document retrieval is denied on the profile |

These raise `ETAAuthenticationError` (401) or `ETAAPIError` (other API errors).
