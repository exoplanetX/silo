from dataclasses import FrozenInstanceError

import pytest

from silo.core.enums import ConstraintSense
from silo.mip.node import BranchingConstraint, MIPNode, Node, make_child_node, root_node


def test_root_node_fields() -> None:
    node = root_node()

    assert node == MIPNode.root()
    assert node.id == 0
    assert node.depth == 0
    assert node.parent_id is None
    assert node.branching_constraints == ()


def test_node_alias_preserves_compatibility() -> None:
    assert Node is MIPNode


def test_rejects_negative_node_id() -> None:
    with pytest.raises(ValueError, match="id must be nonnegative"):
        MIPNode(id=-1, depth=0)


def test_rejects_negative_node_depth() -> None:
    with pytest.raises(ValueError, match="depth must be nonnegative"):
        MIPNode(id=1, depth=-1)


def test_branching_constraints_are_stored_as_tuple() -> None:
    branch = BranchingConstraint("x", ConstraintSense.LE, 0.0)
    node = MIPNode(id=1, depth=1, branching_constraints=[branch])

    assert node.branching_constraints == (branch,)


def test_child_node_preserves_parent_constraints_plus_new_constraint() -> None:
    parent_branch = BranchingConstraint("x", ConstraintSense.LE, 1.0)
    child_branch = BranchingConstraint("y", ConstraintSense.GE, 2.0)
    parent = MIPNode(
        id=3,
        depth=2,
        parent_id=1,
        branching_constraints=(parent_branch,),
    )

    child = make_child_node(parent, node_id=4, branching_constraint=child_branch)

    assert child.id == 4
    assert child.depth == 3
    assert child.parent_id == 3
    assert child.branching_constraints == (parent_branch, child_branch)


def test_child_node_rejects_parent_id_reuse() -> None:
    parent = MIPNode.root()

    with pytest.raises(ValueError, match="differ from parent"):
        make_child_node(
            parent,
            node_id=0,
            branching_constraint=BranchingConstraint("x", ConstraintSense.LE, 0.0),
        )


def test_node_is_immutable() -> None:
    node = MIPNode.root()

    with pytest.raises(FrozenInstanceError):
        node.depth = 1


def test_branching_constraint_validates_variable_name() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        BranchingConstraint("", ConstraintSense.LE, 0.0)


def test_branching_constraint_normalizes_sense_and_rhs() -> None:
    branch = BranchingConstraint("x", "<=", 1)

    assert branch.sense == ConstraintSense.LE
    assert branch.rhs == 1.0
