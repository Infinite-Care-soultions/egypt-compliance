from pydantic import Field

from egypt_compliance.invoices.base import InvoiceDocument


class CreditNote(InvoiceDocument):
    """Credit note v0.9 / v1.0 (`documentType` = `c`)."""

    document_type: str = Field(default="c", alias="documentType")
    references: list[str] | None = None
