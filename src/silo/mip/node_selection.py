from silo.mip.node import Node


def select_depth_first(open_nodes: list[Node]) -> Node | None:
    return open_nodes[-1] if open_nodes else None
