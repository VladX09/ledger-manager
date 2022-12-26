from pathlib import Path
from unittest.mock import MagicMock, patch

import arrow
import pytest

from ledger_manager.api.models import ExchangeRate
from ledger_manager.api.services import ExchangeRatesClient, PriceDB
from ledger_manager.api.use_cases import prepare_date_intervals, split_by_year


@pytest.mark.parametrize(["region", "splits"], [
    (("2001-01-01", "2003-01-01"), [
        ("2001-01-01", "2001-12-31"),
        ("2002-01-01", "2002-12-31"),
        ("2003-01-01", "2003-01-01"),
    ]),
    (("2003-01-01", "2001-01-01"), [
        ("2001-01-01", "2001-12-31"),
        ("2002-01-01", "2002-12-31"),
        ("2003-01-01", "2003-01-01"),
    ]),
    (("2001-05-05", "2003-08-12"), [
        ("2001-05-05", "2002-05-04"),
        ("2002-05-05", "2003-05-04"),
        ("2003-05-05", "2003-08-12"),
    ]),
])
def test_split_by_year(region, splits):
    region = tuple(arrow.get(d).datetime for d in region)
    splits = [tuple(arrow.get(d).datetime for d in r) for r in splits]

    assert split_by_year(region) == splits


def record_mock(date: str | None):
    dt = arrow.get(date).datetime if date else None
    return MagicMock(date=dt)


@pytest.mark.parametrize(
    ["db_start", "first_record", "last_record", "splits"],
    [
        (
            "2001-01-01",
            record_mock("2002-01-10"),
            record_mock("2002-05-10"),
            [
                ("2001-01-01", "2001-12-31"),
                ("2002-01-01", "2002-01-09"),
                ("2002-05-11", "2003-05-10"),
                ("2003-05-11", "2003-08-12"),
            ],
        ),
    ],
)
def test_prepare_intervals(
    db_start,
    first_record,
    last_record,
    splits,
):
    with patch("arrow.utcnow") as patcher:
        patcher.return_value = arrow.get(2003, 8, 12)

        db_start = arrow.get(db_start).datetime
        splits = [tuple(arrow.get(d).datetime for d in r) for r in splits]

        result = prepare_date_intervals(db_start, first_record, last_record)
        assert result == splits


def test_get_rates(apilayer_mock):
    client = ExchangeRatesClient(
        api_url=apilayer_mock,
        api_key="ANY",
        base_symbol="USD",
        symbols=["RUB", "GEL", "TRY", "EUR"],
        currency_aliases={
            "RUB": "₽",
        },
    )

    result = client.get_rates(arrow.get("2022-12-01").datetime, arrow.get("2022-12-02").datetime)
    result = [r.to_db_row() for r in result]

    assert result == [
        'P 2022/12/01 00:00:00 USD 0.94985 EUR',
        'P 2022/12/01 00:00:00 USD 2.704993 GEL',
        'P 2022/12/01 00:00:00 USD 61.214998 ₽',
        'P 2022/12/01 00:00:00 USD 18.637949 TRY',
        'P 2022/12/02 00:00:00 USD 0.94905 EUR',
        'P 2022/12/02 00:00:00 USD 2.69504 GEL',
        'P 2022/12/02 00:00:00 USD 62.50369 ₽',
        'P 2022/12/02 00:00:00 USD 18.633904 TRY',
    ]


def test_prices_db_ops(tmp_path: Path):
    db_path = tmp_path / "prices.db"
    db = PriceDB(db_path)

    assert db.read_db() == []
    assert db.first_record() is None
    assert db.last_record() is None

    rows = [
        ExchangeRate(date=arrow.get(2001, 1, 1).datetime, symbol="RUB", price=30.05, price_symbol="$"),
        ExchangeRate(date=arrow.get(2001, 1, 2).datetime, symbol="RUB", price=31.05, price_symbol="$"),
        ExchangeRate(date=arrow.get(2001, 1, 3).datetime, symbol="RUB", price=34.05, price_symbol="$"),
    ]

    db.append_rows(rows)
    assert db.read_db() == rows
    assert db.first_record() == rows[0]
    assert db.last_record() == rows[-1]
