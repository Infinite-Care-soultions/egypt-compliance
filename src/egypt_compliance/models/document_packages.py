from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_serializer


def _format_eta_datetime(value: datetime | str) -> str:
    if isinstance(value, str):
        return value
    iso = value.isoformat()
    if iso.endswith("+00:00"):
        return iso[:-6] + "Z"
    return iso


class DocumentPackageItemCode(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    code_value: str | None = Field(default=None, alias="codeValue")
    code_type: str | None = Field(default=None, alias="codeType")


class DocumentPackageQueryParameters(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    date_from: datetime | str | None = Field(default=None, alias="dateFrom")
    date_to: datetime | str | None = Field(default=None, alias="dateTo")
    document_type_names: list[str] | None = Field(default=None, alias="documentTypeNames")
    statuses: list[str] | None = None
    products_internal_codes: list[str] | None = Field(default=None, alias="productsInternalCodes")
    receiver_sender_type: str | int | None = Field(default=None, alias="receiverSenderType")
    receiver_sender_id: str | None = Field(default=None, alias="receiverSenderId")
    branch_number: str | None = Field(default=None, alias="branchNumber")
    item_codes: list[DocumentPackageItemCode] | None = Field(default=None, alias="itemCodes")
    truncate_if_exceeded: bool | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "truncateifexceeded",
            "truncateIfExceeded",
            "truncate_if_exceeded",
        ),
        serialization_alias="truncateifexceeded",
    )

    @field_serializer("date_from", "date_to")
    def _serialize_datetime(self, value: datetime | str | None) -> str | None:
        if value is None:
            return None
        return _format_eta_datetime(value)

    @field_serializer("receiver_sender_type")
    def _serialize_receiver_sender_type(self, value: str | int | None) -> str | None:
        if value is None:
            return None
        return str(value)


class RequestDocumentPackageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    type: str = "full"
    format: str = "JSON"
    query_parameters: DocumentPackageQueryParameters = Field(alias="queryParameters")
    represented_taxpayer_filter_type: int | None = Field(
        default=None, alias="representedTaxpayerFilterType"
    )
    representee_rin: str | None = Field(default=None, alias="representeeRin")

    def as_api_body(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")


class RequestDocumentPackageResult(BaseModel):
    """ETA documents HTTP 201 and a body with the assigned package ID."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    package_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("packageId", "packageID", "package_id"),
        serialization_alias="packageId",
    )
