from pydantic import BaseModel, ConfigDict, Field


class DocumentSignature(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    value: str


class SubmittedDocument(BaseModel):
    """A signed document payload. Extra invoice fields are passed through to ETA."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    document_type: str | None = Field(default=None, alias="documentType")
    document_type_version: str | None = Field(default=None, alias="documentTypeVersion")
    internal_id: str | None = Field(default=None, alias="internalID")
    date_time_issued: str | None = Field(default=None, alias="dateTimeIssued")
    signatures: list[DocumentSignature] | None = None


class SubmitDocumentsRequest(BaseModel):
    documents: list[SubmittedDocument]

    def as_api_body(self) -> dict:
        return {"documents": [doc.model_dump(by_alias=True, exclude_none=True, mode="json") for doc in self.documents]}


class SubmissionError(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    code: str | None = None
    message: str | None = None
    target: str | None = None
    property_path: str | None = Field(default=None, alias="propertyPath")
    details: list["SubmissionError"] = Field(default_factory=list)


class AcceptedDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    uuid: str | None = None
    long_id: str | None = Field(default=None, alias="longId")
    internal_id: str | None = Field(default=None, alias="internalId")


class RejectedDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    internal_id: str | None = Field(default=None, alias="internalId")
    uuid: str | None = None
    error: SubmissionError | None = None


class SubmitDocumentsResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    submission_uuid: str | None = Field(default=None, alias="submissionUUID")
    accepted_documents: list[AcceptedDocument] = Field(default_factory=list, alias="acceptedDocuments")
    rejected_documents: list[RejectedDocument] = Field(default_factory=list, alias="rejectedDocuments")


class CancelDocumentRequest(BaseModel):
    status: str = "cancelled"
    reason: str

    def as_api_body(self) -> dict:
        return self.model_dump(exclude_none=True, mode="json")


class CancelDocumentResult(BaseModel):
    """ETA documents a 200 on success; the response body is optional."""

    success: bool = True
    payload: dict | list | None = None


class RejectDocumentRequest(BaseModel):
    status: str = "rejected"
    reason: str

    def as_api_body(self) -> dict:
        return self.model_dump(exclude_none=True, mode="json")


class RejectDocumentResult(BaseModel):
    """ETA documents a 200 on success; the response body is optional."""

    success: bool = True
    payload: dict | list | None = None
