import json

from pydantic import BaseModel, TypeAdapter
from tinydb import TinyDB


class RecipientModel(BaseModel):
    name: str
    emails: list[str]

    @classmethod
    def from_file(cls, file_path: str) -> "list[RecipientModel]":
        adapter = TypeAdapter(list[RecipientModel])
        return adapter.validate_python(json.load(open(file_path)))

    @classmethod
    def from_tinydb(cls, tinydb: TinyDB):
        tinydb_data = tinydb.all()
        return [cls(**data) for data in tinydb_data]
