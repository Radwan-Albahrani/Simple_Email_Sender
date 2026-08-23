import json
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, TypeAdapter


class SearchResult(BaseModel):
    """One result from the SearXNG JSON API; other fields are ignored."""

    title: str = ""
    content: str = ""


class SearchResponse(BaseModel):
    results: list[SearchResult] = []


class RecipientModel(BaseModel):
    name: str
    emails: list[str]

    @property
    def key(self) -> str:
        """Identity used for de-duplication across lists."""
        return self.name.strip().casefold()

    @classmethod
    def from_payload(cls, payload: Any) -> "list[RecipientModel]":
        """Parse either a plain JSON array or a TinyDB-style ``{"_default": {...}}`` mapping."""
        if isinstance(payload, dict):
            table = cast(dict[str, Any], payload).get("_default")
            if not isinstance(table, dict):
                raise ValueError("mapping payload has no '_default' table")
            payload = list(cast(dict[str, Any], table).values())
        adapter = TypeAdapter(list[RecipientModel])
        return adapter.validate_python(payload)

    @classmethod
    def from_file(cls, file_path: str | Path) -> "list[RecipientModel]":
        with open(file_path, encoding="utf-8") as handle:
            return cls.from_payload(json.load(handle))
