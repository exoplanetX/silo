from dataclasses import dataclass, field

from silo.core.enums import ConstraintSense


@dataclass(frozen=True)
class BranchingConstraint:
    variable_name: str
    sense: ConstraintSense
    rhs: float

    def __post_init__(self) -> None:
        if not self.variable_name:
            raise ValueError("Branching constraint variable name must not be empty.")
        object.__setattr__(self, "sense", ConstraintSense(self.sense))
        object.__setattr__(self, "rhs", float(self.rhs))


@dataclass(frozen=True)
class MIPNode:
    id: int
    depth: int
    branching_constraints: tuple[BranchingConstraint, ...] = field(default_factory=tuple)
    parent_id: int | None = None

    def __post_init__(self) -> None:
        if self.id < 0:
            raise ValueError("MIP node id must be nonnegative.")
        if self.depth < 0:
            raise ValueError("MIP node depth must be nonnegative.")
        object.__setattr__(self, "branching_constraints", tuple(self.branching_constraints))

    @classmethod
    def root(cls) -> "MIPNode":
        return cls(id=0, depth=0)


def root_node() -> MIPNode:
    return MIPNode.root()


def make_child_node(
    parent: MIPNode,
    node_id: int,
    branching_constraint: BranchingConstraint,
) -> MIPNode:
    if node_id == parent.id:
        raise ValueError("Child node id must differ from parent id.")
    return MIPNode(
        id=node_id,
        depth=parent.depth + 1,
        parent_id=parent.id,
        branching_constraints=parent.branching_constraints + (branching_constraint,),
    )


Node = MIPNode
