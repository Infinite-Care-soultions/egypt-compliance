from datetime import datetime
from enum import Enum

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_serializer


def _format_eta_datetime(value: datetime | str) -> str:
    if isinstance(value, str):
        return value
    iso = value.isoformat()
    if iso.endswith("+00:00"):
        return iso[:-6] + "Z"
    return iso


class EGSCodeUsageItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code_type: str = Field(default="EGS", alias="codeType")
    parent_code: str = Field(alias="parentCode")
    item_code: str = Field(alias="itemCode")
    code_name: str = Field(alias="codeName")
    code_name_ar: str = Field(alias="codeNameAr")
    active_from: datetime | str = Field(alias="activeFrom")
    active_to: datetime | str | None = Field(default=None, alias="activeTo")
    description: str | None = None
    description_ar: str | None = Field(default=None, alias="descriptionAr")
    request_reason: str | None = Field(default=None, alias="requestReason")
    linked_code: str | None = Field(default=None, alias="linkedCode")

    @field_serializer("active_from", "active_to")
    def _serialize_datetime(self, value: datetime | str | None) -> str | None:
        if value is None:
            return None
        return _format_eta_datetime(value)


class CreateEGSCodeUsageRequest(BaseModel):
    items: list[EGSCodeUsageItem]

    def as_api_body(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")


class CreateEGSCodeUsageResult(BaseModel):
    """ETA documents a 200 on success; the response body is optional."""

    success: bool = True
    payload: dict | list | None = None


class CodeReuseItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code_type: str = Field(
        default="EGS",
        validation_alias=AliasChoices("codetype", "codeType", "code_type"),
        serialization_alias="codetype",
    )
    item_code: str = Field(alias="itemCode")
    comment: str


class RequestCodeReuseRequest(BaseModel):
    items: list[CodeReuseItem]

    def as_api_body(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")


class RequestCodeReuseResult(BaseModel):
    """ETA documents a 200 on success; the response body is optional."""

    success: bool = True
    payload: dict | list | None = None


class EGSRequestStatus(str, Enum):
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class EGSRequestType(str, Enum):
    NEW = "New"
    REUSAGE = "Reusage"


class OrderDirection(str, Enum):
    DESCENDING = "Descending"
    ASCENDING = "Ascending"


class SearchEGSCodeUsageQuery(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    item_code: str | None = None
    code_name: str | None = None
    code_description: str | None = None
    parent_level_name: str | None = None
    parent_item_code: str | None = None
    active_from: datetime | str | None = None
    active_to: datetime | str | None = None
    active: bool | None = None
    status: EGSRequestStatus | str | None = None
    request_type: EGSRequestType | str | None = None
    order_directions: OrderDirection | str | None = None
    page_no: int | None = None
    page_size: int | None = None

    def as_query_params(self) -> dict[str, str]:
        mapping: dict[str, object] = {
            "ItemCode": self.item_code,
            "CodeName": self.code_name,
            "CodeDescription": self.code_description,
            "ParentLevelName": self.parent_level_name,
            "ParentItemCode": self.parent_item_code,
            "ActiveFrom": self.active_from,
            "ActiveTo": self.active_to,
            "Active": self.active,
            "Status": self.status,
            "RequestType": self.request_type,
            "OrderDirections": self.order_directions,
            "Pn": self.page_no,
            "Ps": self.page_size,
        }
        params: dict[str, str] = {}
        for key, value in mapping.items():
            if value is None:
                continue
            if isinstance(value, datetime):
                params[key] = _format_eta_datetime(value)
            elif isinstance(value, bool):
                params[key] = str(value).lower()
            elif isinstance(value, Enum):
                params[key] = value.value
            else:
                params[key] = str(value)
        return params


class TaxpayerInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rin: str | None = None
    name: str | None = None
    name_ar: str | None = Field(default=None, alias="nameAr")


class CodeLevel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str | None = None
    name_ar: str | None = Field(default=None, alias="nameAr")


class CodeCategorization(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str | None = None
    name_ar: str | None = Field(default=None, alias="nameAr")
    level1: CodeLevel | None = None
    level2: CodeLevel | None = None
    level3: CodeLevel | None = None
    level4: CodeLevel | None = None


class EGSCodeUsageRequestDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    code_usage_request_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("codeUsageRequestID", "codeUsageRequestId"),
    )
    code_type_name: str | None = Field(default=None, alias="codeTypeName")
    code_id: int | None = Field(default=None, validation_alias=AliasChoices("codeID", "codeId"))
    item_code: str | None = Field(default=None, alias="itemCode")
    code_name: str | None = Field(default=None, alias="codeName")
    description: str | None = None
    parent_code_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("parentCodeID", "parentCodeId"),
    )
    parent_item_code: str | None = Field(default=None, alias="parentItemCode")
    parent_level_name: str | None = Field(default=None, alias="parentLevelName")
    level_name: str | None = Field(default=None, alias="levelName")
    request_creation_date_time_utc: datetime | None = Field(
        default=None,
        alias="requestCreationDateTimeUtc",
    )
    code_creation_date_time_utc: datetime | None = Field(
        default=None,
        alias="codeCreationDateTimeUtc",
    )
    active_from: datetime | None = Field(default=None, alias="activeFrom")
    active_to: datetime | None = Field(default=None, alias="activeTo")
    active: bool | None = None
    status: str | None = None
    owner_taxpayer: TaxpayerInfo | None = Field(default=None, alias="ownerTaxpayer")
    requester_taxpayer: TaxpayerInfo | None = Field(default=None, alias="requesterTaxpayer")
    code_categorization: CodeCategorization | None = Field(
        default=None,
        alias="codeCategorization",
    )


class SearchEGSCodeUsageResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    result: list[EGSCodeUsageRequestDetails] = Field(default_factory=list)

    def __iter__(self):
        return iter(self.result)

    def __len__(self) -> int:
        return len(self.result)


class PublishedCodeDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    code_id: int | None = Field(default=None, validation_alias=AliasChoices("codeID", "codeId", "CodeID"))
    item_code: str | None = Field(default=None, alias="itemCode")
    code_name: str | None = Field(default=None, alias="codeName")
    code_name_ar: str | None = Field(default=None, alias="codeNameAr")
    description: str | None = None
    description_ar: str | None = Field(default=None, alias="descriptionAr")
    active_from: datetime | None = Field(default=None, alias="activeFrom")
    active_to: datetime | None = Field(default=None, alias="activeTo")
    active: bool | None = None
    parent_code_lookup_value: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ParentCodeLookupValue", "parentCodeLookupValue"),
    )
    parent_code_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("ParentCodeID", "parentCodeID", "parentCodeId"),
    )
    parent_item_code: str | None = Field(default=None, alias="parentItemCode")
    code_type_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("codeTypeID", "codeTypeId"),
    )
    code_type_level_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("CodeTypeLevelID", "codeTypeLevelID", "codeTypeLevelId"),
    )
    code_type_level_name_primary_lang: str | None = Field(
        default=None,
        alias="codeTypeLevelNamePrimaryLang",
    )
    code_type_level_name_secondary_lang: str | None = Field(
        default=None,
        alias="codeTypeLevelNameSecondaryLang",
    )
    code_name_primary_lang: str | None = Field(default=None, alias="codeNamePrimaryLang")
    code_name_secondary_lang: str | None = Field(default=None, alias="codeNameSecondaryLang")
    code_description_primary_lang: str | None = Field(
        default=None,
        alias="codeDescriptionPrimaryLang",
    )
    code_description_secondary_lang: str | None = Field(
        default=None,
        alias="codeDescriptionSecondaryLang",
    )
    owner_taxpayer: TaxpayerInfo | None = Field(default=None, alias="ownerTaxpayer")
    code_categorization: CodeCategorization | None = Field(
        default=None,
        alias="codeCategorization",
    )


class UpdateCodeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code_description_primary_lang: str | None = Field(
        default=None,
        alias="codeDescriptionPrimaryLang",
    )
    code_description_secondary_lang: str | None = Field(
        default=None,
        alias="codeDescriptionSecondaryLang",
    )
    active_to: datetime | str | None = Field(default=None, alias="activeTo")
    linked_code: str | None = Field(default=None, alias="linkedCode")

    @field_serializer("active_to")
    def _serialize_active_to(self, value: datetime | str | None) -> str | None:
        if value is None:
            return None
        return _format_eta_datetime(value)

    def as_api_body(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")


class UpdateCodeResult(BaseModel):
    """ETA documents a 200 on success; the response body is optional."""

    success: bool = True
    payload: dict | list | None = None



