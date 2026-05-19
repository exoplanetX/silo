from dataclasses import dataclass


@dataclass(frozen=True)
class Basis:
    basic_variables: tuple[str, ...]
    nonbasic_variables: tuple[str, ...]
