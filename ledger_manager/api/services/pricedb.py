import typing as t
from pathlib import Path

from ..config import AppConfig
from ..models import ExchangeRate

T = t.TypeVar("T", bound="PriceDB")


class PriceDB:

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    @classmethod
    def from_config(cls: t.Type[T], config: AppConfig) -> T:
        return cls(db_path=config.price_db_settings.path)

    def read_db(self) -> list[ExchangeRate]:
        if not self.db_path.exists():
            return []

        with open(self.db_path, "r") as fp:
            return [ExchangeRate.from_db_row(row) for row in fp.readlines()]

    def first_record(self) -> ExchangeRate | None:
        records = self.read_db()
        return min(records, key=lambda r: r.date, default=None)  # type: ignore

    def last_record(self) -> ExchangeRate | None:
        records = self.read_db()
        return max(records, key=lambda r: r.date, default=None)  # type: ignore

    def append_rows(self, rows: t.Iterable[ExchangeRate]) -> None:
        rows = sorted(list(rows), key=lambda r: r.date)

        with open(self.db_path, "a") as fp:
            fp.writelines([f"{r.to_db_row()}\n" for r in rows])
