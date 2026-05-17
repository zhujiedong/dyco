from pathlib import Path
from typing import Optional

import pandas as pd

from .models import FileMetadata


class CsvReader:
    """Read ``.csv`` and ``.parquet`` files into DataFrames with DatetimeIndex.

    When *timestamp_format* is ``None`` a synthetic index is generated from
    the file start time and *nominal_timeres*.
    """

    def __init__(self, timestamp_format: Optional[str], nominal_timeres: float):
        self.timestamp_format = timestamp_format
        self.nominal_timeres = nominal_timeres

    def read(self, metadata: FileMetadata) -> pd.DataFrame:
        suffix = metadata.path.suffix.lower()
        if suffix == ".csv":
            df = self._read_csv(metadata)
        elif suffix == ".parquet":
            df = pd.read_parquet(metadata.path)
            if not isinstance(df.index, pd.DatetimeIndex) and self.timestamp_format:
                df.index = pd.to_datetime(df.index)
        else:
            raise ValueError(f"Unsupported file extension: {suffix}")

        if not isinstance(df.index, pd.DatetimeIndex):
            if self.timestamp_format:
                ts_col = df.columns[0]
                df[ts_col] = pd.to_datetime(df[ts_col], format=self.timestamp_format)
                df = df.set_index(ts_col)
            else:
                idx = pd.date_range(
                    start=metadata.start_time,
                    periods=len(df),
                    freq=pd.Timedelta(seconds=self.nominal_timeres),
                )
                df.index = idx

        return df

    def _read_csv(self, metadata: FileMetadata) -> pd.DataFrame:
        path = metadata.path

        if self.timestamp_format:
            return pd.read_csv(
                path,
                na_values=-9999,
                encoding="utf-8",
                parse_dates=[0],
                date_format=self.timestamp_format,
                index_col=0,
                engine="c",
            )

        return pd.read_csv(
            path,
            na_values=-9999,
            encoding="utf-8",
            engine="c",
        )
