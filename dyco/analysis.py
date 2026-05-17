from typing import List, Optional

import numpy as np
import pandas as pd

from .types import LagSearchResult, AnalysisResult


class AggregateAnalyzer:
    """Aggregate lag-search results into a daily look-up table (LUT)
    with outlier removal and correction values.
    """

    def __init__(
        self, outlier_thres: float = 1.4, outlier_winsize: Optional[int] = None
    ):
        self.outlier_thres = outlier_thres
        self.outlier_winsize = outlier_winsize

    def analyze(self, results: List[LagSearchResult], target_lag: int) -> AnalysisResult:
        df = pd.DataFrame(
            [
                {
                    "start": r.file_date,
                    "shift": r.peak_covabsmax_shift,
                    "auto_shift": r.peak_auto_shift,
                    "iteration": r.iteration,
                }
                for r in results
            ]
        )

        last_iter = df["iteration"].max()
        last_df = df[df["iteration"] == last_iter].copy()
        last_df.set_index("start", inplace=True)
        last_df.index = pd.to_datetime(last_df.index)

        # High-quality peaks: covabsmax agrees with auto-detected peak
        hq = last_df[last_df["shift"] == last_df["auto_shift"]]["shift"].dropna()
        hq_clean = self._remove_outliers(hq)

        if hq_clean.empty:
            empty_lut = pd.DataFrame(
                columns=["median", "counts", "target_lag", "correction"]
            )
            return AnalysisResult(daily_lut=empty_lut, high_quality_peaks=hq_clean)

        daily = self._aggregate_daily(hq_clean)

        # 如果只有一天数据，直接为该天生成一个条目
        if daily.empty and not hq_clean.empty:
            date = pd.Timestamp(hq_clean.index[0].date())
            daily = pd.DataFrame(
                [{"date": date, "median": hq_clean.median(), "counts": len(hq_clean)}]
            ).set_index("date")

        full_range = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
        daily = daily.reindex(full_range)

        n_missing = daily["median"].isnull().sum()
        if n_missing > 0:
            daily["median"] = daily["median"].fillna(
                daily["median"]
                .rolling(window=5, min_periods=1, center=True)
                .median()
            )

        daily["target_lag"] = target_lag
        daily["correction"] = -1 * (daily["target_lag"] - daily["median"])
        daily["correction"] = daily["correction"].ffill(limit=1).bfill(limit=1)

        return AnalysisResult(daily_lut=daily, high_quality_peaks=hq_clean)

    def _remove_outliers(self, series: pd.Series) -> pd.Series:
        if len(series) < 3:
            return series

        # 如果所有值相同，无需去异常
        if series.nunique() <= 1:
            return series

        winsize = self.outlier_winsize or max(10, int(len(series) / 70))
        winsize = min(winsize, len(series))
        rolling_mean = series.rolling(window=winsize, center=True, min_periods=1).mean()
        rolling_std = (
            series.rolling(window=winsize, center=True, min_periods=1).std().replace(0, np.nan)
        )
        z = (series - rolling_mean) / rolling_std
        # 只保留 z-score 有效且不超过阈值的
        valid = z.notna() & (z.abs() <= self.outlier_thres)
        return series[valid]

    def _aggregate_daily(self, series: pd.Series) -> pd.DataFrame:
        records = []
        unique_dates = np.unique(series.index.date)
        for date in unique_dates:
            dt_date = pd.Timestamp(date)
            # 放宽条件：包含前后2天的数据（包括当天）
            from_date = dt_date - pd.Timedelta("2D")
            to_date = dt_date + pd.Timedelta("2D")
            subset = series[
                (series.index >= from_date) & (series.index <= to_date)
            ]
            if len(subset) >= 1:  # 降低阈值，至少1个即可
                records.append(
                    {"date": dt_date, "median": subset.median(), "counts": len(subset)}
                )
            else:
                records.append(
                    {"date": dt_date, "median": np.nan, "counts": len(subset)}
                )
        return pd.DataFrame(records).set_index("date")
