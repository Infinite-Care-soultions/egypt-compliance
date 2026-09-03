from egypt_compliance import ETAClientFactory, Environment
from egypt_compliance.config import PREPROD, PROD
from egypt_compliance.factory import PreprodClientCreator, ProdClientCreator


def test_factory_create_preprod_uses_identity_and_api_urls():
    client = ETAClientFactory.create("preprod")
    assert client.config.environment is Environment.PREPROD
    assert client.config.identity_base_url == "https://id.preprod.eta.gov.eg"
    assert client.config.api_base_url == "https://api.preprod.invoicing.eta.gov.eg"
    assert client.config.token_url == "https://id.preprod.eta.gov.eg/connect/token"
    assert client.config.document_types_url == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documenttypes"
    )
    assert client.config.document_type_url(45) == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documenttypes/45"
    )
    assert client.config.document_type_version_url(45, 454) == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documenttypes/45/versions/454"
    )
    assert client.config.notifications_url == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/notifications/taxpayer"
    )
    assert client.config.create_egs_code_usage_url == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/codetypes/requests/codes"
    )
    assert client.config.search_egs_code_usage_requests_url == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/codetypes/requests/my"
    )
    assert client.config.request_code_reuse_url == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/codetypes/requests/codeusages"
    )
    assert client.config.code_details_url("EGS", "EG-113317713-1234") == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/codetypes/EGS/codes/EG-113317713-1234"
    )
    assert client.config.update_code_url("EGS", "EG-113317713-1234") == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/codetypes/EGS/codes/EG-113317713-1234"
    )
    assert client.config.document_submissions_url == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documentsubmissions"
    )
    assert client.config.document_state_url("F9D425P6DS7D8IU") == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documents/state/F9D425P6DS7D8IU/state"
    )
    assert client.config.recent_documents_url == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documents/recent"
    )
    assert client.config.search_documents_url == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documents/search"
    )
    assert client.config.document_package_requests_url == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documentpackages/requests"
    )
    assert client.config.document_package_url("45KJHHA62D") == (
        "https://api.preprod.invoicing.eta.gov.eg/api/v1.0/documentpackages/45KJHHA62D"
    )


def test_factory_create_prod_uses_identity_and_api_urls():
    client = ETAClientFactory.create(Environment.PROD)
    assert client.config.environment is Environment.PROD
    assert client.config.identity_base_url == "https://id.eta.gov.eg"
    assert client.config.api_base_url == "https://api.invoicing.eta.gov.eg"
    assert client.config.token_url == "https://id.eta.gov.eg/connect/token"
    assert client.config.document_types_url == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/documenttypes"
    )
    assert client.config.document_type_url(45) == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/documenttypes/45"
    )
    assert client.config.document_type_version_url(45, 454) == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/documenttypes/45/versions/454"
    )
    assert client.config.notifications_url == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/notifications/taxpayer"
    )
    assert client.config.create_egs_code_usage_url == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/codetypes/requests/codes"
    )
    assert client.config.search_egs_code_usage_requests_url == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/codetypes/requests/my"
    )
    assert client.config.request_code_reuse_url == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/codetypes/requests/codeusages"
    )
    assert client.config.code_details_url("EGS", "EG-113317713-1234") == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/codetypes/EGS/codes/EG-113317713-1234"
    )
    assert client.config.update_code_url("EGS", "EG-113317713-1234") == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/codetypes/EGS/codes/EG-113317713-1234"
    )
    assert client.config.document_submissions_url == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/documentsubmissions"
    )
    assert client.config.document_state_url("F9D425P6DS7D8IU") == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/documents/state/F9D425P6DS7D8IU/state"
    )
    assert client.config.recent_documents_url == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/documents/recent"
    )
    assert client.config.search_documents_url == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/documents/search"
    )
    assert client.config.document_package_requests_url == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/documentpackages/requests"
    )
    assert client.config.document_package_url("45KJHHA62D") == (
        "https://api.invoicing.eta.gov.eg/api/v1.0/documentpackages/45KJHHA62D"
    )


def test_factory_rejects_unknown_environment():
    try:
        ETAClientFactory.create("staging")
    except ValueError as exc:
        assert "Unknown environment" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_creators_instantiate_environment_specific_clients():
    preprod = PreprodClientCreator().create_client()
    prod = ProdClientCreator().create_client()
    assert preprod.config == PREPROD
    assert prod.config == PROD
