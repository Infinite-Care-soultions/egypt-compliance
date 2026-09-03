from datetime import date, datetime

from pydantic import AliasChoices, Field, field_serializer

from egypt_compliance.invoices.common import (
    Address,
    Delivery,
    DocumentSignature,
    ETAModel,
    InvoiceLine,
    Issuer,
    Payment,
    Receiver,
    TaxTotal,
    format_eta_date,
    format_eta_datetime,
)


class InvoiceDocument(ETAModel):
    """Shared ETA eInvoicing document fields. Subclasses lock `documentType`."""

    issuer: Issuer
    receiver: Receiver
    document_type: str = Field(alias="documentType")
    document_type_version: str = Field(default="1.0", alias="documentTypeVersion")
    date_time_issued: datetime | str = Field(alias="dateTimeIssued")
    taxpayer_activity_code: str = Field(alias="taxpayerActivityCode")
    internal_id: str = Field(
        validation_alias=AliasChoices("internalID", "internalId", "internal_id"),
        serialization_alias="internalID",
    )
    purchase_order_reference: str | None = Field(default=None, alias="purchaseOrderReference")
    purchase_order_description: str | None = Field(default=None, alias="purchaseOrderDescription")
    sales_order_reference: str | None = Field(default=None, alias="salesOrderReference")
    sales_order_description: str | None = Field(default=None, alias="salesOrderDescription")
    proforma_invoice_number: str | None = Field(default=None, alias="proformaInvoiceNumber")
    payment: Payment | None = None
    delivery: Delivery | None = None
    invoice_lines: list[InvoiceLine] = Field(min_length=1, alias="invoiceLines")
    total_sales_amount: float = Field(alias="totalSalesAmount")
    total_discount_amount: float = Field(default=0, alias="totalDiscountAmount")
    net_amount: float = Field(alias="netAmount")
    tax_totals: list[TaxTotal] | None = Field(default=None, alias="taxTotals")
    extra_discount_amount: float = Field(default=0, alias="extraDiscountAmount")
    total_items_discount_amount: float = Field(default=0, alias="totalItemsDiscountAmount")
    total_amount: float = Field(alias="totalAmount")
    service_delivery_date: date | datetime | str | None = Field(default=None, alias="serviceDeliveryDate")
    signatures: list[DocumentSignature] | None = None

    @field_serializer("date_time_issued")
    def _serialize_issued(self, value: datetime | str) -> str:
        return format_eta_datetime(value)

    @field_serializer("service_delivery_date")
    def _serialize_service_date(self, value: date | datetime | str | None) -> str | None:
        if value is None:
            return None
        return format_eta_date(value)

    def to_json(self) -> dict:
        """ETA camelCase document object for signing, then `submit_documents()`."""
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")

    def add_signature(self, signature_type: str, value: str) -> "InvoiceDocument":
        if self.signatures is None:
            self.signatures = []
        self.signatures.append(DocumentSignature(type=signature_type, value=value))
        return self


__all__ = [
    "Address",
    "Delivery",
    "DocumentSignature",
    "InvoiceDocument",
    "InvoiceLine",
    "Issuer",
    "Payment",
    "Receiver",
    "TaxTotal",
]
