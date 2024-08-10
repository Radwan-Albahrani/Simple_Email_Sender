import json

from pydantic import BaseModel, TypeAdapter


class RecipientModel(BaseModel):
    name: str
    emails: list[str]

    @classmethod
    def from_file(cls, file_path: str) -> "list[RecipientModel]":
        adapter = TypeAdapter(list[RecipientModel])
        return adapter.validate_python(json.load(open(file_path)))
