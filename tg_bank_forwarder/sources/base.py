from abc import ABC, abstractmethod


class BaseSource(ABC):
    @property
    @abstractmethod
    def index_keys(self) -> list:
        pass

    @abstractmethod
    def fetch(self) -> list:
        pass

    @abstractmethod
    def format(self, value) -> str:
        pass
