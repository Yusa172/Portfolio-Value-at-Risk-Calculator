"""Generate reproducible synthetic daily prices for the sample portfolio.

Each asset follows a geometric Brownian motion (GBM) with correlated shocks:

    S_{t+1} = S_t * exp((mu - sigma**2 / 2) * dt + sigma * sqrt(dt) * Z_t)

where ``mu`` is the annual drift, ``sigma`` the annual volatility, ``dt = 1/252``
a trading day, and ``Z_t`` a vector of standard normals with correlation matrix
``rho``. The correlated shocks are obtained from the Cholesky factor ``L`` of
``rho`` (``Z = eps @ L.T`` with ``eps`` independent standard normals).

A fixed seed makes the output identical on every run, so the examples and the
tests never depend on real market data or on the network.

Usage (from the repository root)::

    .venv/Scripts/python scripts/make_sample_data.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

TICKERS: tuple[str, ...] = ("ALFA", "BETA", "GAMA", "DELTA")
ANNUAL_DRIFT = np.array([0.06, 0.04, 0.08, 0.03])
ANNUAL_VOL = np.array([0.20, 0.15, 0.30, 0.12])
CORRELATION = np.array(
    [
        [1.00, 0.30, 0.50, 0.10],
        [0.30, 1.00, 0.20, 0.40],
        [0.50, 0.20, 1.00, 0.05],
        [0.10, 0.40, 0.05, 1.00],
    ]
)
START_PRICE = 100.0
START_DATE = "2020-01-01"
TRADING_DAYS = 252
DEFAULT_DAYS = 750
DEFAULT_SEED = 42
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "sample_prices.csv"


def generate_sample_prices(
    n_days: int = DEFAULT_DAYS,
    seed: int = DEFAULT_SEED,
    start: str = START_DATE,
) -> pd.DataFrame:
    """Simulate correlated GBM prices for the sample assets.

    Parameters
    ----------
    n_days : int
        Number of business days, including the first one. Must be at least 2.
    seed : int
        Seed for the random number generator.
    start : str
        First date of the series, in any format accepted by ``pandas``.

    Returns
    -------
    pandas.DataFrame
        Prices indexed by business day (name ``Date``), one column per ticker.
        The first row equals ``START_PRICE`` for every asset.

    Raises
    ------
    ValueError
        If ``n_days`` is smaller than 2.
    """
    if n_days < 2:
        raise ValueError("n_days must be at least 2")

    rng = np.random.default_rng(seed)
    dt = 1.0 / TRADING_DAYS
    cholesky = np.linalg.cholesky(CORRELATION)

    independent = rng.standard_normal((n_days - 1, len(TICKERS)))
    correlated = independent @ cholesky.T

    drift = (ANNUAL_DRIFT - 0.5 * ANNUAL_VOL**2) * dt
    diffusion = ANNUAL_VOL * np.sqrt(dt) * correlated
    log_returns = np.vstack([np.zeros(len(TICKERS)), drift + diffusion])

    prices = START_PRICE * np.exp(np.cumsum(log_returns, axis=0))
    index = pd.bdate_range(start=start, periods=n_days, name="Date")
    return pd.DataFrame(prices, index=index, columns=list(TICKERS))


def write_prices_csv(prices: pd.DataFrame, path: Path) -> None:
    """Write prices to a CSV file in wide format, rounded to four decimals.

    Parameters
    ----------
    prices : pandas.DataFrame
        Prices indexed by date, one column per ticker.
    path : pathlib.Path
        Destination file. Parent directories are created when missing.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    prices.round(4).to_csv(path, date_format="%Y-%m-%d")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command-line arguments of the script.

    Parameters
    ----------
    argv : list of str, optional
        Arguments to parse. Defaults to ``sys.argv[1:]``.

    Returns
    -------
    argparse.Namespace
        Parsed options: ``output``, ``days`` and ``seed``.
    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="CSV file to write (default: data/sample_prices.csv)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=f"number of business days (default: {DEFAULT_DAYS})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"random seed (default: {DEFAULT_SEED})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Generate the sample prices and write them to disk.

    Parameters
    ----------
    argv : list of str, optional
        Command-line arguments. Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Process exit code (``0`` on success).
    """
    args = parse_args(argv)
    prices = generate_sample_prices(n_days=args.days, seed=args.seed)
    write_prices_csv(prices, args.output)
    print(f"Wrote {len(prices)} rows x {len(TICKERS)} assets to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
