from .currencies import SteamCurrency, SteamLegacyCurrency
from .decorators import sanitized, typechecked
from .enums import AppID, SteamLanguage
from .requests import _request_overview

from typing import Optional, Union

import re


class Market:
    """A class representing a Steam Community Market object.

    It allows users to interact with the Steam Community Market API, by providing methods to get different information about items in the market. \
        It supports all currencies and languages that are supported by the Steam Community Market API.

    :param currency: Currency used for prices. Defaults to :attr:`SteamCurrency.USD <steam_community_market.currencies.SteamCurrency.USD>`.
    :type currency: SteamCurrency or SteamLegacyCurrency or int or str
    :param language: Language used for the returned data. Defaults to :attr:`SteamLanguage.ENGLISH <steam_community_market.enums.SteamLanguage.ENGLISH>`.
    :type language: SteamLanguage or int or str
    :raises InvalidCurrencyException: Raised when the ``currency`` is invalid.
    :raises LegacyCurrencyException: Raised when the ``currency`` is a legacy currency.
    :raises InvalidLanguageException: Raised when the ``language`` is invalid.
    """

    @typechecked
    @sanitized
    def __init__(
        self,
        currency: Union[
            SteamCurrency, SteamLegacyCurrency, int, str
        ] = SteamCurrency.USD,
        language: Union[SteamLanguage, str] = SteamLanguage.ENGLISH,
    ) -> None:
        self.currency = currency
        self.language = language

    @typechecked
    @sanitized
    def get_overview(
        self,
        app_id: Union[AppID, int],
        market_hash_name: str,
        type_conversion: bool = True,
        currency: Union[SteamCurrency, SteamLegacyCurrency, int, str] = None,
    ) -> Optional[dict[str, Union[bool, float, int, str]]]:
        """Gets the prices and volume of an item in the Steam Community Market.

        :param app_id: The :class:`AppID <steam_community_market.enums.AppID>` of the game the item is from.
        :type app_id: AppID or int
        :param market_hash_name: The name of the item how it appears on the Steam Community Market.
        :type market_hash_name: str
        :param type_conversion: Whether to convert the returned values to their corresponding types. Defaults to :obj:`True`.
        :type type_conversion: bool
        :param currency: Currency used for prices. Defaults to the value imposed by the instance of the class.
        :type currency: SteamCurrency or SteamLegacyCurrency or int or str
        :return: An overview of the item on success, :obj:`None` otherwise. Overview includes both volume and prices.
        :rtype: dict[str, bool or float or int or str] or None
        :raises InvalidItemOrAppIDException: Raised when the ``app_id`` or ``market_hash_name``, or the combination of both, is invalid.
        :raises TooManyRequestsException: Raised when the request limit has been reached.
        :raises TypeError: Raised when any of the parameters are of the wrong type.

        .. versionchanged:: 1.3.0
        .. versionadded:: 1.0.0
        """

        data = _request_overview(app_id, market_hash_name, currency or self.currency)
        # if data is None:
        #     # TODO: Raise an exception instead?
        if type_conversion:
            data = self._overview_type_converter(data)

        return data

    @typechecked
    @sanitized
    def get_overviews(
        self,
        app_id: Union[AppID, int, list[Union[AppID, int]]],
        market_hash_names: list[str],
        type_conversion: bool = True,
        currency: Union[SteamCurrency, SteamLegacyCurrency, int, str] = None,
    ) -> dict[str, dict[str, Union[bool, str]]]:
        """Gets the prices and volumes of multiple items in the Steam Community Market.
        
        :param app_id: If given a list, it needs to have the same length as the ``market_hash_names``. If given :obj:`int` or \
            :class:`AppID <steam_community_market.enums.AppID>`, every item in ``market_hash_names`` must have this :class:`AppID <steam_community_market.enums>`.
        :type app_id: AppID or int or list[AppID or int]
        :param market_hash_names: A list of item names how they appear on the Steam Community Market.
        :type market_hash_names: list[str]
        :param type_conversion: Whether to convert the returned values to their corresponding types. Defaults to :obj:`True`.
        :type type_conversion: bool
        :param currency: Currency used for prices. Defaults to the value imposed by the instance of the class.
        :type currency: SteamCurrency or SteamLegacyCurrency or int or str
        :return: An overview of each item. 
        :rtype: dict[str, dict[str, bool or str]]
        :raises IndexError: Raised when ``app_id`` and ``market_hash_names`` have different lengths.
        :raises TooManyRequestsException: Raised when the request limit has been reached.
        :raises TypeError: Raised when any of the parameters are of the wrong type.
        
        .. versionchanged:: 1.3.0
        .. versionadded:: 1.0.0
        """

        if not isinstance(app_id, list):
            app_id = [app_id] * len(market_hash_names)

        if len(market_hash_names) != len(app_id):
            raise IndexError(
                'The length of "market_hash_names" and "app_id" must be the same.'
            )

        return {
            name: (self._overview_type_converter(result) if type_conversion else result)
            for name, id in zip(market_hash_names, app_id)
            for result in [
                _request_overview(
                    id, name, currency or self.currency, raise_exception=False
                )
            ]
        }

    @typechecked
    @sanitized
    def get_overviews_from_dict(
        self,
        items_dict: dict[Union[AppID, int], list[str]],
        type_conversion: bool = True,
        currency: Union[SteamCurrency, SteamLegacyCurrency, int, str] = None,
    ) -> dict[str, dict[str, Union[bool, str]]]:
        """Gets the prices and volumes of multiple items in the Steam Community Market from a dictionary.
        
        :param items_dict: A dictionary containing :class:`AppID <steam_community_market.enums.AppID>` as `keys` and a list of item names as `values`. \
            There is an example on how this dictionary should be constructed in ``example.py``.
        :type items_dict: dict[AppID or int, list[str]]
        :param type_conversion: Whether to convert the returned values to their corresponding types. Defaults to :obj:`True`.
        :type type_conversion: bool
        :param currency: Currency used for prices. Defaults to the value imposed by the instance of the class.
        :type currency: SteamCurrency or SteamLegacyCurrency or int or str
        :return: An overview of each item.
        :rtype: dict[str, dict[str, bool or str]]
        :raises TooManyRequestsException: Raised when the request limit has been reached.
        :raises TypeError: Raised when any of the parameters are of the wrong type.
        
        .. versionchanged:: 1.3.0
        .. versionadded:: 1.1.0
        """

        result = {}
        for app_id, names in items_dict.items():
            for name in names:
                overview = _request_overview(
                    app_id, name, currency or self.currency, raise_exception=False
                )
                if type_conversion:
                    overview = self._overview_type_converter(overview)

                result[name] = overview

        return result

    @typechecked
    @sanitized
    def get_prices(
        self,
        app_id: Union[AppID, int],
        market_hash_name: str,
        type_conversion: bool = True,
        currency: Union[SteamCurrency, SteamLegacyCurrency, int, str] = None,
    ) -> Optional[dict[str, Union[float, str]]]:
        """Gets the lowest and/or median price of an item in the Steam Community Market, if they exist.

        :param app_id: The :class:`AppID <steam_community_market.enums.AppID>` of the game the item is from.
        :type app_id: AppID or int
        :param market_hash_name: The name of the item how it appears on the Steam Community Market.
        :type market_hash_name: str
        :param type_conversion: Whether to convert the returned values to their corresponding types. Defaults to :obj:`True`.
        :type type_conversion: bool
        :param currency: Currency used for prices. Defaults to the value imposed by the instance of the class.
        :type currency: SteamCurrency or SteamLegacyCurrency or int or str
        :return: The lowest and/or median price of the item, if suceess. :obj:`None` otherwise.
        :rtype: dict[str, float or str] or None
        :raises InvalidItemOrAppIDException: Raised when the ``app_id`` or ``market_hash_name``, or the combination of both, is invalid.
        :raises TooManyRequestsException: Raised when the request limit has been reached.
        :raises TypeError: Raised when any of the parameters are of the wrong type.

        .. versionchanged:: 1.3.0
        .. versionadded:: 1.2.0
        """

        item = _request_overview(app_id, market_hash_name, currency or self.currency)
        if item is None:
            return None

        price_keys = ["lowest_price", "median_price"]
        prices = {
            key: (self._price_to_float(item[key]) if type_conversion else item[key])
            for key in price_keys
            if key in item
        }

        return prices or None

    @typechecked
    @sanitized
    def get_lowest_price(
        self,
        app_id: Union[AppID, int],
        market_hash_name: str,
        type_conversion: bool = True,
        currency: Union[SteamCurrency, SteamLegacyCurrency, int, str] = None,
    ) -> Optional[float]:
        """Gets the lowest price of an item in the Steam Community Market, if is exists.

        :param app_id: The :class:`AppID <steam_community_market.enums.AppID>` of the game the item is from.
        :type app_id: AppID or int
        :param market_hash_name: The name of the item how it appears on the Steam Community Market.
        :type market_hash_name: str
        :param type_conversion: Whether to convert the returned values to their corresponding types. Defaults to :obj:`True`.
        :type type_conversion: bool
        :param currency: Currency used for prices. Defaults to the value imposed by the instance of the class.
        :type currency: SteamCurrency or SteamLegacyCurrency or int or str
        :return: The lowest price of the item, if suceess. :obj:`None` otherwise.
        :rtype: float or None
        :raises InvalidItemOrAppIDException: Raised when the ``app_id`` or ``market_hash_name``, or the combination of both, is invalid.
        :raises TooManyRequestsException: Raised when the request limit has been reached.
        :raises TypeError: Raised when any of the parameters are of the wrong type.

        .. versionchanged:: 1.3.0
        .. versionadded:: 1.2.0
        """

        return self._get_price(
            app_id,
            market_hash_name,
            "lowest_price",
            type_conversion,
            currency or self.currency,
        )

    @typechecked
    @sanitized
    def get_median_price(
        self,
        app_id: Union[AppID, int],
        market_hash_name: str,
        type_conversion: bool = True,
        currency: Union[SteamCurrency, SteamLegacyCurrency, int, str] = None,
    ) -> Optional[float]:
        """Gets the median price of an item in the Steam Community Market, if it exists.

        :param app_id: The :class:`AppID <steam_community_market.enums.AppID>` of the game the item is from.
        :type app_id: AppID or int
        :param market_hash_name: The name of the item how it appears on the Steam Community Market.
        :type market_hash_name: str
        :param type_conversion: Whether to convert the returned values to their corresponding types. Defaults to :obj:`True`.
        :type type_conversion: bool
        :param currency: Currency used for prices. Defaults to the value imposed by the instance of the class.
        :type currency: SteamCurrency or SteamLegacyCurrency or int or str
        :return: The median price of the item, if suceess. :obj:`None` otherwise.
        :rtype: float or None
        :raises InvalidItemOrAppIDException: Raised when the ``app_id`` or ``market_hash_name``, or the combination of both, is invalid.
        :raises TooManyRequestsException: Raised when the request limit has been reached.
        :raises TypeError: Raised when any of the parameters are of the wrong type.

        .. versionchanged:: 1.3.0
        .. versionadded:: 1.2.0
        """

        return self._get_price(
            app_id,
            market_hash_name,
            "median_price",
            type_conversion,
            currency or self.currency,
        )

    @typechecked
    @sanitized
    def get_price(
        self,
        app_id: Union[AppID, int],
        market_hash_name: str,
        price_type: str,
        type_conversion: bool = True,
        currency: Union[SteamCurrency, SteamLegacyCurrency, int, str] = None,
    ) -> Optional[float]:
        """Gets the lowest or median price of an item.

        :param app_id: The :class:`AppID <steam_community_market.enums.AppID>` of the game the item is from.
        :type app_id: AppID or int
        :param market_hash_name: The name of the item how it appears on the Steam Community Market.
        :type market_hash_name: str
        :param price_type: The type of price. Can be either ``lowest_price`` or ``median_price``.
        :type price_type: str
        :param type_conversion: Whether to convert the returned values to their corresponding types. Defaults to :obj:`True`.
        :type type_conversion: bool
        :param currency: Currency used for prices. Defaults to the value imposed by the instance of the class.
        :type currency: SteamCurrency or SteamLegacyCurrency or int or str
        :return: The price of the item, if suceess. :obj:`None` otherwise.
        :rtype: float or None
        :raises InvalidItemOrAppIDException: Raised when the ``app_id`` or ``market_hash_name``, or the combination of both, is invalid.
        :raises TooManyRequestsException: Raised when the request limit has been reached.
        :raises TypeError: Raised when any of the parameters are of the wrong type.
        :raises ValueError: Raised when ``price_type`` is not one of ``lowest_price`` or ``median_price``.

        .. versionadded:: 1.3.0
        """

        return self._get_price(
            app_id, market_hash_name, price_type, type_conversion, currency
        )

    @typechecked
    @sanitized
    def get_volume(
        self,
        app_id: Union[AppID, int],
        market_hash_name: str,
        type_conversion: bool = True,
    ) -> Optional[int]:
        """Gets the volume of an item in the Steam Community Market, if it exists.

        :param app_id: The :class:`AppID <steam_community_market.enums.AppID>` of the game the item is from.
        :type app_id: AppID or int
        :param market_hash_name: The name of the item how it appears on the Steam Community Market.
        :type market_hash_name: str
        :param type_conversion: Whether to convert the returned values to their corresponding types. Defaults to :obj:`True`.
        :type type_conversion: bool
        :return: The volume if success, :obj:`None` otherwise.
        :rtype: int or None
        :raises InvalidItemOrAppIDException: Raised when the ``app_id`` or ``market_hash_name``, or the combination of both, is invalid.
        :raises TooManyRequestsException: Raised when the request limit has been reached.
        :raises TypeError: Raised when any of the parameters are of the wrong type.

        .. versionchanged:: 1.3.0
        .. versionadded:: 1.2.0
        """

        item = _request_overview(app_id, market_hash_name, self.currency)
        if item is None or "volume" not in item:
            return None

        return (
            int(item["volume"].replace(",", "")) if type_conversion else item["volume"]
        )

    def _get_price(
        self,
        app_id: Union[AppID, int],
        market_hash_name: str,
        price_type: str,
        type_conversion: bool = True,
        currency: Union[SteamCurrency, SteamLegacyCurrency, int, str] = None,
    ) -> Optional[float]:
        item = _request_overview(app_id, market_hash_name, currency or self.currency)
        if item is None or price_type not in item:
            return None

        return (
            self._price_to_float(item[price_type])
            if type_conversion
            else item[price_type]
        )

    @staticmethod
    def _overview_type_converter(
        overview: dict, keys_to_convert: list[str] = None
    ) -> dict[str, Union[str, int, float]]:
        valid_keys = ["lowest_price", "median_price", "volume"]
        if keys_to_convert is None:
            keys_to_convert = valid_keys

        if any(key not in valid_keys for key in keys_to_convert):
            raise ValueError(
                f'Invalid key found in "keys_to_convert". The valid keys are: {", ".join(valid_keys)}.'
            )

        result = {}
        for key, value in overview.items():
            if key in keys_to_convert and key in ["lowest_price", "median_price"]:
                result[key] = Market._price_to_float(value)
            elif key in keys_to_convert and key == "volume":
                result[key] = int(value.replace(",", ""))
            else:
                result[key] = value

        return result

    @staticmethod
    def _price_to_float(value: str) -> Optional[float]:
        if not (match := re.search(r"(\d{1,3}(?:[.,]\d{3})*)(?:[.,](\d{2}))?", value)):
            return None

        num_str = match[1].replace(",", "").replace(".", "")
        decimal_part = match[2] if match[2] is not None else "00"
        return float(f"{num_str}.{decimal_part}")
