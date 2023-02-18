import json
from operator import lt
from pathlib import Path
from abc import ABC, abstractmethod

from pydantic import BaseModel, parse_file_as, parse_obj_as
from pydantic.json import pydantic_encoder

class BaseProvider(BaseModel, ABC):
    @abstractmethod
    def fetch_accounts(self):
        pass

class BaseEntry(BaseModel, ABC):
    @abstractmethod
    def format(self) -> str:
        pass

    @abstractmethod
    def as_tuple() -> tuple:
        pass

    def __hash__(self):
        return hash(self.as_tuple())

    def __lt__(self, other):
        return lt((self.as_tuple()), (other.as_tuple()))

LAST_POLL_DIRECTORY = "last_polls"
class Account():
    id: str

    def __init__(self, id, Model, entries) -> None:
        self.id = id
        self.Model = Model
        self.entries = parse_obj_as(set[Model], entries) # type: ignore

    @classmethod
    def load_cache(cls, id: str, Model):
        try:
            entries = parse_file_as(set[Model],Path(LAST_POLL_DIRECTORY, f"{id}.json"))
        except FileNotFoundError:
            entries = set()

        return cls(id, Model, entries)

    def store_cache(self):
        with open(Path(LAST_POLL_DIRECTORY, f"{self.id}.json"), "w") as f:
            f.write(json.dumps(sorted(self.entries), indent=4, default=pydantic_encoder))

    def compare_with_cache(self):
        cached_account = self.load_cache(self.id, self.Model)

        new_found_entries = self.entries - cached_account.entries 

        return sorted(new_found_entries)
