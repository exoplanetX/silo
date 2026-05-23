from collections.abc import Iterable
from dataclasses import dataclass
from math import isinf

from silo.core.enums import OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.cuts.callbacks import (
    CallbackEvent,
    CallbackHook,
    CutCallback,
    dispatch_callback_events,
)
from silo.cuts.cut_pool import CutPool
from silo.cuts.separator import Separator, SeparatorContext, separate_cuts
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
        separator: Separator | None = None,
        callbacks: Iterable[CutCallback] | None = None,
    ) -> None:
        if node_limit < 0:
            raise ValueError("Node limit must be nonnegative.")
        if separator is not None and not isinstance(separator, Separator):
            raise TypeError("Branch-and-bound separator must satisfy the Separator protocol.")
        self.lp_solver = lp_solver if lp_solver is not None else TableauSimplexSolver()
        self.node_limit = node_limit
        self.separator = separator
        self.callbacks = tuple(callbacks) if callbacks is not None else ()
        for callback in self.callbacks:
            if not isinstance(callback, CutCallback):
                raise TypeError(
                    "Branch-and-bound callbacks must satisfy the CutCallback protocol."
                )

    def solve(self, model: Model) -> Solution:
        return self.solve_with_details(model).solution

    def solve_with_details(self, model: Model) -> BranchAndBoundResult:
        try:
            integer_variable_names = _validate_supported_mip_scope(model)
        except ValueError as exc:
            return self._complete_result(
                _terminal_result(
                    Solution(status=SolverStatus.ERROR, message=str(exc)),
                    status_message=str(exc),
                )
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
        cut_pool = (
            CutPool(variable_order=variable_names)
            if self.separator is not None
            else None
        )

        while tree.open_nodes and nodes_processed < self.node_limit:
            node = tree.pop()
            if node is None:
                break
            nodes_processed += 1
            self._dispatch_basic_node_event(
                hook=CallbackHook.BEFORE_NODE_SOLVE,
                node=node,
                incumbent=incumbent,
            )

            try:
                relaxation = build_lp_relaxation(
                    model,
                    branching_constraints=node.branching_constraints,
                )
            except ValueError as exc:
                solution = Solution(status=SolverStatus.ERROR, message=str(exc))
                logs.append(_log_error(node, solution))
                return self._complete_result(
                    BranchAndBoundResult(
                        solution=solution,
                        nodes_processed=nodes_processed,
                        nodes_created=nodes_created,
                        nodes_pruned=nodes_pruned,
                        incumbent_value=incumbent.objective_value,
                        best_bound=best_bound,
                        log=tuple(logs),
                        status_message=solution.message,
                    )
                )

            lp_solution = self.lp_solver.solve(relaxation.model)
            if lp_solution.objective_value is not None:
                best_bound = _max_optional(best_bound, lp_solution.objective_value)
            self._dispatch_lp_relaxation_event(node, lp_solution, incumbent)

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
                self._dispatch_node_prune_event(
                    node=node,
                    lp_solution=lp_solution,
                    prune_reason=PruneReason.LP_INFEASIBLE,
                    incumbent=incumbent,
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
                self._dispatch_node_prune_event(
                    node=node,
                    lp_solution=lp_solution,
                    prune_reason=PruneReason.UNBOUNDED,
                    incumbent=incumbent,
                )
                return self._complete_result(
                    BranchAndBoundResult(
                        solution=solution,
                        nodes_processed=nodes_processed,
                        nodes_created=nodes_created,
                        nodes_pruned=nodes_pruned,
                        incumbent_value=incumbent.objective_value,
                        best_bound=best_bound,
                        log=tuple(logs),
                        status_message=solution.message,
                    )
                )

            if lp_solution.status in (SolverStatus.ERROR, SolverStatus.NUMERICAL_ISSUE):
                solution = Solution(status=lp_solution.status, message=lp_solution.message)
                logs.append(_log_error(node, solution))
                return self._complete_result(
                    BranchAndBoundResult(
                        solution=solution,
                        nodes_processed=nodes_processed,
                        nodes_created=nodes_created,
                        nodes_pruned=nodes_pruned,
                        incumbent_value=incumbent.objective_value,
                        best_bound=best_bound,
                        log=tuple(logs),
                        status_message=solution.message,
                    )
                )

            if lp_solution.status != SolverStatus.OPTIMAL:
                solution = Solution(
                    status=SolverStatus.ERROR,
                    message=f"Unexpected LP relaxation status: {lp_solution.status.value}",
                )
                logs.append(_log_error(node, solution))
                return self._complete_result(
                    BranchAndBoundResult(
                        solution=solution,
                        nodes_processed=nodes_processed,
                        nodes_created=nodes_created,
                        nodes_pruned=nodes_pruned,
                        incumbent_value=incumbent.objective_value,
                        best_bound=best_bound,
                        log=tuple(logs),
                        status_message=solution.message,
                    )
                )

            try:
                separator_error = self._run_noop_separator_boundary(
                    variable_names=variable_names,
                    node=node,
                    lp_solution=lp_solution,
                    incumbent=incumbent,
                    cut_pool=cut_pool,
                )
            except (TypeError, ValueError) as exc:
                separator_error = str(exc)
            if separator_error is not None:
                solution = Solution(status=SolverStatus.ERROR, message=separator_error)
                logs.append(_log_error(node, solution))
                return self._complete_result(
                    BranchAndBoundResult(
                        solution=solution,
                        nodes_processed=nodes_processed,
                        nodes_created=nodes_created,
                        nodes_pruned=nodes_pruned,
                        incumbent_value=incumbent.objective_value,
                        best_bound=best_bound,
                        log=tuple(logs),
                        status_message=solution.message,
                    )
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
                self._dispatch_node_prune_event(
                    node=node,
                    lp_solution=lp_solution,
                    prune_reason=PruneReason.BOUND_DOMINATED,
                    incumbent=incumbent,
                )
                continue

            try:
                branching_variable = choose_branching_variable(
                    variable_names=variable_names,
                    integer_variable_names=integer_variable_names,
                    values=lp_solution.primal_values,
                )
            except ValueError as exc:
                solution = Solution(status=SolverStatus.ERROR, message=str(exc))
                logs.append(_log_error(node, solution))
                return self._complete_result(
                    BranchAndBoundResult(
                        solution=solution,
                        nodes_processed=nodes_processed,
                        nodes_created=nodes_created,
                        nodes_pruned=nodes_pruned,
                        incumbent_value=incumbent.objective_value,
                        best_bound=best_bound,
                        log=tuple(logs),
                        status_message=solution.message,
                    )
                )

            if branching_variable is None:
                nodes_pruned += 1
                candidate = _mip_candidate_solution(lp_solution, integer_variable_names)
                incumbent = incumbent.update(candidate)
                self._dispatch_incumbent_update_event(node, lp_solution, incumbent)
                logs.append(
                    _log_node(
                        node=node,
                        lp_solution=lp_solution,
                        prune_reason=PruneReason.INTEGER_FEASIBLE,
                        incumbent_value=incumbent.objective_value,
                        message="LP relaxation solution is integer feasible.",
                    )
                )
                self._dispatch_node_prune_event(
                    node=node,
                    lp_solution=lp_solution,
                    prune_reason=PruneReason.INTEGER_FEASIBLE,
                    incumbent=incumbent,
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
            self._dispatch_child_creation_event(node, lp_solution, branching_variable, incumbent)
            logs.append(
                _log_node(
                    node=node,
                    lp_solution=lp_solution,
                    prune_reason=PruneReason.NOT_PRUNED,
                    branching_variable=branching_variable,
                    incumbent_value=incumbent.objective_value,
                    message="Branched on first fractional integer-restricted variable.",
                )
            )

        if tree.open_nodes:
            solution = _node_limit_solution(incumbent)
            return self._complete_result(
                BranchAndBoundResult(
                    solution=solution,
                    nodes_processed=nodes_processed,
                    nodes_created=nodes_created,
                    nodes_pruned=nodes_pruned,
                    incumbent_value=incumbent.objective_value,
                    best_bound=best_bound,
                    log=tuple(logs),
                    status_message=solution.message,
                )
            )

        if incumbent.solution is not None:
            solution = _final_optimal_solution(incumbent.solution)
            return self._complete_result(
                BranchAndBoundResult(
                    solution=solution,
                    nodes_processed=nodes_processed,
                    nodes_created=nodes_created,
                    nodes_pruned=nodes_pruned,
                    incumbent_value=solution.objective_value,
                    best_bound=solution.objective_value,
                    log=tuple(logs),
                    status_message=solution.message,
                )
            )

        solution = Solution(
            status=SolverStatus.INFEASIBLE,
            message="Branch-and-bound proved the MIP infeasible.",
        )
        return self._complete_result(
            BranchAndBoundResult(
                solution=solution,
                nodes_processed=nodes_processed,
                nodes_created=nodes_created,
                nodes_pruned=nodes_pruned,
                incumbent_value=None,
                best_bound=best_bound,
                log=tuple(logs),
                status_message=solution.message,
            )
        )

    def _run_noop_separator_boundary(
        self,
        *,
        variable_names: tuple[str, ...],
        node: MIPNode,
        lp_solution: Solution,
        incumbent: Incumbent,
        cut_pool: CutPool | None,
    ) -> str | None:
        if self.separator is None:
            return None
        relaxation_values = {
            variable_name: lp_solution.primal_values[variable_name]
            for variable_name in variable_names
            if variable_name in lp_solution.primal_values
        }
        context = SeparatorContext(
            variable_names=variable_names,
            node_id=node.id,
            relaxation_values=relaxation_values,
            cut_pool=cut_pool,
        )
        candidates = separate_cuts(self.separator, context)
        cut_ids = tuple(
            candidate.metadata.cut_id
            for candidate in candidates
            if candidate.metadata.cut_id is not None
        )
        if self.callbacks:
            self._dispatch_callback_event(
                CallbackEvent(
                    hook=CallbackHook.AFTER_CANDIDATE_CUT_SEPARATION,
                    node_id=node.id,
                    depth=node.depth,
                    lp_status=lp_solution.status.value,
                    lp_objective=lp_solution.objective_value,
                    incumbent_objective=incumbent.objective_value,
                    cut_count=len(candidates),
                    cut_ids=cut_ids,
                )
            )
        if candidates:
            return (
                "Branch-and-bound no-op cut integration does not materialize generated "
                "cuts."
            )
        if self.callbacks:
            self._dispatch_callback_event(
                CallbackEvent(
                    hook=CallbackHook.AFTER_CUT_POOL_UPDATE,
                    node_id=node.id,
                    depth=node.depth,
                    lp_status=lp_solution.status.value,
                    lp_objective=lp_solution.objective_value,
                    incumbent_objective=incumbent.objective_value,
                    cut_count=len(cut_pool) if cut_pool is not None else 0,
                )
            )
        return None

    def _dispatch_basic_node_event(
        self,
        *,
        hook: CallbackHook,
        node: MIPNode,
        incumbent: Incumbent,
    ) -> None:
        if not self.callbacks:
            return
        self._dispatch_callback_event(
            CallbackEvent(
                hook=hook,
                node_id=node.id,
                depth=node.depth,
                incumbent_objective=incumbent.objective_value,
            )
        )

    def _dispatch_lp_relaxation_event(
        self,
        node: MIPNode,
        lp_solution: Solution,
        incumbent: Incumbent,
    ) -> None:
        if not self.callbacks:
            return
        self._dispatch_callback_event(
            CallbackEvent(
                hook=CallbackHook.AFTER_LP_RELAXATION,
                node_id=node.id,
                depth=node.depth,
                lp_status=lp_solution.status.value,
                lp_objective=lp_solution.objective_value,
                incumbent_objective=incumbent.objective_value,
            )
        )

    def _dispatch_incumbent_update_event(
        self,
        node: MIPNode,
        lp_solution: Solution,
        incumbent: Incumbent,
    ) -> None:
        if not self.callbacks:
            return
        self._dispatch_callback_event(
            CallbackEvent(
                hook=CallbackHook.AFTER_INCUMBENT_UPDATE,
                node_id=node.id,
                depth=node.depth,
                lp_status=lp_solution.status.value,
                lp_objective=lp_solution.objective_value,
                incumbent_objective=incumbent.objective_value,
            )
        )

    def _dispatch_node_prune_event(
        self,
        *,
        node: MIPNode,
        lp_solution: Solution,
        prune_reason: PruneReason,
        incumbent: Incumbent,
    ) -> None:
        if not self.callbacks:
            return
        self._dispatch_callback_event(
            CallbackEvent(
                hook=CallbackHook.AFTER_NODE_PRUNE,
                node_id=node.id,
                depth=node.depth,
                lp_status=lp_solution.status.value,
                lp_objective=lp_solution.objective_value,
                prune_reason=prune_reason.value,
                incumbent_objective=incumbent.objective_value,
            )
        )

    def _dispatch_child_creation_event(
        self,
        node: MIPNode,
        lp_solution: Solution,
        branching_variable: str,
        incumbent: Incumbent,
    ) -> None:
        if not self.callbacks:
            return
        self._dispatch_callback_event(
            CallbackEvent(
                hook=CallbackHook.AFTER_CHILD_CREATION,
                node_id=node.id,
                depth=node.depth,
                lp_status=lp_solution.status.value,
                lp_objective=lp_solution.objective_value,
                branching_variable=branching_variable,
                incumbent_objective=incumbent.objective_value,
                diagnostics={"children_created": 2},
            )
        )

    def _complete_result(self, result: BranchAndBoundResult) -> BranchAndBoundResult:
        if not self.callbacks:
            return result
        self._dispatch_callback_event(
            CallbackEvent(
                hook=CallbackHook.SOLVE_COMPLETE,
                solver_status=result.solution.status.value,
                incumbent_objective=result.incumbent_value,
                diagnostics={
                    "nodes_processed": result.nodes_processed,
                    "nodes_created": result.nodes_created,
                    "nodes_pruned": result.nodes_pruned,
                },
            )
        )
        return result

    def _dispatch_callback_event(self, event: CallbackEvent) -> None:
        if self.callbacks:
            dispatch_callback_events(self.callbacks, (event,))


def _validate_supported_mip_scope(model: Model) -> tuple[str, ...]:
    model.validate()
    if model.objective.sense != OptimizationSense.MAXIMIZE:
        raise ValueError("Branch-and-bound supports maximization models only.")

    integer_variable_names: list[str] = []
    for variable in model.variables:
        if variable.var_type == VariableType.BINARY:
            if variable.bounds.lower != 0.0 or variable.bounds.upper != 1.0:
                raise ValueError(
                    f"Binary variable bounds must be exactly [0, 1]: {variable.name}"
                )
            integer_variable_names.append(variable.name)
        elif variable.var_type == VariableType.INTEGER:
            if variable.bounds.lower != 0.0:
                raise ValueError(f"Integer variable lower bound must be 0: {variable.name}")
            if isinf(variable.bounds.upper):
                raise ValueError(
                    f"Integer variable requires a finite upper bound: {variable.name}"
                )
            if not _is_integer_bound(variable.bounds.upper):
                raise ValueError(
                    f"Integer variable upper bound must be integer-valued: {variable.name}"
                )
            integer_variable_names.append(variable.name)
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
    return tuple(integer_variable_names)


def _mip_candidate_solution(
    lp_solution: Solution,
    integer_variable_names: tuple[str, ...],
) -> Solution:
    primal_values = dict(lp_solution.primal_values)
    for variable_name in integer_variable_names:
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
        message="Branch-and-bound solved the MIP.",
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


def _is_integer_bound(value: float) -> bool:
    return abs(value - round(value)) <= DEFAULT_INTEGER_TOLERANCE
