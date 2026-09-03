from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from egypt_compliance.models.documents import DocumentSignature


def format_eta_datetime(value: datetime | str) -> str:
    if isinstance(value, str):
        return value
    iso = value.isoformat()
    if iso.endswith("+00:00"):
        return iso[:-6] + "Z"
    return iso


def format_eta_date(value: date | datetime | str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.date().isoformat()
    return value.isoformat()


class ETAModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Address(ETAModel):
    branch_id: str | None = Field(default=None, alias="branchId")
    country: str
    governate: str
    region_city: str = Field(alias="regionCity")
    street: str
    building_number: str = Field(alias="buildingNumber")
    postal_code: str | None = Field(default=None, alias="postalCode")
    floor: str | None = None
    room: str | None = None
    landmark: str | None = None
    additional_information: str | None = Field(default=None, alias="additionalInformation")


class Issuer(ETAModel):
    type: str = "B"
    id: str
    name: str
    address: Address


class Receiver(ETAModel):
    type: str
    id: str | None = None
    name: str | None = None
    address: Address | None = None


class Payment(ETAModel):
    bank_name: str | None = Field(default=None, alias="bankName")
    bank_address: str | None = Field(default=None, alias="bankAddress")
    bank_account_no: str | None = Field(default=None, alias="bankAccountNo")
    bank_account_iban: str | None = Field(default=None, alias="bankAccountIBAN")
    swift_code: str | None = Field(default=None, alias="swiftCode")
    terms: str | None = None


class Delivery(ETAModel):
    approach: str | None = None
    packaging: str | None = None
    date_validity: datetime | date | str | None = Field(default=None, alias="dateValidity")
    export_port: str | None = Field(default=None, alias="exportPort")
    country_of_origin: str | None = Field(default=None, alias="countryOfOrigin")
    gross_weight: float | None = Field(default=None, alias="grossWeight")
    net_weight: float | None = Field(default=None, alias="netWeight")
    terms: str | None = None

    @field_serializer("date_validity")
    def _serialize_date_validity(self, value: datetime | date | str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return format_eta_datetime(value)
        return format_eta_date(value)


class UnitValue(ETAModel):
    currency_sold: str = Field(default="EGP", alias="currencySold")
    amount_egp: float = Field(alias="amountEGP")
    amount_sold: float | None = Field(default=None, alias="amountSold")
    currency_exchange_rate: float | None = Field(default=None, alias="currencyExchangeRate")


class Discount(ETAModel):
    rate: float | None = None
    amount: float | None = None


class TaxableItem(ETAModel):
    tax_type: str = Field(alias="taxType")
    amount: float
    sub_type: str | None = Field(default=None, alias="subType")
    rate: float | None = None


class TaxTotal(ETAModel):
    tax_type: str = Field(alias="taxType")
    amount: float


class InvoiceLine(ETAModel):
    description: str
    item_type: str = Field(alias="itemType")
    item_code: str = Field(alias="itemCode")
    unit_type: str = Field(alias="unitType")
    quantity: float
    unit_value: UnitValue = Field(alias="unitValue")
    sales_total: float = Field(alias="salesTotal")
    total: float
    value_difference: float = Field(default=0, alias="valueDifference")
    total_taxable_fees: float = Field(default=0, alias="totalTaxableFees")
    net_total: float = Field(alias="netTotal")
    items_discount: float = Field(default=0, alias="itemsDiscount")
    discount: Discount | None = None
    taxable_items: list[TaxableItem] | None = Field(default=None, alias="taxableItems")
    internal_code: str | None = Field(default=None, alias="internalCode")
    weight_unit_type: str | None = Field(default=None, alias="weightUnitType")
    weight_quantity: float | None = Field(default=None, alias="weightQuantity")


__all__ = [
    "Address",
    "Delivery",
    "Discount",
    "DocumentSignature",
    "ETAModel",
    "InvoiceLine",
    "Issuer",
    "Payment",
    "Receiver",
    "TaxTotal",
    "TaxableItem",
    "UnitValue",
    "format_eta_date",
    "format_eta_datetime",
]
