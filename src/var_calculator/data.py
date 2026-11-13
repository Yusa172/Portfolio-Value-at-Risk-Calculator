"""Load asset prices into a tidy, date-indexed table.

Every loader in this module returns prices in the same *wide* layout: one row
per date (a sorted ``DatetimeIndex`` named ``Date``) and one ``float`` column
per asset. Missing observations are kept as ``NaN`` by the loaders;
:func:`clean_prices` turns such a table into one that is ready for computing
returns.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

__all__ = ["PriceDataWarning", "clean_prices", "load_prices_csv"]

INDEX_NAME = "Date"


class PriceDataWarning(UserWarning):
    """Warning issued when price data looks wrong but can still be used."""


def load_prices_csv(
    path: str | Path,
    *,
    date_column: str = "Date",
    ticker_column: str = "Ticker",
    price_column: str = "Price",
) -> pd.DataFrame:
    """Read asset prices from a CSV file in wide or long format.

    Two layouts are accepted and detected from the header:

    * **wide** -- a date column followed by one price column per asset::

          Date,ALFA,BETA
          2020-01-01,100.0,100.0
          2020-01-02,100.4,99.2

    * **long** -- one row per (date, asset) pair, with a date column, a ticker
      column and a price column; any other column is ignored::

          Date,Ticker,Price
          2020-01-01,ALFA,100.0
          2020-01-01,BETA,100.0

    A file is read as long when it has a ``ticker_column``; otherwise it is
    read as wide. Column names are matched ignoring case and surrounding
    whitespace.

    Parameters
    ----------
    path : str or pathlib.Path
        CSV file to read.
    date_column : str
        Name of the column holding the dates.
    ticker_column : str
        Name of the column holding the asset identifiers (long format only).
    price_column : str
        Name of the column holding the prices (long format only).

    Returns
    -------
    pandas.DataFrame
        Prices indexed by date (``DatetimeIndex`` named ``Date``, sorted in
        ascending order), one ``float`` column per asset. In wide format the
        columns keep the order of the file; in long format they follow the
        order in which each ticker first appears.

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    ValueError
        If a required column is missing, there are no price columns or no
        rows, a column name is repeated, a date cannot be parsed, a price is
        not numeric, or a date (wide) or a (date, ticker) pair (long) appears
        more than once.
    """
    raw = pd.read_csv(Path(path), dtype=str, skipinitialspace=True)
    raw.columns = [str(column).strip() for column in raw.columns]
    _check_unique_columns(raw.columns)

    date_name = _find_column(raw.columns, date_column, required=True)
    ticker_name = _find_column(raw.columns, ticker_column, required=False)
    if raw.empty:
        raise ValueError("the file has no price rows")

    if ticker_name is None:
        prices = _from_wide(raw, date_name)
    else:
        price_name = _find_column(raw.columns, price_column, required=True)
        prices = _from_long(raw, date_name, ticker_name, price_name)

    prices.index.name = INDEX_NAME
    prices.columns.name = None
    return prices.sort_index()


def _check_unique_columns(columns: pd.Index) -> None:
    """Raise ``ValueError`` when two columns share a name, ignoring case."""
    seen: set[str] = set()
    for column in columns:
        key = column.casefold()
        # pandas renames exact duplicates to "name.1", "name.2", ...
        base, _, suffix = column.rpartition(".")
        if key in seen or (base and suffix.isdigit() and base.casefold() in seen):
            raise ValueError(f"duplicate column name: {column!r}")
        seen.add(key)


def _find_column(columns: pd.Index, name: str, *, required: bool) -> str | None:
    """Return the column matching ``name`` ignoring case, or ``None``."""
    target = name.strip().casefold()
    for column in columns:
        if column.casefold() == target:
            return column
    if required:
        raise ValueError(f"missing required column {name!r}; found {list(columns)}")
    return None


def _parse_dates(values: pd.Series) -> pd.DatetimeIndex:
    """Convert a column of strings to dates, rejecting blanks and bad values."""
    if values.isna().any():
        raise ValueError("the date column has empty values")
    try:
        return pd.DatetimeIndex(pd.to_datetime(values.str.strip()))
    except (ValueError, TypeError) as error:
        raise ValueError(f"could not parse the date column: {error}") from error


def _parse_prices(values: pd.Series, label: str) -> pd.Series:
    """Convert a column of strings to floats; blanks become ``NaN``."""
    try:
        return pd.to_numeric(values.str.strip()).astype(float)
    except (ValueError, TypeError) as error:
        raise ValueError(f"non-numeric price in column {label!r}: {error}") from error


def _from_wide(raw: pd.DataFrame, date_name: str) -> pd.DataFrame:
    """Build the price table from a wide-format file."""
    tickers = [column for column in raw.columns if column != date_name]
    if not tickers:
        raise ValueError("the file has no price columns besides the date column")

    index = _parse_dates(raw[date_name])
    if index.has_duplicates:
        repeated = index[index.duplicated()][0].date()
        raise ValueError(f"duplicate date in wide-format file: {repeated}")

    columns = {
        ticker: _parse_prices(raw[ticker], ticker).to_numpy() for ticker in tickers
    }
    return pd.DataFrame(columns, index=index)


def _from_long(
    raw: pd.DataFrame, date_name: str, ticker_name: str, price_name: str
) -> pd.DataFrame:
    """Build the price table from a long-format file."""
    if raw[ticker_name].isna().any():
        raise ValueError(f"the {ticker_name!r} column has empty values")

    tidy = pd.DataFrame(
        {
            "date": _parse_dates(raw[date_name]),
            "ticker": raw[ticker_name].str.strip().to_numpy(),
            "price": _parse_prices(raw[price_name], price_name).to_numpy(),
        }
    )
    repeated = tidy[tidy.duplicated(["date", "ticker"])]
    if not repeated.empty:
        first = repeated.iloc[0]
        raise ValueError(
            f"duplicate (date, ticker) pair in long-format file: "
            f"({first['date'].date()}, {first['ticker']})"
        )

    tickers = list(dict.fromkeys(tidy["ticker"]))
    dates = pd.DatetimeIndex(tidy["date"].unique()).sort_values()
    indexed = tidy.set_index(["date", "ticker"])["price"]
    full = pd.MultiIndex.from_product([dates, tickers])
    table = indexed.reindex(full).to_numpy().reshape(len(dates), len(tickers))
    return pd.DataFrame(table, index=dates, columns=tickers)


def clean_prices(
    prices: pd.DataFrame,
    *,
    max_fill: int = 5,
    drop_incomplete: bool = True,
) -> pd.DataFrame:
    r"""Clean a wide price table so that every asset shares the same dates.

    The steps are applied in this order:

    1. Prices that are not strictly positive (or are infinite) are reported
       with a :class:`PriceDataWarning` and treated as missing. A price
       :math:`P_t \le 0` is not a valid quote and makes the log return
       :math:`\ln(P_t / P_{t-1})` undefined.
    2. Dates on which no asset has a price (for example a holiday common to
       all markets) are removed.
    3. Gaps are forward-filled with the last known price of the same asset,
       for at most ``max_fill`` consecutive dates. This is the usual treatment
       for assets that trade on different calendars: a stale price implies a
       zero return on the missing day. The limit keeps long gaps (a suspended
       or delisted asset) from being filled with a flat line, which would
       understate volatility. Values before the first observation of an asset
       are never filled, so no future information is used.
    4. If ``drop_incomplete`` is true, dates on which any asset is still
       missing are removed, leaving the common sample of all assets.

    The input is not modified.

    Parameters
    ----------
    prices : pandas.DataFrame
        Prices in wide layout, as returned by :func:`load_prices_csv`: a
        ``DatetimeIndex`` without repeated dates and one numeric column per
        asset.
    max_fill : int
        Maximum number of consecutive missing dates to forward-fill for each
        asset. Use ``0`` to disable forward-filling.
    drop_incomplete : bool
        Whether to drop the dates on which at least one asset has no price
        after forward-filling. If false, those gaps are kept as ``NaN``.

    Returns
    -------
    pandas.DataFrame
        Cleaned prices sorted by date, with ``float`` columns in the original
        order. With ``drop_incomplete=True`` the table has no missing values.

    Raises
    ------
    TypeError
        If ``prices`` is not a DataFrame, its index is not a
        ``DatetimeIndex``, a column is not numeric or ``max_fill`` is not an
        integer.
    ValueError
        If ``max_fill`` is negative, the table has no columns, a date is
        missing or repeated, or no dates are left after cleaning.

    Warns
    -----
    PriceDataWarning
        If any price is non-positive or infinite.
    """
    _check_price_table(prices)
    if isinstance(max_fill, bool) or not isinstance(max_fill, int):
        raise TypeError("max_fill must be an integer")
    if max_fill < 0:
        raise ValueError(f"max_fill must be non-negative, got {max_fill}")

    cleaned = _mask_invalid_prices(prices.astype(float).sort_index())
    cleaned = cleaned.dropna(how="all")
    if max_fill > 0:
        cleaned = cleaned.ffill(limit=max_fill)
    if drop_incomplete:
        cleaned = cleaned.dropna(how="any")
    if cleaned.empty:
        raise ValueError("no dates are left after cleaning the prices")
    return cleaned


def _check_price_table(prices: pd.DataFrame) -> None:
    """Raise if ``prices`` is not a wide, date-indexed, numeric table."""
    if not isinstance(prices, pd.DataFrame):
        raise TypeError("prices must be a pandas DataFrame")
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise TypeError("prices must be indexed by a DatetimeIndex")
    if prices.shape[1] == 0:
        raise ValueError("prices has no asset columns")
    if prices.index.hasnans:
        raise ValueError("the index of prices has missing dates")
    if prices.index.has_duplicates:
        repeated = prices.index[prices.index.duplicated()][0].date()
        raise ValueError(f"duplicate date in prices: {repeated}")
    for column, dtype in prices.dtypes.items():
        is_numeric = pd.api.types.is_numeric_dtype(dtype)
        if not is_numeric or pd.api.types.is_bool_dtype(dtype):
            raise TypeError(f"column {column!r} of prices is not numeric")


def _mask_invalid_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Replace non-positive or infinite prices with ``NaN``, with a warning."""
    invalid = (prices <= 0) | np.isinf(prices)
    counts = invalid.sum()
    counts = counts[counts > 0]
    if counts.empty:
        return prices
    detail = ", ".join(f"{column} ({count})" for column, count in counts.items())
    warnings.warn(
        f"{int(counts.sum())} non-positive or infinite price(s) treated as "
        f"missing: {detail}",
        PriceDataWarning,
        stacklevel=3,
    )
    return prices.mask(invalid)
