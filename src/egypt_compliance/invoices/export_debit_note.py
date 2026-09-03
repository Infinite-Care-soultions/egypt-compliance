from pydantic import Field

from egypt_compliance.invoices.base import InvoiceDocument


class ExportDebitNote(InvoiceDocument):
    """Export debit note v1.0 (`documentType` = `ed`)."""

    document_type: str = Field(default="ed", alias="documentType")
    references: list[str] | None = None
