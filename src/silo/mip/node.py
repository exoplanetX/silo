from dataclasses import dataclass, field


@dataclass(frozen=True)
class Node:
    depth: int = 0
    local_bounds: dict[str, tuple[float, float]] = field(default_factory=dict)
