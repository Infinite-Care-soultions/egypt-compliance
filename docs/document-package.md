# Get document package

Download a ZIP of invoices you previously requested. The file is compressed JSON, XML, or CSV, matching the original request.

Official API: [Get Document Package](https://sdk.invoicing.eta.gov.eg/einvoicingapi/07-get-document-package/)

`GET /api/v1.0/documentpackages/{rid}`

HTTP **200** (or **206** for a byte range) means the ZIP is in `content`. HTTP **204** means the package is not ready yet — poll [`get_package_requests()`](package-requests.md) until `status == 2`.

The package stays downloadable until `deletion_date`. Full packages use the Get Document structure; summary packages are flat rows like Get Recent Documents.

## 1. Login

```python
from egypt_compliance import ETAClientFactory

client = ETAClientFactory.create("preprod")  # or "prod"
token = client.login(client_id="your-client-id", client_secret="your-client-secret")
```

## 2. Download

`package_id` is the ID from [`request_document_package()`](request-document-package.md) or [`get_package_requests()`](package-requests.md).

```python
download = client.get_document_package(token, "45KJHHA62D")
if download.ready:
    download.save("invoices.zip")
    print(download.size, download.content_type)
else:
    print("package is not ready yet")
```

Resume a large download with an HTTP Range header:

```python
part = client.get_document_package(
    token,
    "45KJHHA62D",
    byte_range="bytes=0-1048575",
)
```

## Errors

| HTTP | Typical `error.code` | What it means |
| --- | --- | --- |
| 401 | — | Token missing or expired; call `login()` again |
| 403 | `Forbidden` | ERP document retrieval is denied on the profile |

These raise `ETAAuthenticationError` (401) or `ETAAPIError` (other API errors). HTTP 204 is not an error: `ready` is `False`.
