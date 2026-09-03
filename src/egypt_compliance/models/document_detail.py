from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from egypt_compliance.models.documents import SubmissionError


class AdditionalMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    field_name: str | None = Field(default=None, alias="fieldName")
    field_value: str | None = Field(default=None, alias="fieldValue")
    field_type: str | None = Field(default=None, alias="fieldType")
    field_name_desc_en: str | None = Field(default=None, alias="fieldNameDescEn")
    field_name_desc_ar: str | None = Field(default=None, alias="fieldNameDescAr")


class ValidationStepResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str | None = None
    status: str | None = None
    error: SubmissionError | None = None


class DocumentValidationResults(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    status: str | None = None
    validation_steps: list[ValidationStepResult] = Field(
        default_factory=list, alias="validationSteps"
    )


class DocumentExtended(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    uuid: str | None = None
    submission_uuid: str | None = Field(default=None, alias="submissionUUID")
    long_id: str | None = Field(default=None, alias="longId")
    internal_id: str | None = Field(default=None, alias="internalId")
    type_name: str | None = Field(default=None, alias="typeName")
    type_version_name: str | None = Field(default=None, alias="typeVersionName")
    issuer_id: str | None = Field(default=None, alias="issuerId")
    issuer_name: str | None = Field(default=None, alias="issuerName")
    receiver_id: str | None = Field(default=None, alias="receiverId")
    receiver_name: str | None = Field(default=None, alias="receiverName")
    date_time_issued: str | None = Field(default=None, alias="dateTimeIssued")
    date_time_received: str | None = Field(default=None, alias="dateTimeReceived")
    total_sales: float | None = Field(default=None, alias="totalSales")
    total_discount: float | None = Field(default=None, alias="totalDiscount")
    net_amount: float | None = Field(default=None, alias="netAmount")
    total: float | None = None
    status: str | None = None
    late_submission_request_number: str | None = Field(
        default=None, alias="lateSubmissionRequestNumber"
    )
    document: dict | list | str | None = None
    transformation_status: str | None = Field(default=None, alias="transformationStatus")
    validation_results: DocumentValidationResults | None = Field(
        default=None, alias="validationResults"
    )
    additional_metadata: list[AdditionalMetadata] = Field(
        default_factory=list, alias="additionalMetadata"
    )


class DocumentPrintout(BaseModel):
    """PDF bytes for an ETA document printout."""

    uuid: str
    content: bytes
    content_type: str | None = None
    content_length: int | None = None

    @property
    def size(self) -> int:
        return len(self.content)

    def save(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.write_bytes(self.content)
        return destination

