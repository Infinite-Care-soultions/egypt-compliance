from __future__ import annotations

import base64
from datetime import datetime

import httpx

from egypt_compliance.config import ETAConfig
from egypt_compliance.exceptions import ETAAPIError, ETAAuthenticationError, ETAError
from egypt_compliance.models.document_detail import DocumentExtended, DocumentPrintout
from egypt_compliance.models.document_packages import (
    DocumentPackageDownload,
    DocumentPackageItemCode,
    DocumentPackageQueryParameters,
    PackageRequestsQuery,
    PackageRequestsResult,
    RequestDocumentPackageRequest,
    RequestDocumentPackageResult,
)
from egypt_compliance.models.document_types import (
    DocumentType,
    DocumentTypesResult,
    DocumentTypeVersionDetail,
)
from egypt_compliance.models.documents import (
    CancelDocumentRequest,
    CancelDocumentResult,
    RejectDocumentRequest,
    RejectDocumentResult,
    SubmitDocumentsRequest,
    SubmitDocumentsResult,
    SubmittedDocument,
)
from egypt_compliance.models.egs_codes import (
    CodeReuseItem,
    CreateEGSCodeUsageRequest,
    CreateEGSCodeUsageResult,
    EGSCodeUsageItem,
    EGSRequestStatus,
    EGSRequestType,
    OrderDirection,
    PublishedCodeDetails,
    RequestCodeReuseRequest,
    RequestCodeReuseResult,
    SearchEGSCodeUsageQuery,
    SearchEGSCodeUsageResult,
    UpdateCodeRequest,
    UpdateCodeResult,
)
from egypt_compliance.models.notifications import (
    NotificationQuery,
    NotificationsResult,
    NotificationType,
)
from egypt_compliance.models.recent_documents import (
    RecentDocumentsQuery,
    RecentDocumentsResult,
)
from egypt_compliance.models.search_documents import (
    SearchDocumentsQuery,
    SearchDocumentsResult,
)
from egypt_compliance.models.submission import GetSubmissionQuery, GetSubmissionResult
from egypt_compliance.models.token import LoginCredentials, Token


