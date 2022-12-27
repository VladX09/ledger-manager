import typing as t
from datetime import datetime

import pydantic
import requests

from ..config import AppConfig
from ..models import Consts, ExchangeRate

T = t.TypeVar("T", bound="ExchangeRatesClient")


class ExchangeRatesAPIException(Exception):
    pass


class TimeSeries(pydantic.BaseModel):
    rates: dict[datetime, dict[str, float]]

    @pydantic.validator("rates", pre=True)
    def rates_validate(cls, val):
        return {datetime.strptime(k, Consts.DATE_FORMAT): v for k, v in val.items()}


class ExchangeRatesClient:

    def __init__(
        self,
        api_url: str,
        api_key: str,
        base_symbol: str,
        symbols: list[str],
        currency_aliases: dict[str, str],
    ) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.base_symbol = base_symbol
        self.symbols = symbols
        self.currency_aliases = currency_aliases

    @classmethod
    def from_config(cls: t.Type[T], config: AppConfig) -> T:
        return cls(
            api_url=config.exchange_rates_api_settings.api_url,
            api_key=config.exchange_rates_api_settings.api_key,
            base_symbol=config.exchange_rates_api_settings.main_currency,
            symbols=config.exchange_rates_api_settings.currencies,
            currency_aliases=config.exchange_rates_api_settings.currency_aliases,
        )

    def timeseries_url(self) -> str:
        return f"{self.api_url}/timeseries"

    def auth_header(self) -> dict[str, str]:
        return {"apikey": self.api_key}

    def get_rates(self, start_date: datetime, end_date: datetime) -> t.Iterable[ExchangeRate]:
        response = requests.get(
            url=self.timeseries_url(),
            headers=self.auth_header(),
            params={
                "start_date": start_date.strftime(Consts.DATE_FORMAT),
                "end_date": end_date.strftime(Consts.DATE_FORMAT),
                "base": self.base_symbol,
                "symbols": ",".join(self.symbols),
            },
        )

        try:
            response.raise_for_status()
            response_body = response.json()
            data = TimeSeries.parse_obj(response_body)

        except requests.HTTPError as exc:
            raise ExchangeRatesAPIException("Incorrect exchange rate API response") from exc

        for date, record in data.rates.items():
            for symbol, price in record.items():
                yield ExchangeRate(
                    date=date,
                    symbol=self.currency_aliases.get(self.base_symbol, self.base_symbol),
                    price=price,
                    price_symbol=self.currency_aliases.get(symbol, symbol),
                )
