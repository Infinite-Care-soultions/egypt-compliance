from abc import ABC, abstractmethod

from egypt_compliance.signing.pkcs11 import Pkcs11Signer
from egypt_compliance.signing.signer import DocumentSigner
from egypt_compliance.signing.software import (
    SoftwareSigner,
    UnsignedSigner,
    load_pem_certificate,
    load_pem_private_key,
    load_pfx,
)


class SignerCreator(ABC):
    """Factory Method: subclasses decide which signer to instantiate."""

    @abstractmethod
    def create_signer(self, **kwargs) -> DocumentSigner:
        raise NotImplementedError


class PemSignerCreator(SignerCreator):
    def create_signer(self, **kwargs) -> SoftwareSigner:
        certificate = kwargs.get("certificate")
        private_key = kwargs.get("private_key")
        if certificate is None or private_key is None:
            raise ValueError("pem signer requires certificate= and private_key=")
        return SoftwareSigner(
            load_pem_certificate(certificate),
            load_pem_private_key(private_key, kwargs.get("password")),
            signature_field=kwargs.get("signature_field", "signatureType"),
        )


class PfxSignerCreator(SignerCreator):
    def create_signer(self, **kwargs) -> SoftwareSigner:
        pfx = kwargs.get("pfx") or kwargs.get("pkcs12")
        if pfx is None:
            raise ValueError("pfx signer requires pfx=")
        private_key, certificate = load_pfx(pfx, kwargs.get("password"))
        return SoftwareSigner(
            certificate,
            private_key,
            signature_field=kwargs.get("signature_field", "signatureType"),
        )


class Pkcs11SignerCreator(SignerCreator):
    def create_signer(self, **kwargs) -> DocumentSigner:
        pin = kwargs.get("pin")
        if not pin:
            raise ValueError("pkcs11 signer requires pin=")
        return Pkcs11Signer(
            pin,
            library=kwargs.get("library", "eps2003csp11.dll"),
            certificate_issuer=kwargs.get("certificate_issuer", "Egypt Trust Sealing CA"),
            slot=kwargs.get("slot"),
            signature_field=kwargs.get("signature_field", "signatureType"),
        )


class UnsignedSignerCreator(SignerCreator):
    def create_signer(self, **kwargs) -> UnsignedSigner:
        return UnsignedSigner()


class SignatureFactory:
    """Public facade over PEM, PFX, PKCS#11, and unsigned v0.9 signers."""

    _creators: dict[str, type[SignerCreator]] = {
        "pem": PemSignerCreator,
        "pfx": PfxSignerCreator,
        "pkcs12": PfxSignerCreator,
        "pkcs11": Pkcs11SignerCreator,
        "token": Pkcs11SignerCreator,
        "unsigned": UnsignedSignerCreator,
        "v0.9": UnsignedSignerCreator,
    }

    @classmethod
    def create(cls, method: str, **kwargs) -> DocumentSigner:
        key = str(method).strip().lower()
        creator_cls = cls._creators.get(key)
        if creator_cls is None:
            valid = ", ".join(sorted(set(cls._creators)))
            raise ValueError(f"Unknown signer {method!r}. Expected one of: {valid}")
        return creator_cls().create_signer(**kwargs)
