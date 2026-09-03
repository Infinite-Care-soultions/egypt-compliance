from pydantic import Field

from egypt_compliance.invoices.base import InvoiceDocument


class ExportCreditNote(InvoiceDocument):
    """Export credit note v1.0 (`documentType` = `ec`)."""

    document_type: str = Field(default="ec", alias="documentType")
    references: list[str] | None = None
