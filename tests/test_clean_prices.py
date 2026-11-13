"""Tests for ``var_calculator.data.clean_prices``."""

import warnings

import numpy as np
import pandas as pd
import pytest

from var_calculator.data import PriceDataWarning, clean_prices

NAN = float("nan")


def make_prices(columns: dict[str, list[float]]) -> pd.DataFrame:
    length = len(next(iter(columns.values())))
    index = pd.bdate_range("2020-01-01", periods=length, name="Date")
    return pd.DataFrame(columns, index=index, dtype=float)


def test_clean_table_is_returned_unchanged():
    prices = make_prices({"ALFA": [100.0, 101.0, 102.0], "BETA": [50.0, 49.0, 51.0]})

    cleaned = clean_prices(prices)

    pd.testing.assert_frame_equal(cleaned, prices, check_freq=False)
    assert cleaned.index.name == "Date"


def test_input_is_not_modified():
    prices = make_prices({"ALFA": [100.0, NAN, 0.0], "BETA": [50.0, 49.0, 51.0]})
    original = prices.copy()

    with pytest.warns(PriceDataWarning):
        clean_prices(prices)

    pd.testing.assert_frame_equal(prices, original)


def test_rows_without_any_price_are_removed():
    prices = make_prices({"ALFA": [100.0, NAN, 102.0], "BETA": [50.0, NAN, 51.0]})

    cleaned = clean_prices(prices)

    assert list(cleaned.index) == [prices.index[0], prices.index[2]]
    assert cleaned["ALFA"].tolist() == [100.0, 102.0]


def test_empty_rows_do_not_use_up_the_fill_limit():
    prices = make_prices(
        {"ALFA": [100.0, NAN, NAN, 103.0], "BETA": [50.0, NAN, 52.0, 53.0]}
    )

    cleaned = clean_prices(prices, max_fill=1)

    assert cleaned["ALFA"].tolist() == [100.0, 100.0, 103.0]
    assert cleaned["BETA"].tolist() == [50.0, 52.0, 53.0]


def test_gaps_are_forward_filled_with_the_last_price():
    prices = make_prices({"ALFA": [100.0, NAN, 102.0], "BETA": [50.0, 49.0, 51.0]})

    cleaned = clean_prices(prices)

    assert cleaned["ALFA"].tolist() == [100.0, 100.0, 102.0]
    assert cleaned["BETA"].tolist() == [50.0, 49.0, 51.0]


def test_forward_fill_is_limited():
    prices = make_prices(
        {
            "ALFA": [100.0, NAN, NAN, NAN, 104.0],
            "BETA": [50.0, 51.0, 52.0, 53.0, 54.0],
        }
    )

    cleaned = clean_prices(prices, max_fill=2)

    assert list(cleaned.index) == list(prices.index[[0, 1, 2, 4]])
    assert cleaned["ALFA"].tolist() == [100.0, 100.0, 100.0, 104.0]


def test_long_gap_is_kept_when_incomplete_rows_are_not_dropped():
    prices = make_prices(
        {
            "ALFA": [100.0, NAN, NAN, NAN, 104.0],
            "BETA": [50.0, 51.0, 52.0, 53.0, 54.0],
        }
    )

    cleaned = clean_prices(prices, max_fill=2, drop_incomplete=False)

    assert len(cleaned) == 5
    np.testing.assert_array_equal(
        cleaned["ALFA"].to_numpy(), [100.0, 100.0, 100.0, NAN, 104.0]
    )


def test_max_fill_zero_disables_forward_fill():
    prices = make_prices({"ALFA": [100.0, NAN, 102.0], "BETA": [50.0, 49.0, 51.0]})

    cleaned = clean_prices(prices, max_fill=0)

    assert list(cleaned.index) == [prices.index[0], prices.index[2]]


def test_dates_before_the_first_price_of_an_asset_are_dropped():
    prices = make_prices({"ALFA": [100.0, 101.0, 102.0], "BETA": [NAN, NAN, 51.0]})

    cleaned = clean_prices(prices)

    assert list(cleaned.index) == [prices.index[2]]
    assert not cleaned.isna().any().any()


def test_leading_gap_is_never_back_filled():
    prices = make_prices({"ALFA": [100.0, 101.0, 102.0], "BETA": [NAN, 49.0, 51.0]})

    cleaned = clean_prices(prices, drop_incomplete=False)

    assert np.isnan(cleaned["BETA"].iloc[0])


def test_unsorted_dates_are_sorted():
    prices = make_prices({"ALFA": [100.0, 101.0, 102.0], "BETA": [50.0, 49.0, 51.0]})

    cleaned = clean_prices(prices.iloc[::-1])

    assert cleaned.index.is_monotonic_increasing
    pd.testing.assert_frame_equal(cleaned, prices, check_freq=False)


