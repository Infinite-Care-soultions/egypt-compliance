from pydantic import Field

from egypt_compliance.invoices.base import InvoiceDocument


class Invoice(InvoiceDocument):
    """Invoice v0.9 / v1.0 (`documentType` = `i`)."""

    document_type: str = Field(default="i", alias="documentType")
