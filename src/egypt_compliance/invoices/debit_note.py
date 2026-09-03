from pydantic import Field

from egypt_compliance.invoices.base import InvoiceDocument


class DebitNote(InvoiceDocument):
    """Debit note v0.9 / v1.0 (`documentType` = `d`)."""

    document_type: str = Field(default="d", alias="documentType")
    references: list[str] | None = None
