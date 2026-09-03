from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_document(source: str | Path | dict | list | bytes) -> Any:
    """Load invoice JSON, preserving original number text from files/strings."""
    if isinstance(source, dict | list):
        return source
    if isinstance(source, bytes):
        text = source.decode("utf-8")
    elif isinstance(source, Path) or (isinstance(source, str) and _looks_like_path(source)):
        text = Path(source).read_text(encoding="utf-8")
    else:
        text = source
    return json.loads(text, parse_float=str, parse_int=str)


def _looks_like_path(value: str) -> bool:
    if value.lstrip().startswith("{") or value.lstrip().startswith("["):
        return False
    path = Path(value)
    return path.suffix.lower() == ".json" or path.exists()


def extract_documents(payload: Any) -> list[dict]:
    if isinstance(payload, dict) and isinstance(payload.get("documents"), list):
        documents = payload["documents"]
        if not documents:
            raise ValueError("documents must contain at least one document")
        if not all(isinstance(item, dict) for item in documents):
            raise ValueError("each documents entry must be a JSON object")
        return documents
    if isinstance(payload, dict):
        return [payload]
    raise ValueError("JSON must be a document object or {\"documents\": [...]}")


def canonicalize(source: str | Path | dict | list | bytes) -> str:
    """ETA/ITIDA canonical string for one document (no `signatures`)."""
    payload = load_json_document(source)
    documents = extract_documents(payload)
    if len(documents) != 1:
        raise ValueError("canonicalize() expects a single document; use canonicalize_each() for batches")
    return serialize_value(documents[0])


def canonicalize_each(source: str | Path | dict | list | bytes) -> list[str]:
    payload = load_json_document(source)
    return [serialize_value(document) for document in extract_documents(payload)]


def serialize_value(value: Any) -> str:
    if isinstance(value, dict):
        parts: list[str] = []
        for key, item in value.items():
            if str(key).lower() == "signatures" or item is None:
                continue
            name = f'"{str(key).upper()}"'
            if isinstance(item, list):
                parts.append(name)
                for element in item:
                    parts.append(name)
                    parts.append(serialize_value(element))
            else:
                parts.append(name)
                parts.append(serialize_value(item))
        return "".join(parts)
    if isinstance(value, list):
        return "".join(serialize_value(element) for element in value)
    return _scalar(value)


def _scalar(value: Any) -> str:
    if isinstance(value, bool):
        return '"true"' if value else '"false"'
    if value is None:
        return '"null"'
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, float)):
        return f'"{json.dumps(value)}"'
    return json.dumps(str(value), ensure_ascii=False)
