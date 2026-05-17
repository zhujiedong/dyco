from typing import List

import numpy as np

from ..models import LagSearchResult
from .peaks import find_prominent_peak


class HistogramWindowAdjuster:
    """Narrow the lag-search window based on the histogram of detected peaks."""

    def adjust(
        self,
        results: List[LagSearchResult],
        remove_fringe: bool = True,
        perc_threshold: float = 0.9,
    ) -> tuple[int, int]:
        shifts = [
            r.peak_covabsmax_shift
            for r in results
            if r.peak_covabsmax_shift is not None
        ]
        if not shifts:
            return (-1000, 1000)

        counts, divisions = np.histogram(shifts, bins=30)
        if remove_fringe and len(counts) >= 5:
            counts = counts[1:-1]
            divisions = divisions[1:-1]

        peak_idx = find_prominent_peak(counts)
        start_idx, end_idx = self._expand_around_peak(counts, peak_idx, perc_threshold)

        new_win = [int(divisions[start_idx]), int(divisions[end_idx])]

        while (new_win[1] - new_win[0]) < 20:
            new_win[0] -= 1
            new_win[1] += 1

        return tuple(new_win)

    def _expand_around_peak(
        self, counts: np.ndarray, peak_idx: int, thres: float
    ) -> tuple[int, int]:
        start = end = peak_idx
        total = np.sum(counts)
        while np.sum(counts[start : end + 1]) / total < thres:
            if start > 0:
                start -= 1
            if end < len(counts) - 1:
                end += 1
            if start == 0 and end == len(counts) - 1:
                break
        return start, end
