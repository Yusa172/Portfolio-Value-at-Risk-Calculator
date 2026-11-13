"""Tests for ``var_calculator.data.load_prices_csv``."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from var_calculator.data import load_prices_csv

SAMPLE_CSV = Path(__file__).resolve().parents[1] / "data" / "sample_prices.csv"

WIDE = """\
Date,ALFA,BETA
2020-01-01,100.0,50.0
2020-01-02,101.5,49.5
2020-01-03,99.0,51.25
"""

LONG = """\
Date,Ticker,Price
2020-01-01,ALFA,100.0
2020-01-01,BETA,50.0
2020-01-02,ALFA,101.5
2020-01-02,BETA,49.5
2020-01-03,ALFA,99.0
2020-01-03,BETA,51.25
"""


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "prices.csv"
    path.write_text(text, encoding="utf-8")
    return path


def expected_prices() -> pd.DataFrame:
    index = pd.DatetimeIndex(["2020-01-01", "2020-01-02", "2020-01-03"], name="Date")
    return pd.DataFrame(
        {"ALFA": [100.0, 101.5, 99.0], "BETA": [50.0, 49.5, 51.25]}, index=index
    )


def assert_prices_equal(actual: pd.DataFrame, expected: pd.DataFrame) -> None:
    pd.testing.assert_frame_equal(
        actual, expected, check_freq=False, check_index_type=False, check_dtype=True
    )
    assert actual.index.name == "Date"
    assert actual.columns.name is None


def test_wide_format(tmp_path):
    prices = load_prices_csv(write(tmp_path, WIDE))

    assert isinstance(prices.index, pd.DatetimeIndex)
    assert_prices_equal(prices, expected_prices())


def test_long_format(tmp_path):
    prices = load_prices_csv(write(tmp_path, LONG))

    assert isinstance(prices.index, pd.DatetimeIndex)
    assert_prices_equal(prices, expected_prices())


def test_wide_and_long_give_the_same_table(tmp_path):
    wide = load_prices_csv(write(tmp_path, WIDE))
    long = load_prices_csv(write(tmp_path, LONG))

    pd.testing.assert_frame_equal(wide, long)


def test_accepts_path_as_string(tmp_path):
    prices = load_prices_csv(str(write(tmp_path, WIDE)))

    assert prices.shape == (3, 2)


def test_sample_file_loads():
    prices = load_prices_csv(SAMPLE_CSV)

    assert list(prices.columns) == ["ALFA", "BETA", "GAMA", "DELTA"]
    assert prices.shape == (750, 4)
    assert prices.index.is_monotonic_increasing
    assert prices.index[0] == pd.Timestamp("2020-01-01")
    assert all(dtype == np.float64 for dtype in prices.dtypes)
    assert np.allclose(prices.iloc[0].to_numpy(), 100.0)


def test_rows_are_sorted_by_date(tmp_path):
    text = "Date,ALFA\n2020-01-03,3\n2020-01-01,1\n2020-01-02,2\n"

    prices = load_prices_csv(write(tmp_path, text))

    assert prices.index.is_monotonic_increasing
    assert prices["ALFA"].tolist() == [1.0, 2.0, 3.0]


def test_long_columns_follow_first_appearance(tmp_path):
    text = "Date,Ticker,Price\n2020-01-01,ZETA,1\n2020-01-01,ALFA,2\n"

    prices = load_prices_csv(write(tmp_path, text))

    assert list(prices.columns) == ["ZETA", "ALFA"]


def test_column_names_ignore_case_and_whitespace(tmp_path):
    text = " date , TICKER, price ,Volume\n2020-01-01, ALFA ,100,5000\n"

    prices = load_prices_csv(write(tmp_path, text))

    assert list(prices.columns) == ["ALFA"]
    assert prices.loc["2020-01-01", "ALFA"] == 100.0


def test_custom_column_names(tmp_path):
    text = "Dia,Ativo,Fecho\n2020-01-01,ALFA,100\n2020-01-02,ALFA,101\n"

    prices = load_prices_csv(
        write(tmp_path, text),
        date_column="Dia",
        ticker_column="Ativo",
        price_column="Fecho",
    )

    assert prices["ALFA"].tolist() == [100.0, 101.0]
    assert prices.index.name == "Date"


def test_missing_prices_are_kept_as_nan_in_wide(tmp_path):
    text = "Date,ALFA,BETA\n2020-01-01,100,\n2020-01-02,,50\n"

    prices = load_prices_csv(write(tmp_path, text))

    assert np.isnan(prices.loc["2020-01-01", "BETA"])
    assert np.isnan(prices.loc["2020-01-02", "ALFA"])
    assert prices.loc["2020-01-01", "ALFA"] == 100.0


def test_missing_pairs_are_nan_in_long(tmp_path):
    text = (
        "Date,Ticker,Price\n"
        "2020-01-01,ALFA,100\n"
        "2020-01-02,ALFA,101\n"
        "2020-01-02,BETA,50\n"
    )

    prices = load_prices_csv(write(tmp_path, text))

    assert prices.shape == (2, 2)
    assert np.isnan(prices.loc["2020-01-01", "BETA"])
    assert prices.loc["2020-01-02", "BETA"] == 50.0


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_prices_csv(tmp_path / "does_not_exist.csv")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("Day,ALFA\n2020-01-01,100\n", "missing required column 'Date'"),
        ("Date,Ticker,Close\n2020-01-01,ALFA,100\n", "missing required column 'Price'"),
        ("Date\n2020-01-01\n", "no price columns"),
        ("Date,ALFA\n", "no price rows"),
        ("Date,ALFA,alfa\n2020-01-01,1,2\n", "duplicate column name"),
        ("Date,ALFA,ALFA\n2020-01-01,1,2\n", "duplicate column name"),
        ("Date,ALFA\nnot-a-date,100\n", "could not parse the date column"),
        ("Date,ALFA\n,100\n", "date column has empty values"),
        ("Date,ALFA\n2020-01-01,abc\n", "non-numeric price in column 'ALFA'"),
        ("Date,Ticker,Price\n2020-01-01,ALFA,abc\n", "non-numeric price"),
        ("Date,Ticker,Price\n2020-01-01,,100\n", "'Ticker' column has empty values"),
        ("Date,ALFA\n2020-01-01,1\n2020-01-01,2\n", "duplicate date"),
        (
            "Date,Ticker,Price\n2020-01-01,ALFA,1\n2020-01-01,ALFA,2\n",
            "duplicate \\(date, ticker\\) pair",
        ),
    ],
)
def test_invalid_files_raise_value_error(tmp_path, text, message):
    with pytest.raises(ValueError, match=message):
        load_prices_csv(write(tmp_path, text))
