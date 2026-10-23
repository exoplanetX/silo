"""Run the installed public policy example: python examples/mip_policy.py."""

import json

from silo.mip.research_example import run_example

if __name__ == "__main__":
    print(json.dumps(run_example(), indent=2))
