from .currencies import Currency, LegacyCurrency
from .enums import AppID, Language
from .exceptions import (
    InvalidCurrencyException,
    InvalidLanguageException,
    LegacyCurrencyException,
)

from functools import wraps
from inspect import signature
from typing import Any, Callable, Union, get_args, get_origin


def _sanitize_app_id_value(
    value: Union[AppID, int, list[Union[AppID, int]]]
) -> Union[int, list[int]]:
    return [int(item) for item in value] if isinstance(value, list) else int(value)


def _sanitize_currency_value(
    value: Union[Currency, LegacyCurrency, int, str]
) -> Currency:
    if isinstance(value, (Currency, LegacyCurrency)):
        if isinstance(value, LegacyCurrency):
            raise LegacyCurrencyException(value)

        return value

    if isinstance(value, str):
        if LegacyCurrency.from_string(value) is not None:
            raise LegacyCurrencyException(value)

        currency = Currency.from_string(value)
        if currency is None:
            raise InvalidCurrencyException(value)

        return currency

    if isinstance(value, int):
        if value in LegacyCurrency:
            raise LegacyCurrencyException(value)

        try:
            value = Currency(value)
        except KeyError as e:
            raise InvalidCurrencyException(value) from e

    return value


def _sanitize_market_items_dict(
    value: dict[Union[AppID, int], list[str]]
) -> dict[int, list[str]]:
    return {int(app_id): list(items) for app_id, items in value.items()}


def _sanitize_language_value(value: Union[Language, str]) -> Language:
    if isinstance(value, Language):
        return value

    lanuage = Language.from_string(value)
    if lanuage is None:
        raise InvalidLanguageException(value)

    return lanuage


def _sanitize_market_hash_name_value(value: str) -> str:
    return value.replace("/", "-")


def _sanitize_market_hash_names_value(value: list[str]) -> list[str]:
    return [_sanitize_market_hash_name_value(item) for item in value]


def _sanitize_price_type_value(value: Union[str, tuple[str, ...]]) -> tuple[str, ...]:
    valid_price_types = ("lowest_price", "median_price")
    if isinstance(value, str):
        if value not in valid_price_types:
            raise ValueError(
                f"Invalid price type: {value}. Valid price types: {valid_price_types}"
            )

        return (value,)

    if any(price_type not in valid_price_types for price_type in value):
        raise ValueError(
            f"Invalid price type: {value}. Valid price types: {valid_price_types}"
        )

    return value


_SANITIZE_FUNCS = {
    "app_id": _sanitize_app_id_value,
    "currency": _sanitize_currency_value,
    "market_items_dict": _sanitize_market_items_dict,
    "language": _sanitize_language_value,
    "market_hash_name": _sanitize_market_hash_name_value,
    "market_hash_names": _sanitize_market_hash_names_value,
    "price_type": _sanitize_price_type_value,
}


def _sanitize_value(value: Any, param_name: str) -> Any:
    sanitize_func = _SANITIZE_FUNCS.get(param_name)
    return sanitize_func(value) if sanitize_func is not None else value


def _typecheck_dict_value(value: dict, expected_type_args: tuple[Any, ...]) -> bool:
    return all(
        _typecheck_value(k, expected_type_args[0])
        and _typecheck_value(v, expected_type_args[1])
        for k, v in value.items()
    )


def _typecheck_list_value(value: list, expected_type_args: tuple[Any, ...]) -> bool:
    return all(_typecheck_value(x, expected_type_args[0]) for x in value)


def _typecheck_set_value(value: set, expected_type_args: tuple[Any, ...]) -> bool:
    return all(_typecheck_value(x, expected_type_args[0]) for x in value)


def _typecheck_tuple_value(value: tuple, expected_type_args: tuple[Any, ...]) -> bool:
    return all(_typecheck_value(x, t) for x, t in zip(value, expected_type_args))


_TYPECHECK_FUNCS = {
    dict: _typecheck_dict_value,
    list: _typecheck_list_value,
    set: _typecheck_set_value,
    tuple: _typecheck_tuple_value,
}


def _typecheck_value(value: Any, expected_type: Any) -> bool:
    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if origin is None:
        return isinstance(value, expected_type)

    if origin is Union:
        return any(_typecheck_value(value, arg) for arg in args)

    if check_func := _TYPECHECK_FUNCS.get(origin):
        return check_func(value, args)

    return False


def sanitized(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to sanitize arguments before passing them to a function.

    .. versionadded:: 1.3.0

    Parameters
    ----------
    sanitize_args : str
        The names of the arguments to sanitize, if not specified all known arguments will be sanitized.

    Returns
    -------
    Callable[..., Any]
        The decorator function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        sig = signature(func)
        param_names = list(sig.parameters.keys())
        sanitize_param_names = list(_SANITIZE_FUNCS.keys())

        args_list = list(args)

        for i, arg in enumerate(args_list):
            arg_name = param_names[i]
            if arg_name in sanitize_param_names:
                args_list[i] = _sanitize_value(arg, arg_name)

        for kwarg_name, kwarg_value in kwargs.items():
            if kwarg_name in sanitize_param_names:
                kwargs[kwarg_name] = _sanitize_value(kwarg_value, kwarg_name)

        return func(*tuple(args_list), **kwargs)

    return wrapper


def typechecked(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to typecheck arguments before passing them to a function.

    .. versionadded:: 1.3.0

    Parameters
    ----------
    func : Callable[..., Any]
        The function to decorate.

    Returns
    -------
    Callable[..., Any]
        The decorated function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        annotations = func.__annotations__
        sig = signature(func)
        param_names = list(sig.parameters.keys())

        for i, arg in enumerate(args):
            arg_name = param_names[i]
            if arg_name in annotations and not _typecheck_value(
                arg, annotations[arg_name]
            ):
                raise TypeError(
                    f"Expected argument '{arg_name}' to be of type '{annotations[arg_name]}', not '{type(arg).__name__}'."
                )

        for kwarg_name, kwarg_value in kwargs.items():
            if kwarg_name in annotations and not _typecheck_value(
                kwarg_value, annotations[kwarg_name]
            ):
                raise TypeError(
                    f"Expected argument '{kwarg_name}' to be of type '{annotations[kwarg_name]}', not '{type(kwarg_value).__name__}'."
                )

        return func(*args, **kwargs)

    return wrapper
