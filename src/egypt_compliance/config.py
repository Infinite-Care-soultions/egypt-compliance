from enum import Enum
from urllib.parse import quote

from pydantic import BaseModel


class Environment(str, Enum):
    PREPROD = "preprod"
    PROD = "prod"


class ETAConfig(BaseModel):
    environment: Environment
    identity_base_url: str
    api_base_url: str

    @property
    def token_url(self) -> str:
        return f"{self.identity_base_url.rstrip('/')}/connect/token"

    def api_url(self, path: str) -> str:
        return f"{self.api_base_url.rstrip('/')}/{path.lstrip('/')}"

    @property
    def document_types_url(self) -> str:
        return self.api_url("/api/v1.0/documenttypes")

    def document_type_url(self, document_type_id: int) -> str:
        return self.api_url(f"/api/v1.0/documenttypes/{document_type_id}")

    def document_type_version_url(self, document_type_id: int, version_id: int) -> str:
        return self.api_url(f"/api/v1.0/documenttypes/{document_type_id}/versions/{version_id}")

    @property
    def notifications_url(self) -> str:
        return self.api_url("/api/v1.0/notifications/taxpayer")

    @property
    def create_egs_code_usage_url(self) -> str:
        return self.api_url("/api/v1.0/codetypes/requests/codes")

    @property
    def search_egs_code_usage_requests_url(self) -> str:
        return self.api_url("/api/v1.0/codetypes/requests/my")

    @property
    def request_code_reuse_url(self) -> str:
        return self.api_url("/api/v1.0/codetypes/requests/codeusages")

    def code_details_url(self, code_type: str, item_code: str) -> str:
        return self.api_url(
            f"/api/v1.0/codetypes/{quote(code_type, safe='')}/codes/{quote(item_code, safe='-._~')}"
        )

    def update_code_url(self, code_type: str, item_code: str) -> str:
        return self.code_details_url(code_type, item_code)

    @property
    def document_submissions_url(self) -> str:
        return self.api_url("/api/v1.0/documentsubmissions")

    def document_state_url(self, uuid: str) -> str:
        return self.api_url(f"/api/v1.0/documents/state/{quote(uuid, safe='-._~')}/state")

    @property
    def recent_documents_url(self) -> str:
        return self.api_url("/api/v1.0/documents/recent")

    @property
    def search_documents_url(self) -> str:
        return self.api_url("/api/v1.0/documents/search")


PREPROD = ETAConfig(
    environment=Environment.PREPROD,
    identity_base_url="https://id.preprod.eta.gov.eg",
    api_base_url="https://api.preprod.invoicing.eta.gov.eg",
)

PROD = ETAConfig(
    environment=Environment.PROD,
    identity_base_url="https://id.eta.gov.eg",
    api_base_url="https://api.invoicing.eta.gov.eg",
)

ENVIRONMENTS: dict[Environment, ETAConfig] = {
    Environment.PREPROD: PREPROD,
    Environment.PROD: PROD,
}
