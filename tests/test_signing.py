from base64 import b64decode
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from asn1crypto import cms
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

from egypt_compliance import ETASigningError, SignatureFactory, canonicalize
from egypt_compliance.signing.cades import ID_SIGNING_CERTIFICATE_V2


def _test_cert_and_key():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "ETA Test")])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    return cert, key


def _pem_files(tmp_path: Path):
    cert, key = _test_cert_and_key()
    cert_path = tmp_path / "cert.pem"
    key_path = tmp_path / "key.pem"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    return cert_path, key_path, cert, key


def test_sign_json_file_returns_cades_and_signed_document(tmp_path: Path):
    cert_path, key_path, cert, key = _pem_files(tmp_path)
    source = tmp_path / "SourceDocumentJson.json"
    source.write_text(
        '{"documentType":"i","documentTypeVersion":"1.0","internalID":"INV-1"}',
        encoding="utf-8",
    )
    signer = SignatureFactory.create("pem", certificate=cert_path, private_key=key_path)
    when = datetime(2024, 2, 13, 13, 15, tzinfo=timezone.utc)
    result = signer.sign_file(source, signing_time=when)

    assert result.document["internalID"] == "INV-1"
    assert result.document["signatures"][0]["signatureType"] == "I"
    assert result.submission == {"documents": [result.document]}
    assert result.canonical == canonicalize(source)
    assert "signatures" not in result.canonical.lower()

    cms_bytes = b64decode(result.signature)
    content = cms.ContentInfo.load(cms_bytes)
    assert content["content_type"].native == "signed_data"
    signer_info = content["content"]["signer_infos"][0]
    attr_types = [attr["type"].native for attr in signer_info["signed_attrs"]]
    assert "content_type" in attr_types
    assert "signing_time" in attr_types
    assert "message_digest" in attr_types
    dotted = [attr["type"].dotted for attr in signer_info["signed_attrs"]]
    assert "signing_certificate_v2" in attr_types or ID_SIGNING_CERTIFICATE_V2 in dotted


def test_cades_signature_verifies_against_canonical_bytes(tmp_path: Path):
    cert_path, key_path, cert, key = _pem_files(tmp_path)
    document = {"documentType": "i", "documentTypeVersion": "1.0", "internalID": "INV-1"}
    signer = SignatureFactory.create("pem", certificate=cert_path, private_key=key_path)
    result = signer.sign_document(document, signing_time=datetime(2024, 1, 1, tzinfo=timezone.utc))

    content = cms.ContentInfo.load(b64decode(result.signature))
    signer_info = content["content"]["signer_infos"][0]
    signed_attrs = signer_info["signed_attrs"]
    message_digest = None
    for attr in signed_attrs:
        if attr["type"].native == "message_digest":
            message_digest = attr["values"][0].native
    expected = hashes.Hash(hashes.SHA256())
    expected.update(result.canonical.encode("utf-8"))
    assert message_digest == expected.finalize()

    encoded = signed_attrs.dump(force=True)
    if encoded and encoded[0] == 0xA0:
        encoded = b"\x31" + encoded[1:]
    cert.public_key().verify(
        signer_info["signature"].native,
        encoded,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )


def test_version_0_9_creates_real_cades(tmp_path: Path):
    cert_path, key_path, _, _ = _pem_files(tmp_path)
    signer = SignatureFactory.create("pem", certificate=cert_path, private_key=key_path)
    result = signer.sign_document({"documentType": "i", "documentTypeVersion": "0.9"})
    assert result.signature != "ANY"
    assert len(result.signature) > 100
    cms.ContentInfo.load(b64decode(result.signature))
    assert result.document["signatures"][0]["signatureType"] == "I"


def test_unsigned_factory_returns_any_placeholder():
    signer = SignatureFactory.create("unsigned")
    result = signer.sign_document({"documentType": "i", "documentTypeVersion": "0.9"})
    assert result.signature == "ANY"
    assert result.document["signatures"][0]["signatureType"] == "I"


def test_signature_factory_rejects_unknown_method():
    with pytest.raises(ValueError, match="Unknown signer"):
        SignatureFactory.create("usb")


def test_pkcs11_missing_library_raises():
    signer = SignatureFactory.create("pkcs11", pin="1234", library="missing-pkcs11.dll")
    with pytest.raises(ETASigningError):
        signer.sign_canonical('"A""1"')
