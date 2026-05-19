from silo.core.model import Model
from silo.uncertainty.stochastic_model import StochasticModel


def build_deterministic_equivalent(model: StochasticModel) -> Model:
    return model.base_model
