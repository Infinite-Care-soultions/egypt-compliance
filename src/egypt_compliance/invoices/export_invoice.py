from pydantic import Field

from egypt_compliance.invoices.base import InvoiceDocument


class ExportInvoice(InvoiceDocument):
    """Export invoice v1.0 (`documentType` = `ei`). Receiver type must be `F`."""

    document_type: str = Field(default="ei", alias="documentType")
