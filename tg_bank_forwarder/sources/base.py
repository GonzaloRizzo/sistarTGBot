from abc import ABC, abstractmethod
from pydantic import BaseModel


class BaseSourceModel(ABC, BaseModel):
    @abstractmethod
    def to_index(self) -> frozenset:
        pass

    @abstractmethod
    def format(self) -> str:
        pass


class BaseSourceModelList(BaseModel):
    __root__: list[BaseSourceModel]
