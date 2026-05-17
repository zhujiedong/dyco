from __future__ import annotations

from pathlib import Path
from typing import List

from .config import DycoConfig
from .pipeline import DycoPipeline
from .models import PipelineResult

from .discovery import RegexFileDiscovery
from .io import CsvReader
from .segmentation import TimeBasedSegmenter
from .lag.search import MaxCovarianceSearcher
from .lag.window import HistogramWindowAdjuster
from .analysis import AggregateAnalyzer
from .correction import PandasShiftCorrector
from .reporting import MatplotlibReporter
from .utils.logging import create_logger


class Dyco:
    """Public entry point for the DYCO lag-correction pipeline.

    All configuration options listed in :class:`DycoConfig` are accepted as
    keyword arguments.  Call :meth:`run` to execute the full pipeline.
    """

    def __init__(
        self,
        var_reference: str,
        var_lagged: str,
        var_target: List[str],
        indir: str | Path,
        outdir: str | Path,
        **kwargs,
    ):
        self.config = DycoConfig(
            var_reference=var_reference,
            var_lagged=var_lagged,
            var_target=var_target,
            indir=indir,
            outdir=outdir,
            **kwargs,
        )
        self._pipeline = self._build_pipeline()

    def _build_pipeline(self) -> DycoPipeline:
        cfg = self.config
        logfile_path = cfg.outdir / "0_log" / "run.log"
        logger = create_logger("dyco", logfile_path)

        return DycoPipeline(
            config=cfg,
            discovery=RegexFileDiscovery(
                filename_date_format=cfg.filename_date_format,
                file_duration=cfg.file_duration,
                nominal_timeres=cfg.data_nominal_timeres,
            ),
            reader=CsvReader(
                timestamp_format=cfg.data_timestamp_format,
                nominal_timeres=cfg.data_nominal_timeres,
            ),
            segmenter=TimeBasedSegmenter(segment_dur=cfg.lag_segment_dur),
            searcher=MaxCovarianceSearcher(
                var_reference=cfg.var_reference,
                var_lagged=cfg.var_lagged,
                step_size=cfg.lag_shift_stepsize,
            ),
            window_adjuster=HistogramWindowAdjuster(),
            analyzer=AggregateAnalyzer(
                outlier_thres=cfg.outlier_thres_zscore,
                outlier_winsize=cfg.outlier_winsize,
            ),
            corrector=PandasShiftCorrector(),
            reporter=MatplotlibReporter(),
            logger=logger,
        )

    def run(self) -> PipelineResult:
        return self._pipeline.run()
