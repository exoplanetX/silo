from abc import ABC, abstractmethod

from silo.core.model import Model


class Separator(ABC):
    @abstractmethod
    def separate(self, model: Model) -> list[object]:
        raise NotImplementedError
