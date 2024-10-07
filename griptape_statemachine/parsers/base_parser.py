from abc import ABC, abstractmethod

from attrs import define, field


@define()
class BaseParser(ABC):
    file_path: str = field()

    @abstractmethod
    def parse(self) -> dict: ...
