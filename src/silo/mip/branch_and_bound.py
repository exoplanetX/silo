from dataclasses import dataclass
from math import isinf

from silo.core.enums import OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.lp.base import LPSolver
from silo.lp.simplex.tableau import TableauSimplexSolver
from silo.mip.branching import (
    DEFAULT_INTEGER_TOLERANCE,
    branch_on_value,
    choose_branching_variable,
)
from silo.mip.incumbent import Incumbent
from silo.mip.logging import NodeLogEntry, PruneReason
from silo.mip.node import MIPNode, make_child_node, root_node
from silo.mip.relaxation import build_lp_relaxation
from silo.mip.tree import NodeIdGenerator, SearchTree

MIP_OBJECTIVE_TOLERANCE = 1e-9


@dataclass(frozen=True)
class BranchAndBoundResult:
    solution: Solution
    nodes_processed: int
    nodes_created: int
    nodes_pruned: int
    incumbent_value: float | None
    best_bound: float | None
    log: tuple[NodeLogEntry, ...] = ()
    status_message: str = ""


class BranchAndBoundSolver:
    def __init__(
        self,
        lp_solver: LPSolver | None = None,
        node_limit: int = 10_000,
    ) -> None:
        if node_limit < 0:
            raise ValueError("Node limit must be nonnegative.")
        self.lp_solver = lp_solver if lp_solver is not None else TableauSimplexSolver()
        self.node_limit = node_limit

    def solve(self, model: Model) -> Solution:
        return self.solve_with_details(model).solution

    def solve_with_details(self, model: Model) -> BranchAndBoundResult:
        try:
            binary_variable_names = _validate_binary_mip_scope(model)
        except ValueError as exc:
            return _terminal_result(
                Solution(status=SolverStatus.ERROR, message=str(exc)),
                status_message=str(exc),
            )

        tree = SearchTree(open_nodes=[root_node()])
        node_ids = NodeIdGenerator()
        incumbent = Incumbent()
        logs: list[NodeLogEntry] = []
        nodes_processed = 0
        nodes_created = 1
        nodes_pruned = 0
        best_bound: float | None = None
        variable_names = tuple(model.variable_names())

        while tree.open_nodes and nodes_processed < self.node_limit:
            node = tree.pop()
            if node is None:
                break
            nodes_processed += 1

            try:
                relaxation = build_lp_relaxation(
                    model,
                    branching_constraints=node.branching_constraints,
                )
            except ValueError as exc:
                solution = Solution(status=SolverStatus.ERROR, message=str(exc))
                logs.append(_log_error(node, solution))
                return BranchAndBoundResult(
                    solution=solution,
                    nodes_processed=nodes_processed,
                    nodes_created=nodes_created,
                    nodes_pruned=nodes_pruned,
                    incumbent_value=incumbent.objective_value,
                    best_bound=best_bound,
                    log=tuple(logs),
                    status_message=solution.message,
                )

            lp_solution = self.lp_solver.solve(relaxation.model)
            if lp_solution.objective_value is not None:
                best_bound = _max_optional(best_bound, lp_solution.objective_value)

            if lp_solution.status == SolverStatus.INFEASIBLE:
                nodes_pruned += 1
                logs.append(
                    _log_node(
                        node=node,
                        lp_solution=lp_solution,
                        prune_reason=PruneReason.LP_INFEASIBLE,
                        incumbent_value=incumbent.objective_value,
                        message="LP relaxation is infeasible.",
                    )
                )
                continue

            if lp_solution.status == SolverStatus.UNBOUNDED:
                nodes_pruned += 1
                solution = Solution(
                    status=SolverStatus.UNBOUNDED,
                    message="LP relaxation is unbounded at a branch-and-bound node.",
                )
                logs.append(
                    _log_node(
                        node=node,
                        lp_solution=lp_solution,
                        prune_reason=PruneReason.UNBOUNDED,
                        incumbent_value=incumbent.objective_value,
                        message=solution.message,
                    )
                )
                return BranchAndBoundResult(
                    solution=solution,
                    nodes_processed=nodes_processed,
                    nodes_created=nodes_created,
                    nodes_pruned=nodes_pruned,
                    incumbent_value=incumbent.objective_value,
                    best_bound=best_bound,
                    log=tuple(logs),
                    status_message=solution.message,
                )

            if lp_solution.status in (SolverStatus.ERROR, SolverStatus.NUMERICAL_ISSUE):
                solution = Solution(status=lp_solution.status, message=lp_solution.message)
                logs.append(_log_error(node, solution))
                return BranchAndBoundResult(
                    solution=solution,
                    nodes_processed=nodes_processed,
                    nodes_created=nodes_created,
                    nodes_pruned=nodes_pruned,
                    incumbent_value=incumbent.objective_value,
                    best_bound=best_bound,
                    log=tuple(logs),
                    status_message=solution.message,
                )

            if lp_solution.status != SolverStatus.OPTIMAL:
                solution = Solution(
                    status=SolverStatus.ERROR,
                    message=f"Unexpected LP relaxation status: {lp_solution.status.value}",
                )
                logs.append(_log_error(node, solution))
                return BranchAndBoundResult(
                    solution=solution,
                    nodes_processed=nodes_processed,
                    nodes_created=nodes_created,
                    nodes_pruned=nodes_pruned,
                    incumbent_value=incumbent.objective_value,
                    best_bound=best_bound,
                    log=tuple(logs),
                    status_message=solution.message,
                )

            if _is_bound_dominated(lp_solution, incumbent):
                nodes_pruned += 1
                logs.append(
                    _log_node(
                        node=node,
                        lp_solution=lp_solution,
                        prune_reason=PruneReason.BOUND_DOMINATED,
                        incumbent_value=incumbent.objective_value,
                        message="LP bound cannot improve the incumbent.",
                    )
                )
                continue

            try:
                branching_variable = choose_branching_variable(
                    variable_names=variable_names,
                    integer_variable_names=binary_variable_names,
                    values=lp_solution.primal_values,
                )
            except ValueError as exc:
                solution = Solution(status=SolverStatus.ERROR, message=str(exc))
                logs.append(_log_error(node, solution))
                return BranchAndBoundResult(
                    solution=solution,
                    nodes_processed=nodes_processed,
                    nodes_created=nodes_created,
                    nodes_pruned=nodes_pruned,
                    incumbent_value=incumbent.objective_value,
                    best_bound=best_bound,
                    log=tuple(logs),
                    status_message=solution.message,
                )

            if branching_variable is None:
                nodes_pruned += 1
                candidate = _mip_candidate_solution(lp_solution, binary_variable_names)
                incumbent = incumbent.update(candidate)
                logs.append(
                    _log_node(
                        node=node,
                        lp_solution=lp_solution,
                        prune_reason=PruneReason.INTEGER_FEASIBLE,
                        incumbent_value=incumbent.objective_value,
                        message="LP relaxation solution is binary feasible.",
                    )
                )
                continue

            branching_value = lp_solution.primal_values[branching_variable]
            left_constraint, right_constraint = branch_on_value(
                branching_variable,
                branching_value,
            )
            left_child = make_child_node(node, node_ids.take(), left_constraint)
            right_child = make_child_node(node, node_ids.take(), right_constraint)
            nodes_created += 2
            # Stack is LIFO, so push right first to process left first.
            tree.push(right_child)
            tree.push(left_child)
            logs.append(
                _log_node(
                    node=node,
                    lp_solution=lp_solution,
                    prune_reason=PruneReason.NOT_PRUNED,
                    branching_variable=branching_variable,
                    incumbent_value=incumbent.objective_value,
                    message="Branched on first fractional binary variable.",
                )
            )

        if tree.open_nodes:
            solution = _node_limit_solution(incumbent)
            return BranchAndBoundResult(
                solution=solution,
                nodes_processed=nodes_processed,
                nodes_created=nodes_created,
                nodes_pruned=nodes_pruned,
                incumbent_value=incumbent.objective_value,
                best_bound=best_bound,
                log=tuple(logs),
                status_message=solution.message,
            )

        if incumbent.solution is not None:
            solution = _final_optimal_solution(incumbent.solution)
            return BranchAndBoundResult(
                solution=solution,
                nodes_processed=nodes_processed,
                nodes_created=nodes_created,
                nodes_pruned=nodes_pruned,
                incumbent_value=solution.objective_value,
                best_bound=solution.objective_value,
                log=tuple(logs),
                status_message=solution.message,
            )

        solution = Solution(
            status=SolverStatus.INFEASIBLE,
            message="Branch-and-bound proved the binary MIP infeasible.",
        )
        return BranchAndBoundResult(
            solution=solution,
            nodes_processed=nodes_processed,
            nodes_created=nodes_created,
            nodes_pruned=nodes_pruned,
            incumbent_value=None,
            best_bound=best_bound,
            log=tuple(logs),
            status_message=solution.message,
        )


