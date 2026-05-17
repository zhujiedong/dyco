from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Union


@dataclass
class DycoConfig:
    """Central configuration for the DYCO pipeline.

    Parameters can be passed positionally or as keyword arguments to
    :class:`Dyco`.
    """
    var_reference: str
    var_lagged: str
    var_target: List[str]

    indir: Path
    outdir: Path

    filename_date_format: str = "%Y%m%d%H%M%S"
    filename_pattern: str = "*.csv"
    file_duration: str = "30min"
    files_how_many: Optional[int] = None

    data_timestamp_format: Optional[str] = "%Y-%m-%d %H:%M:%S.%f"
    data_nominal_timeres: float = 0.05

    lag_segment_dur: str = "10min"
    lag_winsize: tuple[int, int] = field(default_factory=lambda: (-1000, 1000))
    lag_n_iter: int = 3
    lag_shift_stepsize: Optional[int] = None
    lag_hist_remove_fringe_bins: bool = True
    lag_hist_perc_thres: float = 0.9

    target_lag: int = 0

    del_previous_results: bool = False

    outlier_thres_zscore: float = 1.4
    outlier_winsize: Optional[int] = None

    def __post_init__(self):
        if isinstance(self.indir, str):
            self.indir = Path(self.indir)
        if isinstance(self.outdir, str):
            self.outdir = Path(self.outdir)

        if isinstance(self.lag_winsize, int):
            w = abs(self.lag_winsize)
            self.lag_winsize = (-w, w)

        if self.lag_hist_perc_thres > 1.0:
            self.lag_hist_perc_thres = 1.0
        elif self.lag_hist_perc_thres < 0.1:
            self.lag_hist_perc_thres = 0.1