class ETAClient:
    """Synchronous ETA eInvoicing client."""

    def __init__(
        self,
        config: ETAConfig,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.config = config
        self._http = http_client
        self._owns_client = http_client is None

    def login(
        self,
        client_id: str,
        client_secret: str,
        *,
        scope: str = "InvoicingAPI",
        on_behalf_of: str | None = None,
    ) -> Token:
        credentials = LoginCredentials(
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
            on_behalf_of=on_behalf_of,
        )
        headers = self._auth_headers(credentials)
        data = {
            "grant_type": "client_credentials",
            "scope": credentials.scope,
        }

        try:
            response = self._client().post(
                self.config.token_url,
                headers=headers,
                data=data,
            )
        except httpx.RequestError as exc:
            raise ETAError(f"Failed to reach ETA identity service: {exc}") from exc

        if response.status_code != 200:
            raise self._authentication_error(response)

        return Token.model_validate(response.json())

    def get_document_types(
        self,
        token: Token | str,
        *,
        accept_language: str = "en",
    ) -> DocumentTypesResult:
        payload = self._request_json(
            "GET",
            self.config.document_types_url,
            token=token,
            accept_language=accept_language,
        )
        if isinstance(payload, list):
            payload = {"result": payload}
        return DocumentTypesResult.model_validate(payload)

    def get_document_type(
        self,
        token: Token | str,
        document_type_id: int,
        *,
        accept_language: str = "en",
    ) -> DocumentType:
        payload = self._request_json(
            "GET",
            self.config.document_type_url(document_type_id),
            token=token,
            accept_language=accept_language,
        )
        if isinstance(payload, dict) and "result" in payload and "id" not in payload:
            payload = payload["result"]
        return DocumentType.model_validate(payload)

    def get_document_type_version(
        self,
        token: Token | str,
        document_type_id: int,
        version_id: int,
        *,
        accept_language: str = "en",
    ) -> DocumentTypeVersionDetail:
        payload = self._request_json(
            "GET",
            self.config.document_type_version_url(document_type_id, version_id),
            token=token,
            accept_language=accept_language,
        )
        if isinstance(payload, dict) and "result" in payload and "name" not in payload:
            payload = payload["result"]
        return DocumentTypeVersionDetail.model_validate(payload)

    def get_notifications(
        self,
        token: Token | str,
        query: NotificationQuery | None = None,
        *,
        date_from: datetime | str | None = None,
        date_to: datetime | str | None = None,
        type: NotificationType | int | str | None = None,
        language: str | None = None,
        status: str | None = None,
        channel: str | None = None,
        page_no: int | None = None,
        page_size: int | None = None,
        accept_language: str = "en",
    ) -> NotificationsResult:
        filters = query or NotificationQuery(
            date_from=date_from,
            date_to=date_to,
            type=type,
            language=language,
            status=status,
            channel=channel,
            page_no=page_no,
            page_size=page_size,
        )
        payload = self._request_json(
            "GET",
            self.config.notifications_url,
            token=token,
            accept_language=accept_language,
            params=filters.as_query_params(),
        )
        if isinstance(payload, list):
            payload = {"result": payload}
        return NotificationsResult.model_validate(payload)

    def create_egs_code_usage(
        self,
        token: Token | str,
        items: list[EGSCodeUsageItem] | CreateEGSCodeUsageRequest,
        *,
        accept_language: str = "en",
    ) -> CreateEGSCodeUsageResult:
        request = (
            items
            if isinstance(items, CreateEGSCodeUsageRequest)
            else CreateEGSCodeUsageRequest(items=items)
        )
        payload = self._request_json(
            "POST",
            self.config.create_egs_code_usage_url,
            token=token,
            accept_language=accept_language,
            json=request.as_api_body(),
        )
        if payload is None:
            return CreateEGSCodeUsageResult(success=True)
        if isinstance(payload, (dict, list)):
            return CreateEGSCodeUsageResult(success=True, payload=payload)
        return CreateEGSCodeUsageResult(success=True)

    def search_egs_code_usage_requests(
        self,
        token: Token | str,
        query: SearchEGSCodeUsageQuery | None = None,
        *,
        item_code: str | None = None,
        code_name: str | None = None,
        code_description: str | None = None,
        parent_level_name: str | None = None,
        parent_item_code: str | None = None,
        active_from: datetime | str | None = None,
        active_to: datetime | str | None = None,
        active: bool | None = None,
        status: EGSRequestStatus | str | None = None,
        request_type: EGSRequestType | str | None = None,
        order_directions: OrderDirection | str | None = None,
        page_no: int | None = None,
        page_size: int | None = None,
        accept_language: str = "en",
    ) -> SearchEGSCodeUsageResult:
        filters = query or SearchEGSCodeUsageQuery(
            item_code=item_code,
            code_name=code_name,
            code_description=code_description,
            parent_level_name=parent_level_name,
            parent_item_code=parent_item_code,
            active_from=active_from,
            active_to=active_to,
            active=active,
            status=status,
            request_type=request_type,
            order_directions=order_directions,
            page_no=page_no,
            page_size=page_size,
        )
        payload = self._request_json(
            "GET",
            self.config.search_egs_code_usage_requests_url,
            token=token,
            accept_language=accept_language,
            params=filters.as_query_params(),
        )
        if payload is None:
            payload = []
        if isinstance(payload, list):
            payload = {"result": payload}
        elif isinstance(payload, dict) and "result" not in payload:
            payload = {"result": [payload]}
        return SearchEGSCodeUsageResult.model_validate(payload)

    def request_code_reuse(
        self,
        token: Token | str,
        items: list[CodeReuseItem] | RequestCodeReuseRequest,
        *,
        accept_language: str = "en",
    ) -> RequestCodeReuseResult:
        request = (
            items
            if isinstance(items, RequestCodeReuseRequest)
            else RequestCodeReuseRequest(items=items)
        )
        payload = self._request_json(
            "PUT",
            self.config.request_code_reuse_url,
            token=token,
            accept_language=accept_language,
            json=request.as_api_body(),
        )
        if payload is None:
            return RequestCodeReuseResult(success=True)
        if isinstance(payload, (dict, list)):
            return RequestCodeReuseResult(success=True, payload=payload)
        return RequestCodeReuseResult(success=True)

    def get_code_details(
        self,
        token: Token | str,
        item_code: str,
        *,
        code_type: str = "EGS",
        accept_language: str = "en",
    ) -> PublishedCodeDetails:
        payload = self._request_json(
            "GET",
            self.config.code_details_url(code_type, item_code),
            token=token,
            accept_language=accept_language,
        )
        if (
            isinstance(payload, dict)
            and "result" in payload
            and "codeID" not in payload
            and "codeId" not in payload
        ):
            payload = payload["result"]
        return PublishedCodeDetails.model_validate(payload)

    def update_code(
        self,
        token: Token | str,
        item_code: str,
        updates: UpdateCodeRequest | None = None,
        *,
        code_type: str = "EGS",
        code_description_primary_lang: str | None = None,
        code_description_secondary_lang: str | None = None,
        active_to: datetime | str | None = None,
        linked_code: str | None = None,
        accept_language: str = "en",
    ) -> UpdateCodeResult:
        request = updates or UpdateCodeRequest(
            code_description_primary_lang=code_description_primary_lang,
            code_description_secondary_lang=code_description_secondary_lang,
            active_to=active_to,
            linked_code=linked_code,
        )
        payload = self._request_json(
            "PUT",
            self.config.update_code_url(code_type, item_code),
            token=token,
            accept_language=accept_language,
            json=request.as_api_body(),
        )
        if payload is None:
            return UpdateCodeResult(success=True)
        if isinstance(payload, (dict, list)):
            return UpdateCodeResult(success=True, payload=payload)
        return UpdateCodeResult(success=True)

    def submit_documents(
        self,
        token: Token | str,
        documents: list[SubmittedDocument | dict] | SubmitDocumentsRequest,
        *,
        accept_language: str = "en",
    ) -> SubmitDocumentsResult:
        if isinstance(documents, SubmitDocumentsRequest):
            if not documents.documents:
                raise ValueError("documents must contain at least one document")
            body = documents.as_api_body()
        else:
            if not documents:
                raise ValueError("documents must contain at least one document")
            body = {
                "documents": [
                    document.model_dump(by_alias=True, exclude_none=True, mode="json")
                    if isinstance(document, SubmittedDocument)
                    else document
                    for document in documents
                ]
            }
        payload = self._request_json(
            "POST",
            self.config.document_submissions_url,
            token=token,
            accept_language=accept_language,
            json=body,
            ok_statuses=(200, 202),
        )
        if payload is None:
            return SubmitDocumentsResult()
        return SubmitDocumentsResult.model_validate(payload)

    def cancel_document(
        self,
        token: Token | str,
        uuid: str,
        reason: str | CancelDocumentRequest,
        *,
        status: str = "cancelled",
        accept_language: str = "en",
    ) -> CancelDocumentResult:
        request = (
            reason
            if isinstance(reason, CancelDocumentRequest)
            else CancelDocumentRequest(status=status, reason=reason)
        )
        if not uuid or not str(uuid).strip():
            raise ValueError("uuid is required")
        if not request.reason or not request.reason.strip():
            raise ValueError("reason is required")
        payload = self._request_json(
            "PUT",
            self.config.document_state_url(str(uuid).strip()),
            token=token,
            accept_language=accept_language,
            json=request.as_api_body(),
        )
        if payload is None:
            return CancelDocumentResult(success=True)
        if isinstance(payload, (dict, list)):
            return CancelDocumentResult(success=True, payload=payload)
        return CancelDocumentResult(success=True)

    def reject_document(
        self,
        token: Token | str,
        uuid: str,
        reason: str | RejectDocumentRequest,
        *,
        status: str = "rejected",
        accept_language: str = "en",
    ) -> RejectDocumentResult:
        request = (
            reason
            if isinstance(reason, RejectDocumentRequest)
            else RejectDocumentRequest(status=status, reason=reason)
        )
        if not uuid or not str(uuid).strip():
            raise ValueError("uuid is required")
        if not request.reason or not request.reason.strip():
            raise ValueError("reason is required")
        payload = self._request_json(
            "PUT",
            self.config.document_state_url(str(uuid).strip()),
            token=token,
            accept_language=accept_language,
            json=request.as_api_body(),
        )
        if payload is None:
            return RejectDocumentResult(success=True)
        if isinstance(payload, (dict, list)):
            return RejectDocumentResult(success=True, payload=payload)
        return RejectDocumentResult(success=True)

    def get_recent_documents(
        self,
        token: Token | str,
        query: RecentDocumentsQuery | None = None,
        *,
        page_no: int | None = None,
        page_size: int | None = None,
        submission_date_from: datetime | str | None = None,
        submission_date_to: datetime | str | None = None,
        issue_date_from: datetime | str | None = None,
        issue_date_to: datetime | str | None = None,
        direction: str | None = None,
        status: str | None = None,
        document_type: str | None = None,
        receiver_type: str | None = None,
        receiver_id: str | None = None,
        issuer_type: str | None = None,
        issuer_id: str | None = None,
        accept_language: str = "en",
    ) -> RecentDocumentsResult:
        filters = query or RecentDocumentsQuery(
            page_no=page_no,
            page_size=page_size,
            submission_date_from=submission_date_from,
            submission_date_to=submission_date_to,
            issue_date_from=issue_date_from,
            issue_date_to=issue_date_to,
            direction=direction,
            status=status,
            document_type=document_type,
            receiver_type=receiver_type,
            receiver_id=receiver_id,
            issuer_type=issuer_type,
            issuer_id=issuer_id,
        )
        payload = self._request_json(
            "GET",
            self.config.recent_documents_url,
            token=token,
            accept_language=accept_language,
            params=filters.as_query_params(),
        )
        if payload is None:
            payload = {"result": []}
        if isinstance(payload, list):
            payload = {"result": payload}
        return RecentDocumentsResult.model_validate(payload)

    def search_documents(
        self,
        token: Token | str,
        query: SearchDocumentsQuery | None = None,
        *,
        submission_date_from: datetime | str | None = None,
        submission_date_to: datetime | str | None = None,
        issue_date_from: datetime | str | None = None,
        issue_date_to: datetime | str | None = None,
        continuation_token: str | None = None,
        page_size: int | None = None,
        direction: str | None = None,
        status: str | None = None,
        document_type: str | None = None,
        receiver_type: str | None = None,
        receiver_id: str | None = None,
        issuer_type: str | None = None,
        issuer_id: str | None = None,
        uuid: str | None = None,
        internal_id: str | None = None,
        accept_language: str = "en",
    ) -> SearchDocumentsResult:
        filters = query or SearchDocumentsQuery(
            submission_date_from=submission_date_from,
            submission_date_to=submission_date_to,
            issue_date_from=issue_date_from,
            issue_date_to=issue_date_to,
            continuation_token=continuation_token,
            page_size=page_size,
            direction=direction,
            status=status,
            document_type=document_type,
            receiver_type=receiver_type,
            receiver_id=receiver_id,
            issuer_type=issuer_type,
            issuer_id=issuer_id,
            uuid=uuid,
            internal_id=internal_id,
        )
        payload = self._request_json(
            "GET",
            self.config.search_documents_url,
            token=token,
            accept_language=accept_language,
            params=filters.as_query_params(),
        )
        if payload is None:
            payload = {"result": []}
        if isinstance(payload, list):
            payload = {"result": payload}
        return SearchDocumentsResult.model_validate(payload)

    def request_document_package(
        self,
        token: Token | str,
        request: RequestDocumentPackageRequest | None = None,
        *,
        type: str = "full",
        format: str = "JSON",
        query_parameters: DocumentPackageQueryParameters | None = None,
        date_from: datetime | str | None = None,
        date_to: datetime | str | None = None,
        document_type_names: list[str] | None = None,
        statuses: list[str] | None = None,
        products_internal_codes: list[str] | None = None,
        receiver_sender_type: str | int | None = None,
        receiver_sender_id: str | None = None,
        branch_number: str | None = None,
        item_codes: list[DocumentPackageItemCode] | None = None,
        truncate_if_exceeded: bool | None = None,
        represented_taxpayer_filter_type: int | None = None,
        representee_rin: str | None = None,
        accept_language: str = "en",
    ) -> RequestDocumentPackageResult:
        if request is None:
            query = query_parameters or DocumentPackageQueryParameters(
                date_from=date_from,
                date_to=date_to,
                document_type_names=document_type_names,
                statuses=statuses,
                products_internal_codes=products_internal_codes,
                receiver_sender_type=receiver_sender_type,
                receiver_sender_id=receiver_sender_id,
                branch_number=branch_number,
                item_codes=item_codes,
                truncate_if_exceeded=truncate_if_exceeded,
            )
            request = RequestDocumentPackageRequest(
                type=type,
                format=format,
                query_parameters=query,
                represented_taxpayer_filter_type=represented_taxpayer_filter_type,
                representee_rin=representee_rin,
            )
        if not request.query_parameters.date_from or not request.query_parameters.date_to:
            raise ValueError("date_from and date_to are required")
        payload = self._request_json(
            "POST",
            self.config.document_package_requests_url,
            token=token,
            accept_language=accept_language,
            json=request.as_api_body(),
            ok_statuses=(200, 201),
        )
        if payload is None:
            return RequestDocumentPackageResult()
        if isinstance(payload, str):
            return RequestDocumentPackageResult(package_id=payload)
        if isinstance(payload, dict):
            inner = payload.get("result")
            if "packageId" not in payload and "packageID" not in payload and "package_id" not in payload:
                if isinstance(inner, dict):
                    payload = inner
                elif isinstance(inner, str):
                    return RequestDocumentPackageResult(package_id=inner)
            return RequestDocumentPackageResult.model_validate(payload)
        return RequestDocumentPackageResult()

    def get_package_requests(
        self,
        token: Token | str,
        query: PackageRequestsQuery | None = None,
        *,
        page_no: int | None = None,
        page_size: int | None = None,
        accept_language: str = "en",
    ) -> PackageRequestsResult:
        filters = query or PackageRequestsQuery(page_no=page_no, page_size=page_size)
        payload = self._request_json(
            "GET",
            self.config.document_package_requests_url,
            token=token,
            accept_language=accept_language,
            params=filters.as_query_params(),
        )
        if payload is None:
            payload = {"result": []}
        if isinstance(payload, list):
            payload = {"result": payload}
        return PackageRequestsResult.model_validate(payload)

    def get_document_package(
        self,
        token: Token | str,
        package_id: str,
        *,
        byte_range: str | None = None,
        accept_language: str = "en",
    ) -> DocumentPackageDownload:
        if not package_id or not str(package_id).strip():
            raise ValueError("package_id is required")
        package_id = str(package_id).strip()
        extra_headers: dict[str, str] = {}
        if byte_range:
            extra_headers["Range"] = byte_range
        response = self._request_raw(
            "GET",
            self.config.document_package_url(package_id),
            token=token,
            accept_language=accept_language,
            accept="application/octet-stream",
            extra_headers=extra_headers or None,
            ok_statuses=(200, 204, 206),
        )
        if response.status_code == 204 or not response.content:
            return DocumentPackageDownload(package_id=package_id, ready=False)
        content_length_header = response.headers.get("Content-Length")
        content_length = None
        if content_length_header:
            try:
                content_length = int(content_length_header)
            except ValueError:
                content_length = None
        return DocumentPackageDownload(
            package_id=package_id,
            ready=True,
            content=response.content,
            content_type=response.headers.get("Content-Type"),
            content_length=content_length,
        )

    def get_document(
        self,
        token: Token | str,
        uuid: str,
        *,
        accept_language: str = "en",
    ) -> DocumentExtended:
        if not uuid or not str(uuid).strip():
            raise ValueError("uuid is required")
        payload = self._request_json(
            "GET",
            self.config.document_raw_url(str(uuid).strip()),
            token=token,
            accept_language=accept_language,
        )
        if payload is None:
            return DocumentExtended()
        if (
            isinstance(payload, dict)
            and "uuid" not in payload
            and isinstance(payload.get("result"), dict)
        ):
            payload = payload["result"]
        return DocumentExtended.model_validate(payload)

    def get_submission(
        self,
        token: Token | str,
        uuid: str,
        query: GetSubmissionQuery | None = None,
        *,
        page_no: int | None = None,
        page_size: int | None = None,
        accept_language: str = "en",
    ) -> GetSubmissionResult:
        if not uuid or not str(uuid).strip():
            raise ValueError("uuid is required")
        filters = query or GetSubmissionQuery(page_no=page_no, page_size=page_size)
        payload = self._request_json(
            "GET",
            self.config.document_submission_url(str(uuid).strip()),
            token=token,
            accept_language=accept_language,
            params=filters.as_query_params(),
        )
        if payload is None:
            return GetSubmissionResult()
        if (
            isinstance(payload, dict)
            and "uuid" not in payload
            and isinstance(payload.get("result"), dict)
        ):
            payload = payload["result"]
        return GetSubmissionResult.model_validate(payload)

    def get_document_printout(
        self,
        token: Token | str,
        uuid: str,
        *,
        accept_language: str = "en",
    ) -> DocumentPrintout:
        if not uuid or not str(uuid).strip():
            raise ValueError("uuid is required")
        uuid = str(uuid).strip()
        response = self._request_raw(
            "GET",
            self.config.document_pdf_url(uuid),
            token=token,
            accept_language=accept_language,
            accept="application/pdf",
            ok_statuses=(200,),
        )
        content_length_header = response.headers.get("Content-Length")
        content_length = None
        if content_length_header:
            try:
                content_length = int(content_length_header)
            except ValueError:
                content_length = None
        return DocumentPrintout(
            uuid=uuid,
            content=response.content,
            content_type=response.headers.get("Content-Type"),
            content_length=content_length,
        )

    def close(self) -> None:
        if self._owns_client and self._http is not None:
            self._http.close()
            self._http = None

    def __enter__(self) -> ETAClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _client(self) -> httpx.Client:
        if self._http is None:
            self._http = httpx.Client()
        return self._http

    @staticmethod
    def _auth_headers(credentials: LoginCredentials) -> dict[str, str]:
        basic = base64.b64encode(
            f"{credentials.client_id}:{credentials.client_secret}".encode("utf-8")
        ).decode("ascii")
        headers = {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        if credentials.on_behalf_of:
            headers["onbehalfof"] = credentials.on_behalf_of
        return headers

    def _request_raw(
        self,
        method: str,
        url: str,
        *,
        token: Token | str,
        accept_language: str = "en",
        accept: str = "application/json",
        params: dict[str, str] | None = None,
        json: object | None = None,
        extra_headers: dict[str, str] | None = None,
        ok_statuses: tuple[int, ...] = (200,),
    ) -> httpx.Response:
        access_token = token.access_token if isinstance(token, Token) else token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": accept,
            "Accept-Language": accept_language,
        }
        if json is not None:
            headers["Content-Type"] = "application/json"
        if extra_headers:
            headers.update(extra_headers)
        try:
            response = self._client().request(
                method,
                url,
                headers=headers,
                params=params or None,
                json=json,
            )
        except httpx.RequestError as exc:
            raise ETAError(f"Failed to reach ETA API: {exc}") from exc

        if response.status_code == 401:
            raise self._authentication_error(response)
        if response.status_code not in ok_statuses:
            raise self._api_error(response)
        return response

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        token: Token | str,
        accept_language: str = "en",
        params: dict[str, str] | None = None,
        json: object | None = None,
        ok_statuses: tuple[int, ...] = (200,),
    ) -> object:
        response = self._request_raw(
            method,
            url,
            token=token,
            accept_language=accept_language,
            params=params,
            json=json,
            ok_statuses=ok_statuses,
        )
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return None

    @staticmethod
    def _api_error(response: httpx.Response) -> ETAAPIError:
        payload: dict[str, object] = {}
        try:
            parsed = response.json()
            if isinstance(parsed, dict):
                payload = parsed
        except ValueError:
            pass

        error = payload.get("error")
        if isinstance(error, dict):
            code = error.get("code")
            message = error.get("message") or response.text or f"ETA API failed with status {response.status_code}"
            return ETAAPIError(
                str(message),
                code=str(code) if code is not None else None,
                target=str(error["target"]) if error.get("target") is not None else None,
                status_code=response.status_code,
                details=list(error["details"]) if isinstance(error.get("details"), list) else [],
            )
        return ETAAPIError(
            response.text or f"ETA API failed with status {response.status_code}",
            status_code=response.status_code,
        )

    @staticmethod
    def _authentication_error(response: httpx.Response) -> ETAAuthenticationError:
        payload: dict[str, object] = {}
        try:
            parsed = response.json()
            if isinstance(parsed, dict):
                payload = parsed
        except ValueError:
            pass

        error = payload.get("error")
        error_description = payload.get("error_description")
        if isinstance(error, dict):
            message = str(
                error.get("message")
                or error.get("code")
                or response.text
                or f"ETA request failed with status {response.status_code}"
            )
            code = error.get("code")
            return ETAAuthenticationError(
                message,
                error=str(code) if code is not None else None,
                error_description=message,
                status_code=response.status_code,
            )
        message = (
            str(error_description)
            if error_description
            else str(error)
            if error
            else (response.text or f"ETA login failed with status {response.status_code}")
        )
        return ETAAuthenticationError(
            message,
            error=str(error) if error is not None else None,
            error_description=str(error_description) if error_description is not None else None,
            status_code=response.status_code,
        )
