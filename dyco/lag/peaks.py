import numpy as np
from scipy.signal import find_peaks


def find_prominent_peak(series: np.ndarray, max_prominence: int = 40) -> int:
    """Find the single most prominent peak in a series."""
    prom = 0
    peaks = np.array([])
    while len(peaks) != 1 and prom < max_prominence:
        prom += 1
        peaks, _ = find_peaks(series, prominence=prom)
    if len(peaks) == 1:
        return int(peaks[0])
    return int(np.argmax(series))
