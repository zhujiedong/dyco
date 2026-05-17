from typing import Optional, Tuple

import pandas as pd
import numpy as np
from scipy.signal import find_peaks

from ..types import Segment, LagSearchResult
from ..protocols import LagSearcher


class MaxCovariance:
    """Compute cross-covariance between two variables over a range of shifts."""

    def __init__(
        self,
        df: pd.DataFrame,
        var_reference: str,
        var_lagged: str,
        lgs_winsize_from: int,
        lgs_winsize_to: int,
        shift_stepsize: int,
        segment_name: str,
    ):
        self.df = df
        self.var_reference = var_reference
        self.var_lagged = var_lagged
        self.winsize_from = lgs_winsize_from
        self.winsize_to = lgs_winsize_to
        self.stepsize = shift_stepsize
        self.segment_name = segment_name
        self.cov_df: Optional[pd.DataFrame] = None
        self.props_peak_auto: Optional[dict] = None

    def run(self):
        ref = self.df[self.var_reference].values
        lag = self.df[self.var_lagged].values

        shifts = range(self.winsize_from, self.winsize_to + 1, self.stepsize)
        records = []

        for shift in shifts:
            if shift == 0:
                r, l = ref, lag
            elif shift > 0:
                r = ref[shift:]
                l = lag[:-shift]
            else:
                r = ref[:shift]
                l = lag[-shift:]

            mask = ~(np.isnan(r) | np.isnan(l))
            n_valid = mask.sum()

            if n_valid < 2:
                cov = np.nan
            else:
                rc = r[mask]
                lc = l[mask]
                cov = np.mean((rc - rc.mean()) * (lc - lc.mean()))

            records.append(
                {
                    "shift": shift,
                    "cov": cov,
                    "cov_abs": abs(cov) if not np.isnan(cov) else np.nan,
                    "index": self.df.index[len(self.df) // 2],
                }
            )

        self.cov_df = pd.DataFrame(records)
        self._flag_peaks()

    def _flag_peaks(self):
        df = self.cov_df

        idx_max = df["cov_abs"].idxmax()
        df["flag_peak_max_cov_abs"] = False
        df.loc[idx_max, "flag_peak_max_cov_abs"] = True

        df["flag_peak_auto"] = False
        peaks, props = find_peaks(df["cov_abs"].fillna(0), prominence=0)
        if len(peaks) > 0:
            most_prom = peaks[np.argmax(props["prominences"])]
            df.loc[most_prom, "flag_peak_auto"] = True
            self.props_peak_auto = dict(peaks=peaks, props=props)
        else:
            df.loc[idx_max, "flag_peak_auto"] = True
            self.props_peak_auto = {}

        df["flag_instantaneous_default_lag"] = df["shift"] == 0

    def get(self) -> Tuple[pd.DataFrame, dict]:
        if self.cov_df is None:
            raise RuntimeError("Must call run() first")
        return self.cov_df, self.props_peak_auto

class MaxCovarianceSearcher:
    """Lag searcher that picks the shift with maximum absolute covariance."""

    def __init__(
        self,
        var_reference: str,
        var_lagged: str,
        step_size: Optional[int] = None,
    ):
        self.var_reference = var_reference
        self.var_lagged = var_lagged
        self.step_size = step_size

    def search(self, segment: Segment, window: Tuple[int, int]) -> LagSearchResult:
        range_size = abs(window[1] - window[0])
        stepsize = self.step_size or max(1, range_size // 200)

        mc = MaxCovariance(
            df=segment.data,
            var_reference=self.var_reference,
            var_lagged=self.var_lagged,
            lgs_winsize_from=window[0],
            lgs_winsize_to=window[1],
            shift_stepsize=stepsize,
            segment_name=segment.name,
        )
        mc.run()
        cov_df, _ = mc.get()

        def get_peak(flag_col: str):
            row = cov_df[cov_df[flag_col]]
            if row.empty:
                return None, None, None
            r = row.iloc[0]
            return int(r["shift"]), float(r["cov"]), r["index"]

        peak_shift, peak_cov, peak_ts = get_peak("flag_peak_max_cov_abs")
        auto_shift, _, _ = get_peak("flag_peak_auto")
        default_shift, _, _ = get_peak("flag_instantaneous_default_lag")

        return LagSearchResult(
            segment_name=segment.name,
            file_date=segment.file_date,
            iteration=segment.iteration,
            search_window=window,
            step_size=stepsize,
            peak_covabsmax_shift=peak_shift,
            peak_covabsmax_cov=peak_cov,
            peak_covabsmax_timestamp=peak_ts,
            peak_auto_shift=auto_shift,
            default_lag_shift=default_shift,
            numvals_reference=segment.data[self.var_reference].dropna().size,
            numvals_lagged=segment.data[self.var_lagged].dropna().size,
            cov_data=cov_df,
        )
