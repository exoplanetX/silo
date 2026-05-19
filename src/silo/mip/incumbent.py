from dataclasses import dataclass

from silo.core.solution import Solution


@dataclass
class Incumbent:
    solution: Solution | None = None

    def has_solution(self) -> bool:
        return self.solution is not None
