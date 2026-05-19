from dataclasses import dataclass

from silo.core.model import Model


@dataclass
class RobustModel:
    base_model: Model
    uncertainty_set_name: str
