from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from egypt_compliance.signing.canonicalize import (
    canonicalize_each,
    extract_documents,
    load_json_document,
)


class SignatureResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    canonical: str
    signature: str
    document: dict
    documents: list[dict] = Field(default_factory=list)
    canonical_list: list[str] = Field(default_factory=list)

    @property
    def submission(self) -> dict:
        return {"documents": self.documents or [self.document]}


class DocumentSigner(ABC):
    """Signs ETA canonical document bytes as CAdES-BES (Base64)."""

    signature_type: str = "I"
    signature_field: str = "signatureType"

    @abstractmethod
    def sign_canonical(self, canonical: str, *, signing_time: datetime | None = None) -> str:
        raise NotImplementedError

    def sign_document(
        self,
        source: str | Path | dict | bytes,
        *,
        signing_time: datetime | None = None,
    ) -> SignatureResult:
        payload = load_json_document(source)
        documents = [deepcopy(item) for item in extract_documents(payload)]
        signed_documents: list[dict] = []
        canonical_list: list[str] = []
        signatures: list[str] = []
        for document in documents:
            document.pop("signatures", None)
            canonical = canonicalize_each(document)[0]
            cades = self.sign_canonical(canonical, signing_time=signing_time)
            document["signatures"] = [{self.signature_field: self.signature_type, "value": cades}]
            signed_documents.append(document)
            canonical_list.append(canonical)
            signatures.append(cades)
        return SignatureResult(
            canonical=canonical_list[0],
            signature=signatures[0],
            document=signed_documents[0],
            documents=signed_documents,
            canonical_list=canonical_list,
        )

    def sign_file(self, path: str | Path, *, signing_time: datetime | None = None) -> SignatureResult:
        return self.sign_document(Path(path), signing_time=signing_time)
