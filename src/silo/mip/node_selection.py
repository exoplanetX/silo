from silo.mip.node import MIPNode


def select_depth_first(open_nodes: list[MIPNode]) -> MIPNode | None:
    return open_nodes[-1] if open_nodes else None


def pop_depth_first(open_nodes: list[MIPNode]) -> MIPNode | None:
    return open_nodes.pop() if open_nodes else None
