from enum import Enum


class OptimizationSense(str, Enum):
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class VariableType(str, Enum):
    CONTINUOUS = "continuous"
    INTEGER = "integer"
    BINARY = "binary"


class ConstraintSense(str, Enum):
    LE = "<="
    GE = ">="
    EQ = "="