def test_integer_prices_become_float():
    index = pd.bdate_range("2020-01-01", periods=2, name="Date")
    prices = pd.DataFrame({"ALFA": [100, 101]}, index=index)

    cleaned = clean_prices(prices)

    assert cleaned["ALFA"].dtype == float


@pytest.mark.parametrize("bad", [0.0, -5.0, float("inf"), float("-inf")])
def test_invalid_prices_warn_and_are_treated_as_missing(bad):
    prices = make_prices({"ALFA": [100.0, bad, 102.0], "BETA": [50.0, 49.0, 51.0]})

    with pytest.warns(PriceDataWarning, match=r"1 non-positive.*ALFA \(1\)"):
        cleaned = clean_prices(prices)

    assert cleaned["ALFA"].tolist() == [100.0, 100.0, 102.0]


def test_warning_counts_invalid_prices_per_asset():
    prices = make_prices({"ALFA": [100.0, 0.0, -1.0], "BETA": [0.0, 49.0, 51.0]})

    with pytest.warns(PriceDataWarning, match=r"3 non-pos.*ALFA \(2\), BETA \(1\)"):
        clean_prices(prices, drop_incomplete=False)


def test_no_warning_for_valid_prices():
    prices = make_prices({"ALFA": [100.0, NAN, 102.0]})

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        clean_prices(prices)


def test_random_gaps_leave_a_complete_positive_table():
    rng = np.random.default_rng(42)
    values = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, size=(300, 4)), axis=0))
    observed = rng.random(values.shape) >= 0.1
    index = pd.bdate_range("2020-01-01", periods=300, name="Date")
    full = pd.DataFrame(values, index=index, columns=list("ABCD"))
    prices = full.where(observed)

    cleaned = clean_prices(prices)

    assert not cleaned.isna().any().any()
    assert (cleaned > 0).all().all()
    assert cleaned.index.is_monotonic_increasing
    assert set(cleaned.index) <= set(prices.index)
    # Observed prices are untouched; only the gaps were filled.
    kept = prices.loc[cleaned.index]
    pd.testing.assert_frame_equal(cleaned.where(kept.notna()), kept, check_freq=False)


def test_all_missing_raises():
    prices = make_prices({"ALFA": [NAN, NAN], "BETA": [NAN, NAN]})

    with pytest.raises(ValueError, match="no dates are left"):
        clean_prices(prices)


def test_no_common_dates_raises():
    prices = make_prices({"ALFA": [100.0, NAN], "BETA": [NAN, 50.0]})

    with pytest.raises(ValueError, match="no dates are left"):
        clean_prices(prices, max_fill=0)


def test_negative_max_fill_raises():
    prices = make_prices({"ALFA": [100.0, 101.0]})

    with pytest.raises(ValueError, match="max_fill must be non-negative"):
        clean_prices(prices, max_fill=-1)


@pytest.mark.parametrize("bad", [1.5, True, "2"])
def test_non_integer_max_fill_raises(bad):
    prices = make_prices({"ALFA": [100.0, 101.0]})

    with pytest.raises(TypeError, match="max_fill must be an integer"):
        clean_prices(prices, max_fill=bad)


def test_not_a_dataframe_raises():
    with pytest.raises(TypeError, match="must be a pandas DataFrame"):
        clean_prices([[100.0, 101.0]])


def test_index_must_be_dates():
    prices = pd.DataFrame({"ALFA": [100.0, 101.0]})

    with pytest.raises(TypeError, match="DatetimeIndex"):
        clean_prices(prices)


def test_no_columns_raises():
    prices = pd.DataFrame(index=pd.bdate_range("2020-01-01", periods=2))

    with pytest.raises(ValueError, match="no asset columns"):
        clean_prices(prices)


def test_duplicate_dates_raise():
    index = pd.DatetimeIndex(["2020-01-01", "2020-01-01"])
    prices = pd.DataFrame({"ALFA": [100.0, 101.0]}, index=index)

    with pytest.raises(ValueError, match="duplicate date in prices: 2020-01-01"):
        clean_prices(prices)


def test_missing_date_in_index_raises():
    index = pd.DatetimeIndex(["2020-01-01", None])
    prices = pd.DataFrame({"ALFA": [100.0, 101.0]}, index=index)

    with pytest.raises(ValueError, match="missing dates"):
        clean_prices(prices)


def test_non_numeric_column_raises():
    index = pd.bdate_range("2020-01-01", periods=2)
    prices = pd.DataFrame({"ALFA": ["100", "101"]}, index=index)

    with pytest.raises(TypeError, match="'ALFA' of prices is not numeric"):
        clean_prices(prices)
