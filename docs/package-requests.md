# Get package requests

List document packages you already requested and check whether each one is ready to download.

Official API: [Get Package Requests](https://sdk.invoicing.eta.gov.eg/einvoicingapi/06-get-package-requests/)

`GET /api/v1.0/documentpackages/requests`

Create a request first with [`request_document_package()`](request-document-package.md). Newest requests come first. Page with `page_no` / `page_size`.

## 1. Login

```python
from egypt_compliance import ETAClientFactory

client = ETAClientFactory.create("preprod")  # or "prod"
token = client.login(client_id="your-client-id", client_secret="your-client-secret")
```

## 2. List

```python
packages = client.get_package_requests(token, page_no=1, page_size=20)
print(packages.metadata.total_count, packages.metadata.total_pages)
for package in packages:
    print(package.package_id, package.status, package.is_expired)
```

`status`: `1` in progress, `2` complete, `3` error, `4` deleted.  
`type`: `1` full, `2` summary.  
`format`: `1` CSV, `2` XML, `3` JSON.

Download only when `status == 2` and `is_expired` is not true. `deletion_date` is when ETA plans to remove a completed package.

```python
ready = [pkg for pkg in packages if pkg.status == 2 and not pkg.is_expired]
```

Or with the query model:

```python
from egypt_compliance import PackageRequestsQuery

packages = client.get_package_requests(
    token,
    PackageRequestsQuery(page_no=3, page_size=20),
)
```

If you requested packages as a taxpayer representative, this list includes packages requested by any representative of that taxpayer.

## Errors

| HTTP | Typical `error.code` | What it means |
| --- | --- | --- |
| 401 | — | Token missing or expired; call `login()` again |
| 403 | `Forbidden` | ERP document retrieval is denied on the profile |

These raise `ETAAuthenticationError` (401) or `ETAAPIError` (other API errors).
