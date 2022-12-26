import enum
import json
import re
from datetime import datetime

import arrow
import pydantic


class Consts:
    APP_NAME = "ledger-manager"
    DEFAULT_CONFIG_FILE_NAME = "config.yaml"
    DATE_FORMAT = "%Y-%m-%d"


class FloorType(str, enum.Enum):
    day = "day"
    week = "week"
    month = "month"
    quarter = "quarter"
    year = "year"

    def aggregation_type(self, shift: int = 1) -> "AggregationType":
        cur_index = list(self.__class__).index(self)
        new_index = max(cur_index - shift, 0)

        return list(AggregationType)[new_index]


class AggregationType(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"

    def to_option(self) -> str:
        return f"--{self.value}"


class ExchangeRate(pydantic.BaseModel):
    # P 2004/06/21 02:18:01 RUB 22.49 $
    date: datetime
    symbol: str
    price: float
    price_symbol: str

    @pydantic.validator('date', pre=True)
    def time_validate(cls, v):
        if isinstance(v, str):
            return arrow.get(v).datetime

        return v

    class Config:
        DATETIME_FMT = "%Y/%m/%d %H:%M:%S"
        DB_ROW_FMT_READ = re.compile((r"^P\s*"
                                      r"(?P<date>\d{4}/\d{2}/\d{2}\s\d{2}:\d{2}:\d{2})\s*"
                                      r"(?P<symbol>[\S]+)\s*"
                                      r"(?P<price>\d+(\.|\,)\d*)\s*"
                                      r"(?P<price_symbol>[\S]+)$"))
        DB_ROW_FMT_WRITE = ("P {date} {symbol} {price} {price_symbol}")

        json_encoders = {
            datetime: lambda v: v.strftime(ExchangeRate.Config.DATETIME_FMT),
        }

    @classmethod
    def from_db_row(cls, row: str):
        row = row.strip("\n ")
        match = cls.Config.DB_ROW_FMT_READ.match(row)

        if not match:
            raise ValueError(f"Row '{row}' dosen't match format.")

        groups = match.groupdict()

        data = {
            "date": arrow.get(groups["date"]).datetime,
            "symbol": groups["symbol"],
            "price": groups["price"],
            "price_symbol": groups["price_symbol"],
        }

        return cls.parse_obj(data)

    def to_db_row(self) -> str:
        return self.Config.DB_ROW_FMT_WRITE.format_map(json.loads(self.json()))
