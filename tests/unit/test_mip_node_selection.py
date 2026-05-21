import pytest

from silo.mip.node import MIPNode
from silo.mip.node_selection import pop_depth_first, select_depth_first
from silo.mip.tree import NodeIdGenerator, SearchTree


def test_depth_first_select_returns_last_node_without_mutating_list() -> None:
    nodes = [MIPNode(id=0, depth=0), MIPNode(id=1, depth=1)]

    selected = select_depth_first(nodes)

    assert selected == nodes[-1]
    assert [node.id for node in nodes] == [0, 1]


def test_depth_first_select_empty_list_returns_none() -> None:
    assert select_depth_first([]) is None


def test_depth_first_pop_returns_and_removes_last_node() -> None:
    nodes = [MIPNode(id=0, depth=0), MIPNode(id=1, depth=1)]

    selected = pop_depth_first(nodes)

    assert selected == MIPNode(id=1, depth=1)
    assert [node.id for node in nodes] == [0]


def test_depth_first_pop_empty_list_returns_none() -> None:
    assert pop_depth_first([]) is None


def test_search_tree_push_and_pop_are_lifo() -> None:
    tree = SearchTree()
    tree.push(MIPNode(id=0, depth=0))
    tree.push(MIPNode(id=1, depth=1))

    assert tree.pop() == MIPNode(id=1, depth=1)
    assert tree.pop() == MIPNode(id=0, depth=0)
    assert tree.pop() is None


def test_node_id_generator_starts_after_root() -> None:
    generator = NodeIdGenerator()

    assert generator.take() == 1
    assert generator.take() == 2
    assert generator.next_id == 3


def test_node_id_generator_rejects_negative_next_id() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        NodeIdGenerator(next_id=-1)
