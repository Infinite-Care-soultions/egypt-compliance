from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from egypt_compliance.models.recent_documents import DocumentSummary, _format_eta_datetime

END_OF_RESULT_SET = "EndofResultSet"


def _is_end_of_result_set(value: str | None) -> bool:
    if value is None:
        return True
    stripped = value.strip()
    return not stripped or stripped.lower() == END_OF_RESULT_SET.lower()


class SearchDocumentsQuery(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    submission_date_from: datetime | str | None = Field(default=None, alias="submissionDateFrom")
    submission_date_to: datetime | str | None = Field(default=None, alias="submissionDateTo")
    issue_date_from: datetime | str | None = Field(default=None, alias="issueDateFrom")
    issue_date_to: datetime | str | None = Field(default=None, alias="issueDateTo")
    continuation_token: str | None = Field(default=None, alias="continuationToken")
    page_size: int | None = Field(default=None, alias="pageSize")
    direction: str | None = None
    status: str | None = None
    document_type: str | None = Field(default=None, alias="documentType")
    receiver_type: str | None = Field(default=None, alias="receiverType")
    receiver_id: str | None = Field(default=None, alias="receiverId")
    issuer_type: str | None = Field(default=None, alias="issuerType")
    issuer_id: str | None = Field(default=None, alias="issuerId")
    uuid: str | None = None
    internal_id: str | None = Field(default=None, alias="internalID")

    def as_query_params(self) -> dict[str, str]:
        mapping = {
            "submissionDateFrom": self.submission_date_from,
            "submissionDateTo": self.submission_date_to,
            "issueDateFrom": self.issue_date_from,
            "issueDateTo": self.issue_date_to,
            "continuationToken": self.continuation_token,
            "pageSize": self.page_size,
            "direction": self.direction,
            "status": self.status,
            "documentType": self.document_type,
            "receiverType": self.receiver_type,
            "receiverId": self.receiver_id,
            "issuerType": self.issuer_type,
            "issuerId": self.issuer_id,
            "uuid": self.uuid,
            "internalID": self.internal_id,
        }
        params: dict[str, str] = {}
        for key, value in mapping.items():
            if value is None:
                continue
            if isinstance(value, datetime):
                params[key] = _format_eta_datetime(value)
            else:
                text = str(value).strip() if key == "continuationToken" else str(value)
                if key == "continuationToken" and _is_end_of_result_set(text):
                    continue
                params[key] = text
        return params


class SearchDocumentsMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    continuation_token: str | None = Field(default=None, alias="continuationToken")


class SearchDocumentsResult(BaseModel):
    result: list[DocumentSummary] = Field(default_factory=list)
    metadata: SearchDocumentsMetadata | None = None

    @field_validator("metadata", mode="before")
    @classmethod
    def _unwrap_metadata(cls, value: object) -> object:
        if isinstance(value, list):
            return value[0] if value else None
        return value

    @property
    def continuation_token(self) -> str | None:
        token = None if self.metadata is None else self.metadata.continuation_token
        if token is None or _is_end_of_result_set(token):
            return None
        return token.strip()

    def has_more(self) -> bool:
        return self.continuation_token is not None

    def __iter__(self):
        return iter(self.result)

    def __len__(self) -> int:
        return len(self.result)
