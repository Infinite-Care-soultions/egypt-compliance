from pydantic import BaseModel, ConfigDict, Field, field_validator

from egypt_compliance.models.recent_documents import DocumentSummary


class GetSubmissionQuery(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    page_no: int | None = Field(default=None, alias="pageNo")
    page_size: int | None = Field(default=None, alias="pageSize")

    def as_query_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        if self.page_no is not None:
            params["pageNo"] = str(self.page_no)
        if self.page_size is not None:
            params["pageSize"] = str(self.page_size)
        return params


class SubmissionMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    total_pages: int | None = Field(default=None, alias="totalPages")
    total_count: int | None = Field(default=None, alias="totalCount")


class GetSubmissionResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    uuid: str | None = None
    document_count: int | None = Field(default=None, alias="documentCount")
    date_time_received: str | None = Field(default=None, alias="dateTimeReceived")
    overall_status: str | None = Field(default=None, alias="overallStatus")
    document_summary: list[DocumentSummary] = Field(default_factory=list, alias="documentSummary")
    document_summary_metadata: SubmissionMetadata | None = Field(
        default=None, alias="documentSummaryMetadata"
    )

    @field_validator("document_summary_metadata", mode="before")
    @classmethod
    def _unwrap_metadata(cls, value: object) -> object:
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def __iter__(self):
        return iter(self.document_summary)

    def __len__(self) -> int:
        return len(self.document_summary)
