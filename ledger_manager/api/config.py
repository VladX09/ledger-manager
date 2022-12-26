import datetime
import importlib.resources
import typing as t
from pathlib import Path

import arrow
import pydantic
import yaml
from typer import get_app_dir

from .models import Consts

BUILTIN_CONFIG_PATH = importlib.resources.path("ledger_manager", Consts.DEFAULT_CONFIG_FILE_NAME)
APP_CONFIG_PATH = Path(get_app_dir(Consts.APP_NAME)) / Consts.DEFAULT_CONFIG_FILE_NAME


def yaml_config_source(path: Path):

    def _reader(*args, **kwargs) -> dict[str, t.Any]:
        if not path.exists():
            return {}

        with open(path) as fp:
            return yaml.safe_load(fp)

    return _reader


class PriceDBSettings(pydantic.BaseModel):
    path: Path
    start_date: datetime.datetime

    @pydantic.validator("start_date", pre=True)
    def _start_date_v(cls, val: str) -> datetime.datetime:
        return arrow.get(val).datetime

    @pydantic.validator("path")
    def _path_v(cls, val: Path) -> Path:
        return val.absolute()


class ExchangeRatesSettings(pydantic.BaseModel):
    api_url: str
    api_key: str
    main_currency: str
    currencies: list[str]
    currency_aliases: dict[str, str]


class AppConfig(pydantic.BaseSettings):
    transactions_path: Path
    exchange_rates_api_settings: ExchangeRatesSettings
    price_db_settings: PriceDBSettings

    @pydantic.validator("transactions_path")
    def _transactions_path_v(cls, val: Path) -> Path:
        val = val.absolute()

        if not val.exists():
            raise ValueError(f"Transactions file '{val}' not found. Configure transaction file path")

        return val

    class Config:

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                yaml_config_source(APP_CONFIG_PATH),
                yaml_config_source(BUILTIN_CONFIG_PATH),
                env_settings,
                file_secret_settings,
            )

    @classmethod
    def from_file(cls, path: t.Optional[Path] = None):
        if not path:
            return cls()

        config = yaml_config_source(path)()
        return cls.parse_obj(config)
