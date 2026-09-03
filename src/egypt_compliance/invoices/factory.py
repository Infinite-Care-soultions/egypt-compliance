from abc import ABC, abstractmethod
from enum import Enum

from egypt_compliance.invoices.base import InvoiceDocument
from egypt_compliance.invoices.credit_note import CreditNote
from egypt_compliance.invoices.debit_note import DebitNote
from egypt_compliance.invoices.export_credit_note import ExportCreditNote
from egypt_compliance.invoices.export_debit_note import ExportDebitNote
from egypt_compliance.invoices.export_invoice import ExportInvoice
from egypt_compliance.invoices.invoice import Invoice


class InvoiceKind(str, Enum):
    INVOICE = "invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    EXPORT_INVOICE = "export_invoice"
    EXPORT_CREDIT_NOTE = "export_credit_note"
    EXPORT_DEBIT_NOTE = "export_debit_note"


class InvoiceCreator(ABC):
    """Factory Method: subclasses decide which invoice document to instantiate."""

    @abstractmethod
    def create_document(self, **data) -> InvoiceDocument:
        raise NotImplementedError


class InvoiceDocumentCreator(InvoiceCreator):
    def create_document(self, **data) -> Invoice:
        return Invoice(**data)


class CreditNoteCreator(InvoiceCreator):
    def create_document(self, **data) -> CreditNote:
        return CreditNote(**data)


class DebitNoteCreator(InvoiceCreator):
    def create_document(self, **data) -> DebitNote:
        return DebitNote(**data)


class ExportInvoiceCreator(InvoiceCreator):
    def create_document(self, **data) -> ExportInvoice:
        return ExportInvoice(**data)


class ExportCreditNoteCreator(InvoiceCreator):
    def create_document(self, **data) -> ExportCreditNote:
        return ExportCreditNote(**data)


class ExportDebitNoteCreator(InvoiceCreator):
    def create_document(self, **data) -> ExportDebitNote:
        return ExportDebitNote(**data)


class InvoiceFactory:
    """Public facade over invoice-type creators."""

    _creators: dict[str, type[InvoiceCreator]] = {
        InvoiceKind.INVOICE.value: InvoiceDocumentCreator,
        "i": InvoiceDocumentCreator,
        InvoiceKind.CREDIT_NOTE.value: CreditNoteCreator,
        "c": CreditNoteCreator,
        InvoiceKind.DEBIT_NOTE.value: DebitNoteCreator,
        "d": DebitNoteCreator,
        InvoiceKind.EXPORT_INVOICE.value: ExportInvoiceCreator,
        "ei": ExportInvoiceCreator,
        InvoiceKind.EXPORT_CREDIT_NOTE.value: ExportCreditNoteCreator,
        "ec": ExportCreditNoteCreator,
        InvoiceKind.EXPORT_DEBIT_NOTE.value: ExportDebitNoteCreator,
        "ed": ExportDebitNoteCreator,
    }

    @classmethod
    def create(cls, document_type: str | InvoiceKind, **data) -> InvoiceDocument:
        if isinstance(document_type, InvoiceKind):
            key = document_type.value
        else:
            key = str(document_type).strip().lower().replace("-", "_").replace(" ", "_")
        creator_cls = cls._creators.get(key)
        if creator_cls is None:
            valid = ", ".join(sorted({kind.value for kind in InvoiceKind}))
            raise ValueError(f"Unknown invoice type {document_type!r}. Expected one of: {valid}")
        return creator_cls().create_document(**data)
