import importlib.util
from pathlib import Path
from types import ModuleType

import numpy as np
import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "make_sample_data.py"


@pytest.fixture(scope="module")
def sample_data() -> ModuleType:
    spec = importlib.util.spec_from_file_location("make_sample_data", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_shape_columns_and_index(sample_data):
    prices = sample_data.generate_sample_prices(n_days=100)

    assert prices.shape == (100, len(sample_data.TICKERS))
    assert list(prices.columns) == list(sample_data.TICKERS)
    assert prices.index.name == "Date"
    assert prices.index[0] == pd.Timestamp(sample_data.START_DATE)
    assert all(day.weekday() < 5 for day in prices.index)


def test_first_row_is_start_price(sample_data):
    prices = sample_data.generate_sample_prices(n_days=10)

    assert np.allclose(prices.iloc[0].to_numpy(), sample_data.START_PRICE)


def test_prices_are_strictly_positive(sample_data):
    prices = sample_data.generate_sample_prices(n_days=500)

    assert (prices > 0).all().all()


def test_same_seed_gives_identical_output(sample_data):
    first = sample_data.generate_sample_prices(n_days=50, seed=7)
    second = sample_data.generate_sample_prices(n_days=50, seed=7)

    pd.testing.assert_frame_equal(first, second)


def test_different_seed_gives_different_output(sample_data):
    first = sample_data.generate_sample_prices(n_days=50, seed=1)
    second = sample_data.generate_sample_prices(n_days=50, seed=2)

    assert not first.equals(second)


def test_log_return_volatility_matches_input(sample_data):
    # GBM log returns have annual volatility sigma; with a long sample and a
    # fixed seed the estimate must be close to the input value.
    prices = sample_data.generate_sample_prices(n_days=5000, seed=42)
    log_returns = np.log(prices).diff().dropna()
    annual_vol = log_returns.std(ddof=1) * np.sqrt(sample_data.TRADING_DAYS)

    np.testing.assert_allclose(annual_vol.to_numpy(), sample_data.ANNUAL_VOL, rtol=0.1)


def test_too_few_days_raises(sample_data):
    with pytest.raises(ValueError, match="at least 2"):
        sample_data.generate_sample_prices(n_days=1)


def test_write_prices_csv_round_trip(sample_data, tmp_path):
    prices = sample_data.generate_sample_prices(n_days=20)
    destination = tmp_path / "nested" / "prices.csv"

    sample_data.write_prices_csv(prices, destination)
    loaded = pd.read_csv(destination, index_col="Date", parse_dates=True)

    assert destination.exists()
    assert loaded.shape == prices.shape
    assert list(loaded.columns) == list(sample_data.TICKERS)
    np.testing.assert_allclose(loaded.to_numpy(), prices.round(4).to_numpy())


def test_main_writes_file_and_returns_zero(sample_data, tmp_path, capsys):
    output = tmp_path / "sample.csv"

    exit_code = sample_data.main(
        ["--output", str(output), "--days", "30", "--seed", "3"]
    )

    assert exit_code == 0
    assert output.exists()
    assert "30 rows" in capsys.readouterr().out
