import itertools
import re
import subprocess
import typing as t
from pathlib import Path

from loguru import logger

from ..config import AppConfig

T = t.TypeVar("T", bound="LedgerClient")


class LedgerClientException(Exception):
    pass


class LedgerCmd:

    def __init__(self, client: 'LedgerClient') -> None:
        self._client = client
        self._cmd_base = ["ledger", "-f", str(client.transactions_path)]
        self._options: dict[str, str] = {}
        self._args: list[str] = []
        self._accounts: list[str] = []

        if client.price_db_path.exists():
            self._options["--price-db"] = str(client.price_db_path)

    @staticmethod
    def _to_option_name(key: str) -> str:
        key = key.replace("_", "-")
        return f"--{str(key)}"

    @staticmethod
    def _to_option_value(value: t.Any) -> str:
        return str(value)

    @property
    def _options_list(self):
        return list(itertools.chain.from_iterable(self._options.items()))

    def _list_accounts(self) -> list[str]:
        cmd = [*self._cmd_base, "accounts"]
        accounts = [s.strip() for s in self._client.call(cmd).split("\n")]
        accounts = [s for s in accounts if s]

        return accounts

    def _search_accounts(self, *patterns: str) -> list[str]:
        accounts = self._list_accounts()
        result = set()

        for pattern in patterns:
            regex = re.compile(pattern)
            for account in accounts:
                if regex.match(account) or pattern in account:
                    result.add(account)

        return list(result)

    def add_options(self, **options: t.Any) -> 'LedgerCmd':
        for option_name, option_value in options.items():
            if not option_value:
                continue

            self._options[self._to_option_name(option_name)] = self._to_option_value(option_value)

        return self

    def add_arguments(self, *arguments: t.Any) -> 'LedgerCmd':
        self._args.extend(map(self._to_option_value, arguments))

        return self

    def add_accounts(self, *patterns: str) -> 'LedgerCmd':
        accounts = self._search_accounts(*patterns)
        self._accounts.extend(accounts)

        return self

    def build(self) -> list[str]:
        return [*self._cmd_base, *self._args, *self._options_list, *self._accounts]

    def call(self) -> str:
        return self._client.call(self.build())


class LedgerClient:

    def __init__(self, transactions_path: Path, price_db_path: Path) -> None:
        self.transactions_path = transactions_path
        self.price_db_path = price_db_path

    @classmethod
    def from_config(cls: t.Type[T], config: AppConfig) -> T:
        return cls(
            transactions_path=config.transactions_path,
            price_db_path=config.price_db_settings.path,
        )

    def call(self, cmd: list[str]) -> str:
        logger.debug("Exec cmd: {}", cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate()

        if stderr:
            raise LedgerClientException(stderr)

        return stdout
