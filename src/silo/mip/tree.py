from dataclasses import dataclass, field

from silo.mip.node import Node


@dataclass
class SearchTree:
    open_nodes: list[Node] = field(default_factory=list)

    def push(self, node: Node) -> None:
        self.open_nodes.append(node)

    def pop(self) -> Node | None:
        return self.open_nodes.pop() if self.open_nodes else None
