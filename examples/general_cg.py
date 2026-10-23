"""Run the packaged public finite-pool covering CG example (no external solver)."""

import json

from silo.core.solve_types import SolveOptions
from silo.decomposition.general_master import covering_example


def main():
    result = covering_example(SolveOptions(time_limit=10))
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.status == "optimal" else 1


if __name__ == "__main__":
    raise SystemExit(main())
