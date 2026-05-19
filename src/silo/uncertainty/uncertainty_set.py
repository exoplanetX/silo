from dataclasses import dataclass, field


@dataclass(frozen=True)
class UncertaintySet:
    name: str
    parameters: dict[str, float] = field(default_factory=dict)
