import itertools
import typing as t
from datetime import datetime

import arrow
from loguru import logger

from ledger_manager.console import console

from .config import AppConfig
from .models import AggregationType, Consts, ExchangeRate, FloorType
from .services import ExchangeRatesClient, LedgerClient, LedgerCmd, PriceDB

EPOCH_BEGIN = arrow.get(1980, 1, 1)


def get_leger_end_day() -> arrow.Arrow:
    return arrow.now().floor('days').shift(days=1)


def forward(
    *args,
    config: AppConfig,
    patterns: t.Optional[t.List[str]] = None,
):
    client = LedgerClient.from_config(config)
    patterns = patterns or []

    output = LedgerCmd(client).add_accounts(*patterns).add_arguments(*args).call()

    console.print(output)


def balance(
    *args,
    config: AppConfig,
    patterns: t.Optional[t.List[str]] = None,
    end: t.Optional[datetime] = None,
    floor: t.Optional[FloorType] = None,
    begin: t.Optional[datetime] = None,
    **options: t.Any,
):
    client = LedgerClient.from_config(config)
    end_arrow = arrow.get(end) if end else get_leger_end_day()
    patterns = patterns or []

    if not begin:
        if floor:
            begin_arrow = end_arrow.floor(floor.value)  # type: ignore
        else:
            begin_arrow = EPOCH_BEGIN
    else:
        begin_arrow = arrow.get(begin)

    output = LedgerCmd(client).add_arguments("balance", *args).add_accounts(*patterns).add_options(
        begin=begin_arrow.datetime.strftime(Consts.DATE_FORMAT),
        end=end_arrow.datetime.strftime(Consts.DATE_FORMAT),
        **options,
    ).call()

    console.print(output)


def average(
    *args,
    config: AppConfig,
    patterns: t.Optional[t.List[str]] = None,
    end: t.Optional[datetime] = None,
    floor: t.Optional[FloorType] = None,
    begin: t.Optional[datetime] = None,
    aggregation: t.Optional[AggregationType] = None,
    **options: t.Any,
):
    client = LedgerClient.from_config(config)
    end_arrow = arrow.get(end) if end else get_leger_end_day()
    patterns = patterns or []

    if not aggregation:
        if floor:
            aggregation = floor.aggregation_type()
        else:
            aggregation = AggregationType.daily

    if not begin:
        if floor:
            begin_arrow = end_arrow.floor(floor.value)  # type: ignore
        else:
            begin_arrow = EPOCH_BEGIN
    else:
        begin_arrow = arrow.get(begin)

    output = LedgerCmd(client).add_arguments(
        "register",
        aggregation.to_option(),
        "--average",
        "--collapse",
        *args,
    ).add_accounts(*patterns).add_options(
        begin=begin_arrow.datetime.strftime(Consts.DATE_FORMAT),
        end=end_arrow.datetime.strftime(Consts.DATE_FORMAT),
        **options,
    ).call()
    console.print(output)


def update_price_db(config: AppConfig):
    price_db = PriceDB.from_config(config)
    exchange_api = ExchangeRatesClient.from_config(config)

    intervals = prepare_date_intervals(
        db_start=config.price_db_settings.start_date,
        first_record=price_db.first_record(),
        last_record=price_db.last_record(),
    )

    logger.debug("Update price DB for intervals: {}", intervals)
    for interval in intervals:
        rows = exchange_api.get_rates(*interval)
        price_db.append_rows(rows)


def prepare_date_intervals(
    db_start: datetime,
    first_record: ExchangeRate | None,
    last_record: ExchangeRate | None,
) -> list[tuple[datetime, datetime]]:
    now = arrow.utcnow().floor("days").datetime
    intervals = []

    if first_record and last_record:
        if first_record.date > db_start:
            intervals.append((db_start, arrow.get(first_record.date).shift(days=-1).datetime))

        if last_record.date < now:
            intervals.append((arrow.get(last_record.date).shift(days=1).datetime, now))

    else:
        intervals.append((db_start, now))

    return list(itertools.chain.from_iterable(map(split_by_year, intervals)))


def split_by_year(region: tuple[datetime, datetime]) -> list[tuple[datetime, datetime]]:
    from_date, to_date = sorted(map(arrow.get, region))

    dt = from_date
    intervals: list[tuple[datetime, datetime]] = []

    while dt.shift(years=1, days=-1) < to_date:
        intervals.append((dt.datetime, dt.shift(years=1, days=-1).datetime))
        dt = dt.shift(years=1)

    intervals.append((dt.datetime, to_date.datetime))
    return intervals
