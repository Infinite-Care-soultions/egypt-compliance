from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Callable

from asn1crypto import algos, cms, core, x509 as ax509
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dsa, ec, rsa
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15

from egypt_compliance.exceptions import ETASigningError

ID_SIGNING_CERTIFICATE_V2 = "1.2.840.113549.1.9.16.2.47"


class ESSCertIDv2(core.Sequence):
    _fields = [
        ("hash_algorithm", algos.DigestAlgorithm, {"optional": True}),
        ("cert_hash", core.OctetString),
    ]


class SigningCertificateV2(core.Sequence):
    _fields = [
        ("certs", core.SequenceOf, {"spec": ESSCertIDv2}),
    ]


class SetOfSigningCertificateV2(core.SetOf):
    _child_spec = SigningCertificateV2


cms.CMSAttributeType._map[ID_SIGNING_CERTIFICATE_V2] = "signing_certificate_v2"
cms.CMSAttribute._oid_specs["signing_certificate_v2"] = SetOfSigningCertificateV2


def build_cades_bes(
    canonical: str,
    certificate: x509.Certificate,
    sign: Callable[[bytes], bytes],
    *,
    signing_time: datetime | None = None,
) -> bytes:
    """Build a detached CAdES-BES CMS over the UTF-8 canonical document."""
    data = canonical.encode("utf-8")
    message_digest = hashlib.sha256(data).digest()
    cert_der = certificate.public_bytes(serialization.Encoding.DER)
    cert_hash = hashlib.sha256(cert_der).digest()
    when = signing_time or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)

    signing_cert = SigningCertificateV2(
        {
            "certs": [
                {
                    "hash_algorithm": {"algorithm": "sha256"},
                    "cert_hash": cert_hash,
                }
            ]
        }
    )
    signed_attrs = cms.CMSAttributes(
        [
            cms.CMSAttribute({"type": "content_type", "values": ["data"]}),
            cms.CMSAttribute({"type": "signing_time", "values": [cms.Time({"utc_time": when})]}),
            cms.CMSAttribute({"type": "message_digest", "values": [message_digest]}),
            cms.CMSAttribute({"type": ID_SIGNING_CERTIFICATE_V2, "values": [signing_cert]}),
        ]
    )
    signature = sign(signed_attrs.dump(force=True))
    asn1_cert = ax509.Certificate.load(cert_der)
    signer_info = cms.SignerInfo(
        {
            "version": 1,
            "sid": cms.SignerIdentifier(
                {
                    "issuer_and_serial_number": cms.IssuerAndSerialNumber(
                        {
                            "issuer": asn1_cert.issuer,
                            "serial_number": certificate.serial_number,
                        }
                    )
                }
            ),
            "digest_algorithm": {"algorithm": "sha256"},
            "signed_attrs": signed_attrs,
            "signature_algorithm": _signature_algorithm(certificate),
            "signature": signature,
        }
    )
    signed_data = cms.SignedData(
        {
            "version": 1,
            "digest_algorithms": [{"algorithm": "sha256"}],
            "encap_content_info": {"content_type": "data"},
            "certificates": [asn1_cert],
            "signer_infos": [signer_info],
        }
    )
    return cms.ContentInfo({"content_type": "signed_data", "content": signed_data}).dump()


def sign_with_private_key(to_sign: bytes, private_key) -> bytes:
    if isinstance(private_key, rsa.RSAPrivateKey):
        return private_key.sign(to_sign, PKCS1v15(), hashes.SHA256())
    if isinstance(private_key, ec.EllipticCurvePrivateKey):
        return private_key.sign(to_sign, ec.ECDSA(hashes.SHA256()))
    if isinstance(private_key, dsa.DSAPrivateKey):
        return private_key.sign(to_sign, hashes.SHA256())
    raise ETASigningError(f"Unsupported private key type: {type(private_key)!r}")


def _signature_algorithm(certificate: x509.Certificate) -> dict:
    public_key = certificate.public_key()
    if isinstance(public_key, rsa.RSAPublicKey):
        return {"algorithm": "rsassa_pkcs1v15"}
    if isinstance(public_key, ec.EllipticCurvePublicKey):
        return {"algorithm": "sha256_ecdsa"}
    if isinstance(public_key, dsa.DSAPublicKey):
        return {"algorithm": "sha256_dsa"}
    raise ETASigningError(f"Unsupported certificate key type: {type(public_key)!r}")