def _validate_binary_mip_scope(model: Model) -> tuple[str, ...]:
    model.validate()
    if model.objective.sense != OptimizationSense.MAXIMIZE:
        raise ValueError("Binary branch-and-bound supports maximization models only.")

    binary_variable_names: list[str] = []
    for variable in model.variables:
        if variable.var_type == VariableType.BINARY:
            if variable.bounds.lower != 0.0 or variable.bounds.upper != 1.0:
                raise ValueError(
                    f"Binary variable bounds must be exactly [0, 1]: {variable.name}"
                )
            binary_variable_names.append(variable.name)
        elif variable.var_type == VariableType.INTEGER:
            raise ValueError(
                f"Binary branch-and-bound does not support general integer variables: "
                f"{variable.name}"
            )
        elif variable.var_type == VariableType.CONTINUOUS:
            if variable.bounds.lower != 0.0:
                raise ValueError(
                    f"Continuous variable lower bound must be 0: {variable.name}"
                )
            if not isinf(variable.bounds.upper):
                raise ValueError(
                    f"Continuous variable finite upper bounds are not supported: "
                    f"{variable.name}"
                )
        else:
            raise ValueError(f"Unsupported variable type: {variable.var_type}")
    return tuple(binary_variable_names)


def _mip_candidate_solution(
    lp_solution: Solution,
    binary_variable_names: tuple[str, ...],
) -> Solution:
    primal_values = dict(lp_solution.primal_values)
    for variable_name in binary_variable_names:
        value = primal_values[variable_name]
        rounded = float(round(value))
        if abs(value - rounded) <= DEFAULT_INTEGER_TOLERANCE:
            primal_values[variable_name] = rounded

    return Solution(
        status=SolverStatus.OPTIMAL,
        objective_value=lp_solution.objective_value,
        primal_values=primal_values,
        message="Integer-feasible branch-and-bound incumbent.",
    )


