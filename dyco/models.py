from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import pandas as pd


@dataclass(frozen=True)
class FileMetadata:
    """Immutable metadata for a single input data file."""
    path: Path
    start_time: datetime
    expected_end: datetime
    expected_duration_sec: float
    expected_records: int
    found_records: Optional[int] = None
    true_resolution: Optional[float] = None
    is_available: bool = True


@dataclass
class Segment:
    """A contiguous time slice of data from a single file."""
    name: str
    file_date: datetime
    start: datetime
    end: datetime
    data: pd.DataFrame
    iteration: int = 1


@dataclass
class LagSearchResult:
    """Result of a lag search on a single segment, including peak diagnostics."""
    segment_name: str
    file_date: datetime
    iteration: int
    search_window: tuple[int, int]
    step_size: int

    peak_covabsmax_shift: Optional[int] = None
    peak_covabsmax_cov: Optional[float] = None
    peak_covabsmax_timestamp: Optional[datetime] = None

    peak_auto_shift: Optional[int] = None
    default_lag_shift: Optional[int] = None

    numvals_reference: int = 0
    numvals_lagged: int = 0

    cov_data: Optional[pd.DataFrame] = field(default=None, repr=False)


@dataclass
class AnalysisResult:
    """Daily look-up table (LUT) and high-quality peak series."""
    daily_lut: pd.DataFrame
    instantaneous_lut: Optional[pd.DataFrame] = None
    high_quality_peaks: pd.Series = field(default_factory=pd.Series, repr=False)


@dataclass
class PipelineResult:
    """Complete output of one pipeline run."""
    lag_results: List[LagSearchResult]
    analysis: AnalysisResult
    corrected_files: List[Path]
    output_dir: Path
