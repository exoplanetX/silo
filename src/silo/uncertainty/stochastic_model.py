from dataclasses import dataclass, field

from silo.core.model import Model
from silo.uncertainty.scenario import Scenario


@dataclass
class StochasticModel:
    base_model: Model
    scenarios: list[Scenario] = field(default_factory=list)
