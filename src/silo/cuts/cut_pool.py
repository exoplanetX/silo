from dataclasses import dataclass, field


@dataclass
class CutPool:
    cuts: list[object] = field(default_factory=list)

    def add(self, cut: object) -> None:
        self.cuts.append(cut)
