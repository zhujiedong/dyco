from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import List, Optional

import pandas as pd

from .config import DycoConfig
from .types import FileMetadata, LagSearchResult, PipelineResult
from .protocols import (
    FileDiscovery,
    DataReader,
    Segmenter,
    LagSearcher,
    WindowAdjuster,
    LagAnalyzer,
    LagCorrector,
    Reporter,
)


class DycoPipeline:
    """Orchestrates the multi-iteration lag-detection and correction process.

    Assembles file discovery, data reading, segmentation, lag search,
    window adjustment, analysis, correction, and reporting.
    """

    def __init__(
        self,
        config: DycoConfig,
        discovery: FileDiscovery,
        reader: DataReader,
        segmenter: Segmenter,
        searcher: LagSearcher,
        window_adjuster: WindowAdjuster,
        analyzer: LagAnalyzer,
        corrector: LagCorrector,
        reporter: Optional[Reporter] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.cfg = config
        self.discovery = discovery
        self.reader = reader
        self.segmenter = segmenter
        self.searcher = searcher
        self.window_adjuster = window_adjuster
        self.analyzer = analyzer
        self.corrector = corrector
        self.reporter = reporter
        self.logger = logger or logging.getLogger("dyco")
        self._prepare_output()

    def _prepare_output(self):
        subdirs = [
            "0_log",
            "1_overview",
            "2_covariances",
            "3_covariances_plots",
            "4_time_lags_overview",
            "5_time_lags_histograms",
            "6_time_lags_timeseries",
            "7_lookup_table",
            "8_corrected_files",
        ]
        for name in subdirs:
            p = self.cfg.outdir / name
            if p.exists() and self.cfg.del_previous_results and name != "0_log":
                shutil.rmtree(p)
            p.mkdir(parents=True, exist_ok=True)

    def run(self) -> PipelineResult:
        self.logger.info("=" * 60)
        self.logger.info("DYCO Pipeline Started")
        self.logger.info("=" * 60)

        files = self.discovery.discover(self.cfg.indir, self.cfg.filename_pattern)
        if self.cfg.files_how_many:
            files = files[: self.cfg.files_how_many]
        self.logger.info(f"Discovered {len(files)} files matching pattern")

        all_results: List[LagSearchResult] = []
        window = self.cfg.lag_winsize

        for iteration in range(1, self.cfg.lag_n_iter + 1):
            self.logger.info(
                f"--- Iteration {iteration}/{self.cfg.lag_n_iter} | window={window} ---"
            )
            iter_results = self._detect_lags(files, window, iteration)
            all_results.extend(iter_results)

            # 保存本次迭代的 segment lag times
            self._save_segment_lagtimes(iter_results, iteration)

            if iteration < self.cfg.lag_n_iter:
                window = self.window_adjuster.adjust(
                    iter_results,
                    remove_fringe=self.cfg.lag_hist_remove_fringe_bins,
                    perc_threshold=self.cfg.lag_hist_perc_thres,
                )
                self.logger.info(f"Adjusted window for next iteration: {window}")

            if self.reporter:
                self.reporter.plot_histogram(
                    iter_results,
                    iteration,
                    self.cfg.outdir / "5_time_lags_histograms",
                )

        analysis = self.analyzer.analyze(all_results, target_lag=self.cfg.target_lag)
        lut_path = self.cfg.outdir / "7_lookup_table" / "LUT_default_agg_time_lags.csv"
        analysis.daily_lut.to_csv(lut_path)
        self.logger.info(f"LUT saved to {lut_path}")

        corrected = self._correct_files(files, analysis)

        if self.reporter:
            self.reporter.plot_covariances(
                all_results, self.cfg.outdir / "3_covariances_plots"
            )
            self.reporter.plot_timeseries(
                all_results, self.cfg.outdir / "6_time_lags_timeseries"
            )
            self.reporter.plot_summary(
                PipelineResult(all_results, analysis, corrected, self.cfg.outdir),
                self.cfg.outdir / "SUMMARY",
            )

        self.logger.info("DYCO Pipeline Finished")
        return PipelineResult(all_results, analysis, corrected, self.cfg.outdir)

    def _save_segment_lagtimes(self, results: List[LagSearchResult], iteration: int):
        """Convert results to DataFrame and save to CSV (兼容原 analyze.py 的列名)."""
        records = []
        for r in results:
            records.append({
                "file_date": r.file_date,
                "start": r.file_date,  # 简化：用 file_date 作为 start
                "end": r.file_date,
                "iteration": r.iteration,
                "PEAK-COVABSMAX_SHIFT": r.peak_covabsmax_shift,
                "PEAK-COVABSMAX_COV": r.peak_covabsmax_cov,
                "PEAK-AUTO_SHIFT": r.peak_auto_shift,
                "lagsearch_start": r.search_window[0],
                "lagsearch_end": r.search_window[1],
            })
        df = pd.DataFrame(records)
        outdir = self.cfg.outdir / "4_time_lags_overview"
        outdir.mkdir(parents=True, exist_ok=True)

        # 追加模式保存所有迭代
        filepath = outdir / "segments_found_lag_times.csv"
        if filepath.exists():
            existing = pd.read_csv(filepath, index_col=0)
            df = pd.concat([existing, df], ignore_index=True)
        df.to_csv(filepath, index_label="row_id")

        # 同时保存本次迭代的单独文件
        iter_file = outdir / f"{iteration}_segments_found_lag_times_after_iteration-{iteration}.csv"
        df_iter = df[df["iteration"] == iteration].copy()
        df_iter.to_csv(iter_file)

    def _detect_lags(
        self, files: List[FileMetadata], window: tuple[int, int], iteration: int
    ) -> List[LagSearchResult]:
        results: List[LagSearchResult] = []
        for fm in files:
            if not fm.is_available:
                continue
            df = self.reader.read(fm)
            segments = self.segmenter.split(df, fm)
            for seg in segments:
                seg.iteration = iteration
                res = self.searcher.search(seg, window)

                if res.cov_data is not None:
                    cov_dir = self.cfg.outdir / "2_covariances"
                    cov_dir.mkdir(parents=True, exist_ok=True)
                    cov_path = (
                        cov_dir
                        / f"{seg.name}_covariance_iteration-{iteration}.csv"
                    )
                    res.cov_data.to_csv(cov_path)

                results.append(res)
        return results

    def _correct_files(
        self, files: List[FileMetadata], analysis
    ) -> List[Path]:
        corrected_paths: List[Path] = []
        lut = analysis.daily_lut
        outdir = self.cfg.outdir / "8_corrected_files"

        for fm in files:
            if not fm.is_available:
                continue

            date_key = pd.Timestamp(fm.start_time.date())
            shift = 0
            if date_key in lut.index and "correction" in lut.columns:
                val = lut.loc[date_key, "correction"]
                if pd.notna(val):
                    shift = int(val)

            df = self.reader.read(fm)
            df_corrected = self.corrector.correct(
                fm, df, shift, self.cfg.var_target
            )

            outpath = outdir / f"{fm.path.stem}_DYCO.csv"
            df_corrected.to_csv(outpath, index=False)
            corrected_paths.append(outpath)
            self.logger.debug(
                f"Corrected {fm.path.name} -> shift={shift}"
            )

        return corrected_paths
