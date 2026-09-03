from __future__ import annotations

from base64 import b64encode
from datetime import datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12

from egypt_compliance.exceptions import ETASigningError
from egypt_compliance.signing.cades import build_cades_bes, sign_with_private_key
from egypt_compliance.signing.signer import DocumentSigner


def _read_bytes(value: str | Path | bytes) -> bytes:
    if isinstance(value, bytes):
        return value
    return Path(value).read_bytes()


def load_pem_certificate(certificate: str | Path | bytes | x509.Certificate) -> x509.Certificate:
    if isinstance(certificate, x509.Certificate):
        return certificate
    return x509.load_pem_x509_certificate(_read_bytes(certificate))


def load_pem_private_key(private_key: str | Path | bytes, password: str | bytes | None = None):
    if not isinstance(private_key, str | Path | bytes):
        return private_key
    secret = None if password is None else (password.encode("utf-8") if isinstance(password, str) else password)
    return serialization.load_pem_private_key(_read_bytes(private_key), password=secret)


def load_pfx(pfx: str | Path | bytes, password: str | bytes | None = None):
    secret = b"" if password is None else (password.encode("utf-8") if isinstance(password, str) else password)
    key, certificate, _extra = pkcs12.load_key_and_certificates(_read_bytes(pfx), secret)
    if key is None or certificate is None:
        raise ETASigningError("PFX/PKCS#12 file must contain a private key and certificate")
    return key, certificate


class SoftwareSigner(DocumentSigner):
    def __init__(self, certificate: x509.Certificate, private_key, *, signature_field: str = "signatureType") -> None:
        self.certificate = certificate
        self.private_key = private_key
        self.signature_field = signature_field

    def sign_canonical(self, canonical: str, *, signing_time: datetime | None = None) -> str:
        cms_bytes = build_cades_bes(
            canonical,
            self.certificate,
            lambda data: sign_with_private_key(data, self.private_key),
            signing_time=signing_time,
        )
        return b64encode(cms_bytes).decode("ascii")


class UnsignedSigner(DocumentSigner):
    """v0.9 placeholder signer. Always returns `ANY`."""

    def sign_canonical(self, canonical: str, *, signing_time: datetime | None = None) -> str:
        return "ANY"
