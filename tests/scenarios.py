import inspect
from functools import wraps

import pytest


def scenario_fixture(vars):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)  # should return locals()
            if not isinstance(result, dict):
                raise RuntimeError(
                    f"Scenario '{func.__name__}' must return locals(). "
                    f"Add 'return locals()' at the end of the scenario."
                )

            func_params = set(inspect.signature(func).parameters.keys())
            local_vars = {
                k: v
                for k, v in result.items()
                if not k.startswith("_") and k not in func_params
            }

            return_vars = {}
            for var in vars:
                if var not in local_vars:
                    available = [k for k in local_vars.keys() if not k.startswith("_")]
                    raise RuntimeError(
                        f"Variable '{var}' not found in scenario '{func.__name__}'. "
                        f"Available variables: {available}"
                    )
                return_vars[var] = local_vars[var]
            return return_vars

        wrapper._is_scenario_fixture = True
        wrapper._original_func = func
        wrapper._vars = vars
        return pytest.fixture(wrapper)

    return decorator


def _accessor_factory(scenario, var_name):
    def accessor(self, request):
        scenario_result = request.getfixturevalue(scenario.__name__)
        if not isinstance(scenario_result, dict):
            raise RuntimeError(
                f"Scenario '{scenario.__name__}' did not return a dict. "
                f"Ensure it returns locals()."
            )
        if var_name not in scenario_result:
            raise RuntimeError(
                f"Variable '{var_name}' not found in scenario '{scenario.__name__}'. "
                f"Available: {list(scenario_result.keys())}"
            )
        return scenario_result[var_name]

    accessor.__name__ = var_name
    return pytest.fixture(accessor)


def scenario_class(cls):
    scenarios = [
        attr for attr in cls.__dict__.values() if getattr(attr, "_is_scenario_fixture", False)
    ]
    if not scenarios:
        raise RuntimeError(
            f"No scenario fixtures found in class '{cls.__name__}'. "
            f"Ensure at least one method is decorated with @scenario_fixture."
        )
    for scenario in scenarios:
        for var in scenario._vars:
            accessor = _accessor_factory(scenario, var)
            setattr(cls, var, accessor)
    return cls
