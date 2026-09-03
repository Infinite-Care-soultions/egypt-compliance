# Invoice documents

Build ETA eInvoicing JSON for each document type, then sign it and send it with [`submit_documents()`](submit-documents.md).

Official types: [ETA document types](https://sdk.invoicing.eta.gov.eg/types/#invoice)

This SDK models **eInvoicing** documents (submit documents API), not eReceipt types.

| Module / class | `documentType` | Versions |
| --- | --- | --- |
| `Invoice` | `i` | `1.0` (default), `0.9` |
| `CreditNote` | `c` | `1.0`, `0.9` |
| `DebitNote` | `d` | `1.0`, `0.9` |
| `ExportInvoice` | `ei` | `1.0` |
| `ExportCreditNote` | `ec` | `1.0` |
| `ExportDebitNote` | `ed` | `1.0` |

v0.9 uses the same JSON as v1.0; ETA skips signature validation on v0.9. Set `document_type_version="0.9"` when you need that.

## 1. Set document data

Use the class for the type you need, or `InvoiceFactory.create(...)`.

```python
from datetime import datetime, timezone
from egypt_compliance import (
    Address,
    Invoice,
    InvoiceFactory,
    InvoiceLine,
    Issuer,
    Receiver,
    TaxableItem,
    TaxTotal,
    UnitValue,
)

issuer = Issuer(
    id="100015840",
    name="Issuer Co",
    address=Address(
        branch_id="0",
        country="EG",
        governate="Cairo",
        region_city="Nasr City",
        street="Street 1",
        building_number="10",
    ),
)
receiver = Receiver(
    type="B",
    id="200015840",
    name="Buyer Co",
    address=Address(
        country="EG",
        governate="Giza",
        region_city="Dokki",
        street="Street 2",
        building_number="17",
    ),
)
line = InvoiceLine(
    description="Bottle of water",
    item_type="EGS",
    item_code="EG-100015840-1",
    unit_type="EA",
    quantity=1,
    unit_value=UnitValue(amount_egp=100),
    sales_total=100,
    total=114,
    net_total=100,
    taxable_items=[TaxableItem(tax_type="T1", amount=14, sub_type="V001", rate=14)],
)

invoice = Invoice(
    issuer=issuer,
    receiver=receiver,
    date_time_issued=datetime(2024, 2, 13, 13, 15, tzinfo=timezone.utc),
    taxpayer_activity_code="4620",
    internal_id="INV-1",
    invoice_lines=[line],
    total_sales_amount=100,
    net_amount=100,
    total_amount=114,
    tax_totals=[TaxTotal(tax_type="T1", amount=14)],
)

# Same result via factory:
invoice = InvoiceFactory.create(
    "invoice",  # or "i", "credit_note", "c", "debit_note", "d",
                # "export_invoice", "ei", "export_credit_note", "ec",
                # "export_debit_note", "ed"
    issuer=issuer,
    receiver=receiver,
    date_time_issued=datetime(2024, 2, 13, 13, 15, tzinfo=timezone.utc),
    taxpayer_activity_code="4620",
    internal_id="INV-1",
    invoice_lines=[line],
    total_sales_amount=100,
    net_amount=100,
    total_amount=114,
    tax_totals=[TaxTotal(tax_type="T1", amount=14)],
)
```

Python names (`internal_id`, `invoice_lines`) map to ETA camelCase (`internalID`, `invoiceLines`) in the generated JSON.

## 2. Generate JSON

```python
payload = invoice.to_json()
# {
#   "documentType": "i",
#   "documentTypeVersion": "1.0",
#   "internalID": "INV-1",
#   ...
# }
```

This object is one element of the `documents` array expected by Submit Documents. It does **not** include `signatures` until you add them.

## 3. Credit / debit notes

Pass `references` with the ETA UUIDs of the invoices you are adjusting.

```python
from egypt_compliance import CreditNote, DebitNote

credit = CreditNote(
    issuer=issuer,
    receiver=receiver,
    references=["S98L2CP1SMVBIU"],
    date_time_issued=datetime(2024, 2, 13, 13, 15, tzinfo=timezone.utc),
    taxpayer_activity_code="4620",
    internal_id="CN-1",
    invoice_lines=[line],
    total_sales_amount=100,
    net_amount=100,
    total_amount=114,
)
debit = DebitNote(..., references=["S98L2CP1SMVBIU"])
```

Lines and parties should match the referenced invoices; only quantities and amounts change. Credit note totals cannot exceed the referenced invoices.

## 4. Export documents

Receiver `type` must be `F` (foreign), country not `EG`. Optional line fields: `weight_unit_type`, `weight_quantity`. Optional header: `service_delivery_date` (`yyyy-MM-dd`).

```python
from egypt_compliance import ExportInvoice

export = ExportInvoice(
    issuer=issuer,
    receiver=Receiver(
        type="F",
        id="IE8256796U",
        name="Foreign Buyer Ltd",
        address=Address(
            country="IE",
            governate="Leinster",
            region_city="Dublin",
            street="Export Street",
            building_number="1",
        ),
    ),
    service_delivery_date="2015-02-13",
    date_time_issued=datetime(2024, 2, 13, 13, 15, tzinfo=timezone.utc),
    taxpayer_activity_code="9478",
    internal_id="EXP-1",
    invoice_lines=[line],
    total_sales_amount=100,
    net_amount=100,
    total_amount=114,
)
```

## 5. Sign, then submit

```python
from egypt_compliance import SignatureFactory

signer = SignatureFactory.create("pem", certificate="cert.pem", private_key="key.pem")
signed = signer.sign_document(invoice.to_json())
client.submit_documents(token, [signed.document])
```

USB token and canonicalization details: [Generate signature](signing.md).

See [Submit documents](submit-documents.md) for login, 202 handling, and mapping `uuid` / `longId` back to `internalID`.
