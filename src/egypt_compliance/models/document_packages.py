from datetime import datetime
import json

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_serializer, field_validator


def _format_eta_datetime(value: datetime | str) -> str:
    if isinstance(value, str):
        return value
    iso = value.isoformat()
    if iso.endswith("+00:00"):
        return iso[:-6] + "Z"
    return iso


class DocumentPackageItemCode(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    code_value: str | None = Field(
        default=None,
        validation_alias=AliasChoices("codeValue", "CodeValue", "code_value"),
        serialization_alias="codeValue",
    )
    code_type: str | None = Field(
        default=None,
        validation_alias=AliasChoices("codeType", "CodeType", "code_type"),
        serialization_alias="codeType",
    )


class DocumentPackageQueryParameters(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    date_from: datetime | str | None = Field(default=None, alias="dateFrom")
    date_to: datetime | str | None = Field(default=None, alias="dateTo")
    document_type_names: list[str] | None = Field(default=None, alias="documentTypeNames")
    document_type_name: str | None = Field(default=None, alias="documentTypeName")
    statuses: list[str] | str | None = None
    products_internal_codes: list[str] | str | None = Field(default=None, alias="productsInternalCodes")
    receiver_sender_type: str | int | None = Field(default=None, alias="receiverSenderType")
    receiver_sender_id: str | None = Field(default=None, alias="receiverSenderId")
    branch_number: str | None = Field(default=None, alias="branchNumber")
    item_codes: list[DocumentPackageItemCode] | str | None = Field(default=None, alias="itemCodes")
    truncate_if_exceeded: bool | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "truncateifexceeded",
            "truncateIfExceeded",
            "truncate_if_exceeded",
        ),
        serialization_alias="truncateifexceeded",
    )

    @field_validator("statuses", "products_internal_codes", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            parts = [part.strip() for part in value.split(",") if part.strip()]
            return parts or None
        return value

    @field_validator("item_codes", mode="before")
    @classmethod
    def _parse_item_codes(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        try:
            parsed = json.loads(value)
        except ValueError:
            return value
        if isinstance(parsed, dict):
            return parsed.get("ItemCodes") or parsed.get("itemCodes") or parsed
        return parsed

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


class PackageRequestsQuery(BaseModel):
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


class DocumentPackageInformation(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    package_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("packageId", "packageID", "package_id"),
        serialization_alias="packageId",
    )
    submission_date: str | None = Field(default=None, alias="submissionDate")
    status: int | None = None
    type: int | str | None = None
    format: int | str | None = None
    requestor_type_id: int | None = Field(default=None, alias="requestorTypeId")
    requestor_taxpayer_rin: str | None = Field(default=None, alias="requestorTaxpayerRIN")
    requestor_taxpayer_name: str | None = Field(default=None, alias="requestorTaxpayerName")
    deletion_date: str | None = Field(default=None, alias="deletionDate")
    is_expired: bool | None = Field(default=None, alias="isExpired")
    query_parameters: DocumentPackageQueryParameters | None = Field(
        default=None, alias="queryParameters"
    )


class PackageRequestsMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    total_pages: int | None = Field(default=None, alias="totalPages")
    total_count: int | None = Field(default=None, alias="totalCount")


class PackageRequestsResult(BaseModel):
    result: list[DocumentPackageInformation] = Field(default_factory=list)
    metadata: PackageRequestsMetadata | None = None

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

