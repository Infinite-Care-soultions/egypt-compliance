import json
from pathlib import Path

from egypt_compliance import canonicalize, canonicalize_each


def test_canonicalize_nested_object_array_and_scalars():
    document = {
        "issuer": {"id": "1", "name": "A"},
        "active": True,
        "invoiceLines": [{"description": "x", "quantity": 1.0}],
        "signatures": [{"type": "I", "value": "ignore-me"}],
    }
    assert canonicalize(document) == (
        '"ISSUER""ID""1""NAME""A""ACTIVE""true"'
        '"INVOICELINES""INVOICELINES""DESCRIPTION""x""QUANTITY""1.0"'
    )


def test_canonicalize_preserves_json_number_text(tmp_path: Path):
    path = tmp_path / "doc.json"
    path.write_text('{"rate": 14.00, "count": 1}', encoding="utf-8")
    assert canonicalize(path) == '"RATE""14.00""COUNT""1"'


def test_canonicalize_string_escaping_and_unicode():
    document = {"name": 'he said "hi"', "ar": "فاتورة"}
    canonical = canonicalize(document)
    assert '"NAME"' + json.dumps('he said "hi"', ensure_ascii=False) in canonical
    assert '"AR""فاتورة"' in canonical


def test_canonicalize_references_string_array():
    document = {"references": ["ABC", "DEF"]}
    assert canonicalize(document) == '"REFERENCES""REFERENCES""ABC""REFERENCES""DEF"'


def test_canonicalize_unwraps_single_documents_wrapper():
    payload = {"documents": [{"internalID": "INV-1"}]}
    assert canonicalize(payload) == '"INTERNALID""INV-1"'


def test_canonicalize_each_signs_batch():
    payload = {"documents": [{"id": "1"}, {"id": "2"}]}
    assert canonicalize_each(payload) == ['"ID""1"', '"ID""2"']
