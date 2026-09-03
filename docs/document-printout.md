# Get document printout

Download the ETA PDF of one invoice (layout, status watermark, and a QR code for public validation).

Official API: [Get Document Printout](https://sdk.invoicing.eta.gov.eg/einvoicingapi/10-get-document-printout/)

`GET /api/v1.0/documents/{uuid}/pdf`

`uuid` comes from submit, [`search_documents()`](search-documents.md), or [`get_recent_documents()`](recent-documents.md).

Receivers can only print `Valid`, `Rejected`, and `Cancelled`. If the document is still `submitted` or `invalid`, ETA returns 404. Issuers can print any status. If the document is still in processing, ETA returns `NotReady`.

## 1. Login

```python
from egypt_compliance import ETAClientFactory

client = ETAClientFactory.create("preprod")  # or "prod"
token = client.login(client_id="your-client-id", client_secret="your-client-secret")
```

## 2. Download

```python
pdf = client.get_document_printout(token, "SG4SSD5KJHHA62D")
pdf.save("invoice.pdf")
print(pdf.size, pdf.content_type)
```

## Errors

| HTTP | Typical `error.code` | What it means |
| --- | --- | --- |
| 400 | `NotReady` | Document is still in processing; try again later |
| 401 | — | Token missing or expired; call `login()` again |
| 403 | `Forbidden` | ERP document retrieval is denied on the profile |
| 404 | `Not Found` | Unknown uuid, or a receiver asked for a submitted/invalid document |

These raise `ETAAuthenticationError` (401) or `ETAAPIError` (other API errors).
