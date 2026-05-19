from silo.core.model import Model


class MasterProblem:
    def __init__(self, model: Model) -> None:
        self.model = model
