from silo.core.model import Model


def validate_model(model: Model) -> None:
    model.validate()
