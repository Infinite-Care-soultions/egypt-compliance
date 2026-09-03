from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NotificationType(IntEnum):
    DELEGATION_INVITE = 1
    OTP = 2
    PROFILE_DATA_VALIDATION = 3
    GENERIC_NOTIFICATION = 4
    RECEIVE_DOWNLOAD_READY = 5
    DOCUMENT_RECEIVED = 6
    DOCUMENT_VALIDATED = 7
    DOCUMENT_CANCELLED = 8
    DOCUMENT_REJECTED = 9


class NotificationQuery(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date_from: datetime | str | None = Field(default=None, alias="dateFrom")
    date_to: datetime | str | None = Field(default=None, alias="dateTo")
    type: NotificationType | int | str | None = None
    language: str | None = None
    status: str | None = None
    channel: str | None = None
    page_no: int | None = Field(default=None, alias="pageNo")
    page_size: int | None = Field(default=None, alias="pageSize")

    def as_query_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        mapping = {
            "dateFrom": self.date_from,
            "dateTo": self.date_to,
            "type": self.type,
            "language": self.language,
            "status": self.status,
            "channel": self.channel,
            "pageNo": self.page_no,
            "pageSize": self.page_size,
        }
        for key, value in mapping.items():
            if value is None:
                continue
            if isinstance(value, datetime):
                params[key] = _format_eta_datetime(value)
            else:
                params[key] = str(int(value) if isinstance(value, NotificationType) else value)
        return params


class DeliveryAttempt(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    attempt_date_time: datetime = Field(alias="attemptDateTime")
    status: str
    status_details: str | None = Field(default=None, alias="statusDetails")


class Notification(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    notification_id: str = Field(alias="notificationId")
    received_date_time: datetime = Field(alias="receivedDateTime")
    delivered_date_time: datetime | None = Field(default=None, alias="deliveredDateTime")
    type_id: str = Field(alias="typeId")
    type_name: str = Field(alias="typeName")
    final_message: str | None = Field(default=None, alias="finalMessage")
    channel: str
    address: str | None = None
    language: str
    status: str
    delivery_attempts: list[DeliveryAttempt] = Field(
        default_factory=list,
        alias="deliveryAttempts",
    )

    @field_validator("type_id", mode="before")
    @classmethod
    def _coerce_type_id(cls, value: object) -> object:
        if isinstance(value, int):
            return str(value)
        return value


class PageMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_pages: int = Field(alias="totalPages")
    total_count: int = Field(alias="totalCount")


class NotificationsResult(BaseModel):
    result: list[Notification] = Field(default_factory=list)
    metadata: PageMetadata | None = None

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


def _format_eta_datetime(value: datetime) -> str:
    iso = value.isoformat()
    if iso.endswith("+00:00"):
        return iso[:-6] + "Z"
    return iso
