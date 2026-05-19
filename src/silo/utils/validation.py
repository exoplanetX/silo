from silo.core.model import Model


def validate_model(model: Model) -> None:
    seen = set()
    for variable in model.variables:
        if variable.name in seen:
            raise ValueError(f"Duplicate variable name: {variable.name}")
        seen.add(variable.name)
