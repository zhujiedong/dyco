from pathlib import Path
from typing import List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd

from .models import LagSearchResult, PipelineResult


class MatplotlibReporter:
    """Generate diagnostic plots (covariances, histograms, time-series, summary)."""

    def plot_covariances(self, results: List[LagSearchResult], outdir: Path) -> None:
        fig = plt.figure(figsize=(16, 12))
        gs = gridspec.GridSpec(3, 1, hspace=0.2)
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[1, 0], sharex=ax1)
        ax3 = fig.add_subplot(gs[2, 0], sharex=ax1)

        collection = []
        for res in results:
            if res.cov_data is None or res.cov_data.empty:
                continue
            df = res.cov_data
            collection.append(df)
            ax1.plot(df["shift"], df["cov"], alpha=0.05, c="black", lw=0.5)
            ax2.plot(df["shift"], df["cov_abs"], alpha=0.05, c="black", lw=0.5)
            norm = df["cov_abs"] / df["cov_abs"].max()
            ax3.plot(df["shift"], norm, alpha=0.05, c="black", lw=0.5)

        if collection:
            all_df = pd.concat(collection, ignore_index=True)
            numeric = all_df.select_dtypes(include=["number"])
            grouped = numeric.groupby("shift").agg(
                median=("cov", "median"),
                q25=("cov", lambda x: x.quantile(0.25)),
                q75=("cov", lambda x: x.quantile(0.75)),
                median_abs=("cov_abs", "median"),
            )

            ax1.plot(grouped.index, grouped["median"], label="median", c="#f44336", lw=1.5)
            ax2.plot(grouped.index, grouped["median_abs"], label="median", c="#f44336", lw=1.5)

        ax1.set_title("Covariances")
        ax2.set_title("Absolute covariances")
        ax3.set_title("Normalized absolute covariances")
        ax1.legend()
        for ax in (ax1, ax2, ax3):
            ax.grid(True, alpha=0.3)

        outpath = outdir / "1_covariance_collection_all_segments.png"
        fig.savefig(outpath, dpi=150, bbox_inches="tight", facecolor="w")
        plt.close(fig)

    def plot_histogram(
        self, results: List[LagSearchResult], iteration: int, outdir: Path
    ) -> None:
        shifts = [
            r.peak_covabsmax_shift
            for r in results
            if r.peak_covabsmax_shift is not None
        ]
        if not shifts:
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        counts, bins, patches = ax.hist(
            shifts, bins=30, color="#78909c", edgecolor="white"
        )
        ax.set_xlabel("lag [records]")
        ax.set_ylabel("counts")
        ax.set_title(f"Histogram of found lag times in iteration {iteration}")

        outpath = outdir / f"{iteration}_HISTOGRAM_segment_lag_times.png"
        fig.savefig(outpath, dpi=150, bbox_inches="tight")
        plt.close(fig)

    def plot_timeseries(self, results: List[LagSearchResult], outdir: Path) -> None:
        df = pd.DataFrame(
            [
                {
                    "start": r.file_date,
                    "shift": r.peak_covabsmax_shift,
                    "iteration": r.iteration,
                }
                for r in results
            ]
        )

        fig, ax = plt.subplots(figsize=(16, 9))
        for it, group in df.groupby("iteration"):
            ax.plot(
                group["start"], group["shift"], "o", alpha=0.6, label=f"iter {it}"
            )

        ax.axhline(0, color="black", ls="-", lw=1)
        ax.set_xlabel("segment date")
        ax.set_ylabel("lag [records]")
        ax.set_title("Found time lags across all iterations")
        ax.legend(loc="upper right")

        locator = mdates.AutoDateLocator(minticks=5, maxticks=20)
        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

        outpath = outdir / "TIMESERIES_segment_lag_times_FINAL.png"
        fig.savefig(outpath, dpi=150, bbox_inches="tight")
        plt.close(fig)

    def plot_summary(self, result: PipelineResult, outdir: Path) -> None:
        outdir.mkdir(parents=True, exist_ok=True)
        lut = result.analysis.daily_lut
        if lut.empty:
            return

        fig, ax = plt.subplots(figsize=(16, 9))
        ax.plot(lut.index, lut["median"], label="median lag", marker="o")
        ax.axhline(
            result.analysis.daily_lut["target_lag"].iloc[0],
            color="black",
            ls="--",
            label="target lag",
        )
        ax.plot(lut.index, lut["correction"], label="correction", marker="s", color="green")

        ax.set_xlabel("date")
        ax.set_ylabel("lag [records]")
        ax.set_title("DYCO Summary: Daily Lag Correction LUT")
        ax.legend()

        outpath = outdir / "summary_lut.png"
        fig.savefig(outpath, dpi=150, bbox_inches="tight")
        plt.close(fig)
