from dataclasses import dataclass, field

from silo.mip.node import MIPNode


@dataclass
class NodeIdGenerator:
    next_id: int = 1

    def __post_init__(self) -> None:
        if self.next_id < 0:
            raise ValueError("Next node id must be nonnegative.")

    def take(self) -> int:
        node_id = self.next_id
        self.next_id += 1
        return node_id


@dataclass
class SearchTree:
    open_nodes: list[MIPNode] = field(default_factory=list)

    def push(self, node: MIPNode) -> None:
        self.open_nodes.append(node)

    def pop(self) -> MIPNode | None:
        return self.open_nodes.pop() if self.open_nodes else None
