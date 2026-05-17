import logging
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd

from .exceptions import NoFilesFoundError
from .types import FileMetadata

_logger = logging.getLogger(__name__)


class RegexFileDiscovery:
    """Discover data files by matching a glob pattern and parsing filenames
    with a ``strptime`` date format.
    """

    def __init__(
        self,
        filename_date_format: str,
        file_duration: str,
        nominal_timeres: float,
    ):
        self.filename_date_format = filename_date_format
        self.file_duration = pd.to_timedelta(file_duration)
        self.nominal_timeres = nominal_timeres

    def discover(self, directory: Path, pattern: str) -> List[FileMetadata]:
        files = sorted(directory.glob(pattern))
        if not files:
            raise NoFilesFoundError(f"No files found with pattern {pattern} in {directory}")

        metas: List[FileMetadata] = []
        for f in files:
            try:
                start = datetime.strptime(f.stem, self.filename_date_format)
            except ValueError:
                _logger.debug("Skipping file %s: name does not match date format %s",
                              f.name, self.filename_date_format)
                continue

            expected_end = start + self.file_duration
            expected_dur_sec = self.file_duration.total_seconds()
            expected_records = int(expected_dur_sec / self.nominal_timeres)

            metas.append(
                FileMetadata(
                    path=f,
                    start_time=start,
                    expected_end=expected_end,
                    expected_duration_sec=expected_dur_sec,
                    expected_records=expected_records,
                )
            )

        return metas
