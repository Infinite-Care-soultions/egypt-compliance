from __future__ import annotations

from base64 import b64encode
from datetime import datetime

import pkcs11
from cryptography import x509
from pkcs11 import Attribute, Mechanism, ObjectClass

from egypt_compliance.exceptions import ETASigningError
from egypt_compliance.signing.cades import build_cades_bes
from egypt_compliance.signing.signer import DocumentSigner


class Pkcs11Signer(DocumentSigner):
    """Sign with a USB eSeal token (`eps2003csp11.dll` / `SignatureP11.dll`)."""

    def __init__(
        self,
        pin: str,
        *,
        library: str = "eps2003csp11.dll",
        certificate_issuer: str = "Egypt Trust Sealing CA",
        slot: int | None = None,
        signature_field: str = "signatureType",
    ) -> None:
        self.pin = pin
        self.library = library
        self.certificate_issuer = certificate_issuer
        self.slot = slot
        self.signature_field = signature_field

    def sign_canonical(self, canonical: str, *, signing_time: datetime | None = None) -> str:
        try:
            lib = pkcs11.lib(self.library)
            tokens = list(lib.get_tokens())
        except ETASigningError:
            raise
        except Exception as exc:
            raise ETASigningError(f"Unable to load PKCS#11 library {self.library!r}: {exc}") from exc

        if not tokens:
            raise ETASigningError("No PKCS#11 token present")
        if self.slot is not None:
            if self.slot < 0 or self.slot >= len(tokens):
                raise ETASigningError(f"PKCS#11 slot {self.slot} is not available")
            token = tokens[self.slot]
        else:
            token = tokens[0]

        try:
            with token.open(user_pin=self.pin) as session:
                token_cert, private_key = self._load_key_pair(session, Attribute, ObjectClass)
                x509_cert = x509.load_der_x509_certificate(token_cert[Attribute.VALUE])

                def _sign(data: bytes) -> bytes:
                    return private_key.sign(data, mechanism=Mechanism.SHA256_RSA_PKCS)

                cms_bytes = build_cades_bes(canonical, x509_cert, _sign, signing_time=signing_time)
                return b64encode(cms_bytes).decode("ascii")
        except ETASigningError:
            raise
        except Exception as exc:
            raise ETASigningError(f"PKCS#11 signing failed: {exc}") from exc

    def _load_key_pair(self, session, Attribute, ObjectClass):
        certificates = list(session.get_objects({Attribute.CLASS: ObjectClass.CERTIFICATE}))
        if not certificates:
            raise ETASigningError("No certificate found on the PKCS#11 token")

        issuer_hint = (self.certificate_issuer or "").lower()
        selected = None
        for certificate in certificates:
            parsed = x509.load_der_x509_certificate(certificate[Attribute.VALUE])
            issuer = parsed.issuer.rfc4514_string()
            if issuer_hint and issuer_hint in issuer.lower():
                selected = certificate
                break
            if selected is None:
                selected = certificate
        if selected is None:
            raise ETASigningError("Certificate not found on the PKCS#11 token")

        try:
            key_id = selected[Attribute.ID]
        except Exception:
            key_id = None
        query = {Attribute.CLASS: ObjectClass.PRIVATE_KEY, Attribute.SIGN: True}
        if key_id:
            query[Attribute.ID] = key_id
        keys = list(session.get_objects(query))
        if not keys:
            keys = list(session.get_objects({Attribute.CLASS: ObjectClass.PRIVATE_KEY, Attribute.SIGN: True}))
        if not keys:
            raise ETASigningError("No private key found on the PKCS#11 token")
        return selected, keys[0]
