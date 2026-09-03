from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _format_eta_datetime(value: datetime | str) -> str:
    if isinstance(value, str):
        return value
    iso = value.isoformat()
    if iso.endswith("+00:00"):
        return iso[:-6] + "Z"
    return iso


class RecentDocumentsQuery(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    page_no: int | None = Field(default=None, alias="pageNo")
    page_size: int | None = Field(default=None, alias="pageSize")
    submission_date_from: datetime | str | None = Field(default=None, alias="submissionDateFrom")
    submission_date_to: datetime | str | None = Field(default=None, alias="submissionDateTo")
    issue_date_from: datetime | str | None = Field(default=None, alias="issueDateFrom")
    issue_date_to: datetime | str | None = Field(default=None, alias="issueDateTo")
    direction: str | None = None
    status: str | None = None
    document_type: str | None = Field(default=None, alias="documentType")
    receiver_type: str | None = Field(default=None, alias="receiverType")
    receiver_id: str | None = Field(default=None, alias="receiverId")
    issuer_type: str | None = Field(default=None, alias="issuerType")
    issuer_id: str | None = Field(default=None, alias="issuerId")

    def as_query_params(self) -> dict[str, str]:
        mapping = {
            "pageNo": self.page_no,
            "pageSize": self.page_size,
            "submissionDateFrom": self.submission_date_from,
            "submissionDateTo": self.submission_date_to,
            "issueDateFrom": self.issue_date_from,
            "issueDateTo": self.issue_date_to,
            "direction": self.direction,
            "status": self.status,
            "documentType": self.document_type,
            "receiverType": self.receiver_type,
            "receiverId": self.receiver_id,
            "issuerType": self.issuer_type,
            "issuerId": self.issuer_id,
        }
        params: dict[str, str] = {}
        for key, value in mapping.items():
            if value is None:
                continue
            if isinstance(value, datetime):
                params[key] = _format_eta_datetime(value)
            else:
                params[key] = str(value)
        return params


class FreezeStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    frozen: bool | None = None
    type: int | None = None
    scope: int | None = None
    action_date: str | None = Field(default=None, alias="actionDate")
    au_code: str | None = Field(default=None, alias="auCode")
    au_name: str | None = Field(default=None, alias="auName")


class DocumentSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    uuid: str | None = None
    submission_uuid: str | None = Field(default=None, alias="submissionUUID")
    long_id: str | None = Field(default=None, alias="longId")
    public_url: str | None = Field(default=None, alias="publicUrl")
    internal_id: str | None = Field(default=None, alias="internalId")
    type_name: str | None = Field(default=None, alias="typeName")
    type_version_name: str | None = Field(default=None, alias="typeVersionName")
    issuer_id: str | None = Field(default=None, alias="issuerId")
    issuer_name: str | None = Field(default=None, alias="issuerName")
    issuer_type: str | None = Field(default=None, alias="issuerType")
    receiver_id: str | None = Field(default=None, alias="receiverId")
    receiver_name: str | None = Field(default=None, alias="receiverName")
    receiver_type: str | None = Field(default=None, alias="receiverType")
    date_time_issued: str | None = Field(default=None, alias="dateTimeIssued")
    date_time_received: str | None = Field(default=None, alias="dateTimeReceived")
    total_sales: float | None = Field(default=None, alias="totalSales")
    total_discount: float | None = Field(default=None, alias="totalDiscount")
    net_amount: float | None = Field(default=None, alias="netAmount")
    total: float | None = None
    status: str | None = None
    cancel_request_date: str | None = Field(default=None, alias="cancelRequestDate")
    reject_request_date: str | None = Field(default=None, alias="rejectRequestDate")
    cancel_request_delayed_date: str | None = Field(default=None, alias="cancelRequestDelayedDate")
    reject_request_delayed_date: str | None = Field(default=None, alias="rejectRequestDelayedDate")
    decline_cancel_request_date: str | None = Field(default=None, alias="declineCancelRequestDate")
    decline_reject_request_date: str | None = Field(default=None, alias="declineRejectRequestDate")
    document_status_reason: str | None = Field(default=None, alias="documentStatusReason")
    created_by_user_id: str | None = Field(default=None, alias="createdByUserId")
    freeze_status: FreezeStatus | None = Field(default=None, alias="freezeStatus")
    late_submission_request_number: str | None = Field(default=None, alias="lateSubmissionRequestNumber")


class RecentDocumentsMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    total_pages: int | None = Field(default=None, alias="totalPages")
    total_count: int | None = Field(default=None, alias="totalCount")
    query_contains_complete_result_set: bool | None = Field(
        default=None, alias="queryContainsCompleteResultSet"
    )
    remaining_records_count: int | None = Field(default=None, alias="remainingRecordsCount")


class RecentDocumentsResult(BaseModel):
    result: list[DocumentSummary] = Field(default_factory=list)
    metadata: RecentDocumentsMetadata | None = None

    @field_validator("metadata", mode="before")
    @classmethod
    def _unwrap_metadata(cls, value: object) -> object:
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def __iter__(self):
        return iter(self.result)

    def __len__(self) -> int:
        return len(self.result)
