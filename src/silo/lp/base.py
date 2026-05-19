from abc import ABC, abstractmethod

from silo.core.model import Model
from silo.core.solution import Solution


class LPSolver(ABC):
    @abstractmethod
    def solve(self, model: Model) -> Solution:
        raise NotImplementedError
