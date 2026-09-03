# Generate signature

Create an ETA/ITIDA canonical string from invoice JSON and a Base64 CAdES-BES value that can be sent to [`submit_documents()`](submit-documents.md).

Official process: [Document Signature Creation](https://sdk.invoicing.eta.gov.eg/signature-creation/) and [Invoice signature](https://sdk.invoicing.eta.gov.eg/documents/invoice-v1-0/#signature)

Serialization rules: [Document Serialization Approach](https://sdk.invoicing.eta.gov.eg/document-serialization-approach/)

Reference implementation: [bassemAgmi/EInvoicingSigner](https://github.com/bassemAgmi/EInvoicingSigner) (C#)

This SDK does **not** need that C# exe. Pass a JSON file (or `Invoice.to_json()`) to a signer and get the canonical text plus CAdES-BES.

## 1. Build unsigned JSON

Use an [invoice module](invoices.md) or a JSON file **without** `signatures`.

```python
from egypt_compliance import Invoice, canonicalize

payload = invoice.to_json()          # dict
canonical = canonicalize(payload)    # ETA uppercase quoted string
# or
canonical = canonicalize("invoice.json")
```

Property names become culture-invariant uppercase. Scalar values are kept as in the JSON (so `14.00` stays `14.00`). `signatures` is omitted from the hash.

PEM, PFX, and PKCS#11 signers always create a CAdES-BES value, including for **v0.9**. ETA skips signature *validation* on v0.9, but the JSON still needs a `signatures` entry. Placeholder `ANY` is only returned by `SignatureFactory.create("unsigned")`.

## 2. Sign

### USB eSeal token (production)

Same inputs as the C# tool: token PIN, certificate issuer, PKCS#11 library. Token signing is included in the main package (`python -m pip install .`).

```python
from egypt_compliance import SignatureFactory

signer = SignatureFactory.create(
    "pkcs11",  # or "token"
    pin="12345678",
    library="eps2003csp11.dll",  # or SignatureP11.dll
    certificate_issuer="Egypt Trust Sealing CA",  # or "Egypt Trust CA G6"
)
result = signer.sign_file("SourceDocumentJson.json")
print(result.signature)   # Base64 CAdES-BES
print(result.canonical)   # same role as CanonicalString.txt
signed = result.document  # original JSON + signatures
submission = result.submission  # {"documents": [signed]}  (FullSignedDocument.json)
```

### PEM certificate and key

```python
signer = SignatureFactory.create(
    "pem",
    certificate="cert.pem",
    private_key="key.pem",
    password=None,
)
result = signer.sign_document(invoice.to_json())
```

### PFX / PKCS#12

```python
signer = SignatureFactory.create("pfx", pfx="eseal.pfx", password="secret")
result = signer.sign_file("invoice.json")
```

The CAdES-BES structure is detached CMS with SHA-256, signing-time, and SigningCertificateV2 (same family of attributes as the C# `SignWithCMS` path).

## 3. Signature JSON field

Default matches the C# tool (`signatureType` + `value`):

```json
"signatures": [{ "signatureType": "I", "value": "<cades-bes-base64>" }]
```

Official invoice tables also allow `type`. To use that:

```python
signer = SignatureFactory.create("pem", certificate="cert.pem", private_key="key.pem")
signer.signature_field = "type"
```

Issuer signature type is `I`. Optional service-provider signature is `S`.

## 4. Submit

```python
from egypt_compliance import ETAClientFactory, SignatureFactory

client = ETAClientFactory.create("preprod")
token = client.login(client_id="...", client_secret="...")

signer = SignatureFactory.create("pkcs11", pin="1234", library="eps2003csp11.dll")
signed = signer.sign_file("invoice.json")
result = client.submit_documents(token, signed.submission["documents"])
print(result.submission_uuid)
```

`sign_file` / `sign_document` also accept a `{ "documents": [ ... ] }` wrapper and sign each document.

## Factory methods

| `SignatureFactory.create(...)` | Use |
| --- | --- |
| `"pkcs11"` / `"token"` | USB token via PKCS#11 |
| `"pem"` | PEM cert + private key |
| `"pfx"` / `"pkcs12"` | `.pfx` file |
| `"unsigned"` / `"v0.9"` | placeholder `ANY` only — no CAdES |
