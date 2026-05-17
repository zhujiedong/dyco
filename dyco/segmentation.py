from typing import List

import pandas as pd

from .types import FileMetadata, Segment


class TimeBasedSegmenter:
    """Split a DatetimeIndex-ed DataFrame into fixed-duration segments."""

    def __init__(self, segment_dur: str):
        self.segment_dur = segment_dur

    def split(self, df: pd.DataFrame, metadata: FileMetadata) -> List[Segment]:
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame index must be DatetimeIndex")

        segments: List[Segment] = []
        counter = 0
        for _, group in df.groupby(pd.Grouper(freq=self.segment_dur)):
            if len(group) == 0:
                continue
            counter += 1
            name = f"{group.index[0].strftime('%Y%m%d%H%M%S')}_segment{counter}"
            segments.append(
                Segment(
                    name=name,
                    file_date=metadata.start_time,
                    start=group.index[0],
                    end=group.index[-1],
                    data=group.copy(),
                )
            )
        return segments
