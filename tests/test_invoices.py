from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from egypt_compliance import (
    Address,
    CreditNote,
    DebitNote,
    ExportCreditNote,
    ExportDebitNote,
    ExportInvoice,
    Invoice,
    InvoiceFactory,
    InvoiceKind,
    InvoiceLine,
    Issuer,
    Receiver,
    TaxableItem,
    TaxTotal,
    UnitValue,
)


ISSUED = datetime(2024, 2, 13, 13, 15, tzinfo=timezone.utc)

ISSUER = Issuer(
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

RECEIVER = Receiver(
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

FOREIGN_RECEIVER = Receiver(
    type="F",
    id="IE8256796U",
    name="MICROSOFT IRELAND OPERATIONS LIMITED",
    address=Address(
        country="IE",
        governate="Leinster",
        region_city="Dublin",
        street="Carmanhall and Leopardstown",
        building_number="One Microsoft Place",
        postal_code="D18 P521",
    ),
)

LINE = InvoiceLine(
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


def _totals():
    return {
        "date_time_issued": ISSUED,
        "taxpayer_activity_code": "4620",
        "internal_id": "INV-1",
        "invoice_lines": [LINE],
        "total_sales_amount": 100,
        "net_amount": 100,
        "total_amount": 114,
        "tax_totals": [TaxTotal(tax_type="T1", amount=14)],
    }


def test_invoice_to_json_uses_eta_camel_case_and_type_i():
    invoice = Invoice(issuer=ISSUER, receiver=RECEIVER, **_totals())
    payload = invoice.to_json()

    assert payload["documentType"] == "i"
    assert payload["documentTypeVersion"] == "1.0"
    assert payload["dateTimeIssued"] == "2024-02-13T13:15:00Z"
    assert payload["internalID"] == "INV-1"
    assert payload["taxpayerActivityCode"] == "4620"
    assert payload["issuer"]["address"]["branchId"] == "0"
    assert payload["issuer"]["address"]["regionCity"] == "Nasr City"
    assert payload["invoiceLines"][0]["itemType"] == "EGS"
    assert payload["invoiceLines"][0]["unitValue"]["amountEGP"] == 100
    assert payload["invoiceLines"][0]["taxableItems"][0]["taxType"] == "T1"
    assert payload["taxTotals"][0]["taxType"] == "T1"
    assert "signatures" not in payload
    assert "references" not in payload


def test_invoice_version_0_9():
    invoice = Invoice(
        issuer=ISSUER,
        receiver=RECEIVER,
        document_type_version="0.9",
        **_totals(),
    )
    assert invoice.to_json()["documentTypeVersion"] == "0.9"


def test_credit_note_and_debit_note_json():
    totals = _totals()
    credit = CreditNote(
        issuer=ISSUER,
        receiver=RECEIVER,
        references=["S98L2CP1SMVBIU"],
        **totals,
    )
    debit = DebitNote(
        issuer=ISSUER,
        receiver=RECEIVER,
        references=["S98L2CP1SMVBIU"],
        **totals,
    )
    assert credit.to_json()["documentType"] == "c"
    assert credit.to_json()["references"] == ["S98L2CP1SMVBIU"]
    assert debit.to_json()["documentType"] == "d"
    assert debit.to_json()["references"] == ["S98L2CP1SMVBIU"]


def test_export_invoice_json_includes_weight_and_service_date():
    export_line = InvoiceLine(
        description="Export apples",
        item_type="GS1",
        item_code="10003752",
        unit_type="kgm",
        quantity=4.44444,
        unit_value=UnitValue(amount_egp=1.21984),
        sales_total=5.42,
        total=5.42,
        net_total=5.42,
        weight_unit_type="kgm",
        weight_quantity=1.2,
    )
    invoice = ExportInvoice(
        issuer=ISSUER,
        receiver=FOREIGN_RECEIVER,
        date_time_issued=ISSUED,
        service_delivery_date=date(2015, 2, 13),
        taxpayer_activity_code="9478",
        internal_id="AZ-24883",
        invoice_lines=[export_line],
        total_sales_amount=5.42,
        net_amount=5.42,
        total_amount=5.42,
    )
    payload = invoice.to_json()
    assert payload["documentType"] == "ei"
    assert payload["receiver"]["type"] == "F"
    assert payload["serviceDeliveryDate"] == "2015-02-13"
    assert payload["invoiceLines"][0]["weightUnitType"] == "kgm"
    assert payload["invoiceLines"][0]["weightQuantity"] == 1.2


def test_export_credit_and_debit_note_types():
    totals = _totals()
    credit = ExportCreditNote(
        issuer=ISSUER,
        receiver=FOREIGN_RECEIVER,
        references=["S98L2CP1SMVBIU"],
        **totals,
    )
    debit = ExportDebitNote(
        issuer=ISSUER,
        receiver=FOREIGN_RECEIVER,
        references=["S98L2CP1SMVBIU"],
        **totals,
    )
    assert credit.to_json()["documentType"] == "ec"
    assert debit.to_json()["documentType"] == "ed"


def test_invoice_factory_creates_each_type():
    totals = _totals()
    invoice = InvoiceFactory.create("invoice", issuer=ISSUER, receiver=RECEIVER, **totals)
    credit = InvoiceFactory.create("c", issuer=ISSUER, receiver=RECEIVER, **totals)
    export = InvoiceFactory.create(
        InvoiceKind.EXPORT_INVOICE,
        issuer=ISSUER,
        receiver=FOREIGN_RECEIVER,
        **totals,
    )
    assert isinstance(invoice, Invoice)
    assert isinstance(credit, CreditNote)
    assert isinstance(export, ExportInvoice)
    assert invoice.to_json()["documentType"] == "i"
    assert credit.to_json()["documentType"] == "c"
    assert export.to_json()["documentType"] == "ei"


def test_invoice_factory_rejects_unknown_type():
    with pytest.raises(ValueError, match="Unknown invoice type"):
        InvoiceFactory.create("receipt")


def test_invoice_requires_at_least_one_line():
    with pytest.raises(ValidationError):
        Invoice(
            issuer=ISSUER,
            receiver=RECEIVER,
            date_time_issued=ISSUED,
            taxpayer_activity_code="4620",
            internal_id="INV-1",
            invoice_lines=[],
            total_sales_amount=0,
            net_amount=0,
            total_amount=0,
        )


def test_add_signature_then_to_json():
    invoice = Invoice(issuer=ISSUER, receiver=RECEIVER, **_totals())
    invoice.add_signature("I", "cades-bes-base64")
    payload = invoice.to_json()
    assert payload["signatures"] == [{"type": "I", "value": "cades-bes-base64"}]
