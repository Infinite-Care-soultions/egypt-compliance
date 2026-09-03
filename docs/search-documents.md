# Search documents

Search invoices you **sent** or **received**. This is the API ETA recommends instead of Get Recent Documents: more filters, continuation-token paging, and no 10,000-record cap.

Official API: [Search Documents](https://sdk.invoicing.eta.gov.eg/einvoicingapi/16-search-documents/)

`GET /api/v1.0/documents/search`

Send **either** `submission_date_from` / `submission_date_to` **or** `issue_date_from` / `issue_date_to` (UTC). Each pair is currently limited to about **30 days**. Keep the same filters when you request the next page.

ETA throttles this endpoint (about **1 request every 2 seconds** per taxpayer).

## 1. Login

```python
from egypt_compliance import ETAClientFactory

client = ETAClientFactory.create("preprod")  # or "prod"
token = client.login(client_id="your-client-id", client_secret="your-client-secret")
```

## 2. Search

Omit `continuation_token` on the first page. When `has_more()` is true, pass `continuation_token` from the previous response. Do not change the other filters.

```python
docs = client.search_documents(
    token,
    page_size=100,
    submission_date_from="2022-11-25T01:59:10Z",
    submission_date_to="2022-12-22T23:59:59Z",
    direction="Sent",          # or "Received"; omit to get both
    status="Valid",            # Valid, Invalid, Rejected, Cancelled, Submitted
    document_type="i",         # i, c, d, ei, ec, ed, ii
)
for doc in docs:
    print(doc.uuid, doc.internal_id, doc.status, doc.total)
if docs.has_more():
    next_page = client.search_documents(
        token,
        page_size=100,
        submission_date_from="2022-11-25T01:59:10Z",
        submission_date_to="2022-12-22T23:59:59Z",
        direction="Sent",
        status="Valid",
        document_type="i",
        continuation_token=docs.continuation_token,
    )
```

Look up one document:

```python
docs = client.search_documents(
    token,
    submission_date_from="2022-11-25T01:59:10Z",
    submission_date_to="2022-12-22T23:59:59Z",
    uuid="42S512YACQBRSRHYKBXBTGQG22",
    internal_id="PZ-234-A",
)
```

`direction="Sent"` can add `receiver_type` / `receiver_id`.  
`direction="Received"` can add `issuer_type` / `issuer_id`.

Receivers only see `Valid`, `Rejected`, and `Cancelled`. Issuers can see every status.

The last page returns `EndofResultSet` as the continuation token. `has_more()` is then `False`.

## Errors

| HTTP | Typical `error.code` | What it means |
| --- | --- | --- |
| 401 | — | Token missing or expired; call `login()` again |
| 403 | `forbidden` | ERP document retrieval is denied on the profile |

These raise `ETAAuthenticationError` (401) or `ETAAPIError` (other API errors).
