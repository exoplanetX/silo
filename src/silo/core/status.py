from enum import Enum


class SolverStatus(str, Enum):
    NOT_SOLVED = "not_solved"
    OPTIMAL = "optimal"
    INFEASIBLE = "infeasible"
    UNBOUNDED = "unbounded"
    ITERATION_LIMIT = "iteration_limit"
    NUMERICAL_ISSUE = "numerical_issue"
    ERROR = "error"
