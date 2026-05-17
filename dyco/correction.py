from typing import List

import pandas as pd

from .types import FileMetadata


class PandasShiftCorrector:
    """Apply a row-index shift to target columns via :meth:`pandas.DataFrame.shift`."""

    def correct(
        self,
        metadata: FileMetadata,
        df: pd.DataFrame,
        shift: int,
        target_cols: List[str],
    ) -> pd.DataFrame:
        df = df.copy()
        for col in target_cols:
            outcol = f"{col}_DYCO"
            df[outcol] = df[col].shift(shift)
        return df
