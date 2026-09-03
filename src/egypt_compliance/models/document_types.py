from base64 import b64decode
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentTypeVersion(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    description: str | None = None
    version_number: Decimal = Field(alias="versionNumber")
    status: str
    active_from: datetime = Field(alias="activeFrom")
    active_to: datetime | None = Field(default=None, alias="activeTo")

    @field_validator("version_number", mode="before")
    @classmethod
    def _coerce_version_number(cls, value: object) -> object:
        if isinstance(value, float):
            return Decimal(str(value))
        return value


class WorkflowParameter(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    parameter: str
    value: Decimal
    active_from: datetime = Field(alias="activeFrom")
    active_to: datetime | None = Field(default=None, alias="activeTo")

    @field_validator("value", mode="before")
    @classmethod
    def _coerce_value(cls, value: object) -> object:
        if isinstance(value, float):
            return Decimal(str(value))
        return value


class DocumentType(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    description: str | None = None
    active_from: datetime = Field(alias="activeFrom")
    active_to: datetime | None = Field(default=None, alias="activeTo")
    document_type_versions: list[DocumentTypeVersion] = Field(
        default_factory=list,
        alias="documentTypeVersions",
    )
    workflow_parameters: list[WorkflowParameter] = Field(
        default_factory=list,
        alias="workflowParameters",
    )


class DocumentTypesResult(BaseModel):
    result: list[DocumentType] = Field(default_factory=list)

    def __iter__(self):
        return iter(self.result)

    def __len__(self) -> int:
        return len(self.result)


class DocumentTypeVersionDetail(BaseModel):
    """Full document type version including JSON/XML schemas."""

    model_config = ConfigDict(populate_by_name=True)

    id: int | None = None
    type_name: str = Field(alias="typeName")
    name: str
    description: str | None = None
    version_number: Decimal = Field(alias="versionNumber")
    status: str
    active_from: datetime = Field(alias="activeFrom")
    active_to: datetime | None = Field(default=None, alias="activeTo")
    json_schema: str | None = Field(default=None, alias="jsonSchema")
    xml_schema: str | None = Field(default=None, alias="xmlSchema")

    @field_validator("version_number", mode="before")
    @classmethod
    def _coerce_version_number(cls, value: object) -> object:
        if isinstance(value, float):
            return Decimal(str(value))
        return value

    def decode_json_schema(self) -> str | None:
        return _decode_schema(self.json_schema)

    def decode_xml_schema(self) -> str | None:
        return _decode_schema(self.xml_schema)


def _decode_schema(value: str | None) -> str | None:
    if not value:
        return None
    return b64decode(value).decode("utf-8")