def _final_optimal_solution(solution: Solution) -> Solution:
    return Solution(
        status=SolverStatus.OPTIMAL,
        objective_value=solution.objective_value,
        primal_values=dict(solution.primal_values),
        message="Branch-and-bound solved the binary MIP.",
    )


def _node_limit_solution(incumbent: Incumbent) -> Solution:
    if incumbent.solution is None:
        return Solution(
            status=SolverStatus.ITERATION_LIMIT,
            message="Branch-and-bound stopped at the node limit without an incumbent.",
        )
    return Solution(
        status=SolverStatus.ITERATION_LIMIT,
        objective_value=incumbent.solution.objective_value,
        primal_values=dict(incumbent.solution.primal_values),
        message="Branch-and-bound stopped at the node limit with an incumbent.",
    )


def _is_bound_dominated(lp_solution: Solution, incumbent: Incumbent) -> bool:
    if incumbent.objective_value is None or lp_solution.objective_value is None:
        return False
    return lp_solution.objective_value <= incumbent.objective_value + MIP_OBJECTIVE_TOLERANCE


def _log_node(
    node: MIPNode,
    lp_solution: Solution,
    prune_reason: PruneReason,
    incumbent_value: float | None,
    message: str,
    branching_variable: str | None = None,
) -> NodeLogEntry:
    return NodeLogEntry(
        node_id=node.id,
        depth=node.depth,
        lp_status=lp_solution.status,
        lp_objective=lp_solution.objective_value,
        prune_reason=prune_reason,
        branching_variable=branching_variable,
        incumbent_value=incumbent_value,
        message=message,
    )


def _log_error(node: MIPNode, solution: Solution) -> NodeLogEntry:
    return NodeLogEntry(
        node_id=node.id,
        depth=node.depth,
        lp_status=solution.status,
        prune_reason=PruneReason.ERROR,
        message=solution.message,
    )


def _terminal_result(solution: Solution, status_message: str) -> BranchAndBoundResult:
    return BranchAndBoundResult(
        solution=solution,
        nodes_processed=0,
        nodes_created=0,
        nodes_pruned=0,
        incumbent_value=None,
        best_bound=None,
        log=(),
        status_message=status_message,
    )


def _max_optional(left: float | None, right: float) -> float:
    if left is None:
        return right
    return max(left, right)
