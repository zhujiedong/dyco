from typing import Protocol, runtime_checkable, List
from pathlib import Path
import pandas as pd

from .types import FileMetadata, Segment, LagSearchResult, AnalysisResult, PipelineResult


@runtime_checkable
class FileDiscovery(Protocol):
    """Discover input files from a directory matching a glob pattern."""
    def discover(self, directory: Path, pattern: str) -> List[FileMetadata]: ...


@runtime_checkable
class DataReader(Protocol):
    """Read a file into a pandas DataFrame."""
    def read(self, metadata: FileMetadata) -> pd.DataFrame: ...


@runtime_checkable
class Segmenter(Protocol):
    """Split a DataFrame into time-based segments."""
    def split(self, df: pd.DataFrame, metadata: FileMetadata) -> List[Segment]: ...


@runtime_checkable
class LagSearcher(Protocol):
    """Search for the time lag between reference and lagged variables."""
    def search(self, segment: Segment, window: tuple[int, int]) -> LagSearchResult: ...


@runtime_checkable
class WindowAdjuster(Protocol):
    """Adjust the search window between iterations."""
    def adjust(
        self,
        results: List[LagSearchResult],
        remove_fringe: bool,
        perc_threshold: float,
    ) -> tuple[int, int]: ...


@runtime_checkable
class LagAnalyzer(Protocol):
    """Analyse collected lag results and produce a daily LUT."""
    def analyze(self, results: List[LagSearchResult], target_lag: int) -> AnalysisResult: ...


@runtime_checkable
class LagCorrector(Protocol):
    """Apply a shift correction to target columns."""
    def correct(
        self,
        metadata: FileMetadata,
        df: pd.DataFrame,
        shift: int,
        target_cols: List[str],
    ) -> pd.DataFrame: ...


@runtime_checkable
class Reporter(Protocol):
    """Generate diagnostic plots for pipeline results."""
    def plot_covariances(self, results: List[LagSearchResult], outdir: Path) -> None: ...
    def plot_histogram(self, results: List[LagSearchResult], iteration: int, outdir: Path) -> None: ...
    def plot_timeseries(self, results: List[LagSearchResult], outdir: Path) -> None: ...
    def plot_summary(self, result: PipelineResult, outdir: Path) -> None: ...
