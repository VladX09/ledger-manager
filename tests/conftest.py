import pytest
import requests_mock

APILAYER_EXCHANGE_RATES_TIMESERIES = {
    "base": "USD",
    "end_date": "2022-12-02",
    "rates": {
        "2022-12-01": {
            "EUR": 0.94985,
            "GEL": 2.704993,
            "RUB": 61.214998,
            "TRY": 18.637949
        },
        "2022-12-02": {
            "EUR": 0.94905,
            "GEL": 2.69504,
            "RUB": 62.50369,
            "TRY": 18.633904
        },
    },
    "start_date": "2022-12-01",
    "success": True,
    "timeseries": True
}


@pytest.fixture
def apilayer_mock():
    api_url = 'http://test.com'
    with requests_mock.Mocker() as m:
        m.get('http://test.com/timeseries', json=APILAYER_EXCHANGE_RATES_TIMESERIES)
        yield api_url
