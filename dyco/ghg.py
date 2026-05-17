from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd


class GHGDataProcessor:
    """
    GHG data processor for batch processing LI-COR eddy covariance compressed data files.

    Parameters:
    -----------
    output_dir : str or Path
        Output directory where all extracted files and CSV files will be placed.
    verbose : bool
        Whether to print detailed processing information, default is True.
    """

    def __init__(self, output_dir: Union[str, Path], verbose: bool = True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.processing_log = []

    def log(self, message: str):
        """Record processing log message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.processing_log.append(log_message)
        if self.verbose:
            print(log_message)

    def find_ghg_files(
        self, directory: Union[str, Path], pattern: str = "*.ghg"
    ) -> List[Path]:
        """
        Find all GHG compressed files in the specified directory.

        Parameters:
        -----------
        directory : str or Path
            Directory to search for GHG files.
        pattern : str
            File matching pattern, default is "*.ghg".

        Returns:
        --------
        List[Path]
            List of found compressed file paths.
        """
        directory = Path(directory)
        if not directory.exists():
            self.log(f"Error: Directory does not exist - {directory}")
            return []

        ghg_files = sorted(directory.glob(pattern))
        self.log(f"Found {len(ghg_files)} GHG files in {directory}")

        if self.verbose and ghg_files:
            for f in ghg_files:
                self.log(f"  - {f.name}")

        return ghg_files

    def process_single_file(self, ghg_path: Union[str, Path]) -> Dict:
        """
        Process a single GHG compressed file.

        Parameters:
        -----------
        ghg_path : str or Path
            Path to the GHG compressed file.

        Returns:
        --------
        dict
            Dictionary containing processing results.
        """
        ghg_path = Path(ghg_path)
        base_noext = ghg_path.stem

        result = {
            "file": str(ghg_path),
            "base_name": base_noext,
            "status": "failed",
            "eddy_csv": None,
            "biomet_csv": None,
            "extracted_files": [],
            "error": None,
        }

        try:
            # Check if file exists
            if not ghg_path.exists():
                raise FileNotFoundError(f"File not found: {ghg_path}")

            # Extract all files from the archive (GHG files use zip format internally)
            self.log(f"Extracting: {ghg_path.name}")
            with zipfile.ZipFile(ghg_path, "r") as z:
                z.extractall(self.output_dir)

            # Record extracted files using pathlib
            for file_path in self.output_dir.iterdir():
                if file_path.is_file() and base_noext in file_path.name:
                    result["extracted_files"].append(str(file_path))

            self.log(f"  Extracted {len(result['extracted_files'])} files")

            # Process eddy covariance data file
            data_file = self.output_dir / f"{base_noext}.data"
            if data_file.exists():
                self.log(f"  Processing eddy data: {data_file.name}")
                csv_path = self._process_eddy_data(data_file)
                if csv_path:
                    result["eddy_csv"] = str(csv_path)
            else:
                self.log(f"  Eddy data file not found: {data_file.name}")

            # Process biomet data file
            biomet_file = self.output_dir / f"{base_noext}-biomet.data"
            if biomet_file.exists():
                self.log(f"  Processing biomet data: {biomet_file.name}")
                csv_path = self._process_biomet_data(biomet_file)
                if csv_path:
                    result["biomet_csv"] = str(csv_path)
            else:
                self.log(f"  Biomet data file not found: {biomet_file.name}")

            if result["eddy_csv"] or result["biomet_csv"]:
                result["status"] = "success"
                self.log(f"✓ Successfully processed: {base_noext}")
            else:
                self.log(f"⚠ No data files generated for: {base_noext}")

        except Exception as e:
            result["error"] = str(e)
            self.log(f"✗ Failed to process {base_noext}: {e}")

        return result

    def _process_eddy_data(self, data_file: Path) -> Optional[Path]:
        """
        Process eddy covariance data file and convert to CSV.

        Parameters:
        -----------
        data_file : Path
            Path to the .data file.

        Returns:
        --------
        Path or None
            Path to the generated CSV file, or None if processing failed.
        """
        try:
            with open(data_file, "r") as f:
                lines = [line.rstrip("\n") for line in f]

            if len(lines) < 5:
                self.log(f"    Insufficient lines in file")
                return None

            # Find DATAH header line
            hdr_idx = None
            for i, line in enumerate(lines):
                if line.strip().startswith("DATAH"):
                    hdr_idx = i
                    break

            if hdr_idx is None:
                self.log(f"    DATAH line not found")
                return None

            # Extract column headers
            header_line = lines[hdr_idx].strip()
            header_parts = header_line.replace("DATAH", "").strip().split("\t")
            columns = [col.strip() for col in header_parts if col.strip()]

            self.log(f"    Found {len(columns)} columns")

            # Find all DATA lines
            data_lines = []
            for line in lines[hdr_idx + 1 :]:
                if line.strip().startswith("DATA"):
                    data_content = line.strip()[4:].strip()
                    if data_content:
                        data_lines.append(data_content)

            if not data_lines:
                self.log(f"    No valid data lines found")
                return None

            self.log(f"    Found {len(data_lines)} data rows")

            # Parse data
            data_matrix = []
            for line in data_lines:
                parts = line.split("\t")
                if len(parts) < len(columns):
                    parts += [""] * (len(columns) - len(parts))
                data_matrix.append(parts[: len(columns)])

            # Create DataFrame
            df = pd.DataFrame(data_matrix, columns=columns)

            # Convert numeric columns
            for col in df.columns:
                if col not in ("Date", "Time", "CHK"):
                    try:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    except:
                        pass

            # Generate CSV filename: eddy_ + original_filename + .csv
            csv_filename = f"eddy_{data_file.stem}.csv"
            csv_path = self.output_dir / csv_filename

            # Save to CSV
            df.to_csv(csv_path, index=False, encoding="utf-8")
            self.log(
                f"    Saved: {csv_filename} ({df.shape[0]} rows, {df.shape[1]} columns)"
            )

            return csv_path

        except Exception as e:
            self.log(f"    Failed to process eddy data: {e}")
            return None

    def _process_biomet_data(self, data_file: Path) -> Optional[Path]:
        """
        Process biometeorological data file and convert to CSV.

        Parameters:
        -----------
        data_file : Path
            Path to the -biomet.data file.

        Returns:
        --------
        Path or None
            Path to the generated CSV file, or None if processing failed.
        """
        try:
            with open(data_file, "r") as f:
                lines = [line.rstrip("\n") for line in f]

            if len(lines) < 5:
                self.log(f"    Insufficient lines in file")
                return None

            # Find DATAH header line
            hdr_idx = None
            for i, line in enumerate(lines):
                if line.strip().startswith("DATAH"):
                    hdr_idx = i
                    break

            if hdr_idx is None:
                self.log(f"    DATAH line not found")
                return None

            # Extract column headers
            header_line = lines[hdr_idx].strip()
            header_parts = header_line.replace("DATAH", "").strip().split("\t")
            columns = [col.strip() for col in header_parts if col.strip()]

            self.log(f"    Found {len(columns)} columns")

            # Find all DATA lines
            data_lines = []
            for line in lines[hdr_idx + 1 :]:
                if line.strip().startswith("DATA"):
                    data_content = line.strip()[4:].strip()
                    if data_content:
                        data_lines.append(data_content)

            if not data_lines:
                self.log(f"    No valid data lines found")
                return None

            self.log(f"    Found {len(data_lines)} data rows")

            # Parse data
            data_matrix = []
            for line in data_lines:
                parts = line.split("\t")
                if len(parts) < len(columns):
                    parts += [""] * (len(columns) - len(parts))
                data_matrix.append(parts[: len(columns)])

            # Create DataFrame
            df = pd.DataFrame(data_matrix, columns=columns)

            # Convert numeric columns
            for col in df.columns:
                if col not in ("DATE", "TIME", "CHK"):
                    try:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    except:
                        pass

            # Generate CSV filename: biomet_ + original_filename + .csv
            csv_filename = f"biomet_{data_file.stem}.csv"
            csv_path = self.output_dir / csv_filename

            # Save to CSV
            df.to_csv(csv_path, index=False, encoding="utf-8")
            self.log(
                f"    Saved: {csv_filename} ({df.shape[0]} rows, {df.shape[1]} columns)"
            )

            return csv_path

        except Exception as e:
            self.log(f"    Failed to process biomet data: {e}")
            return None

    def batch_process(
        self, ghg_directory: Union[str, Path], pattern: str = "*.ghg"
    ) -> Dict:
        """
        Batch process all GHG compressed files in the specified directory.

        Parameters:
        -----------
        ghg_directory : str or Path
            Directory containing GHG compressed files.
        pattern : str
            File matching pattern, default is "*.ghg".

        Returns:
        --------
        dict
            Dictionary containing batch processing results summary.
        """
        self.log(f"Starting batch processing of GHG files")
        self.log(f"Source directory: {ghg_directory}")
        self.log(f"Output directory: {self.output_dir}")
        self.log(f"File pattern: {pattern}")

        # Find all GHG files
        ghg_files = self.find_ghg_files(ghg_directory, pattern)

        if not ghg_files:
            self.log("No GHG files found matching the pattern")
            return {"total": 0, "success": 0, "failed": 0, "results": []}

        # Process each file
        results = []
        for i, ghg_file in enumerate(ghg_files, 1):
            self.log(f"\n[{i}/{len(ghg_files)}] Processing: {ghg_file.name}")
            result = self.process_single_file(ghg_file)
            results.append(result)

        # Calculate statistics
        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = sum(1 for r in results if r["status"] == "failed")

        summary = {
            "total": len(results),
            "success": success_count,
            "failed": failed_count,
            "results": results,
            "processing_log": self.processing_log,
        }

        self.log(f"\n{'='*50}")
        self.log(f"Batch processing completed!")
        self.log(f"Total files: {summary['total']}")
        self.log(f"Successfully processed: {summary['success']}")
        self.log(f"Failed: {summary['failed']}")

        # List generated CSV files
        eddy_files = self.get_csv_files("eddy")
        biomet_files = self.get_csv_files("biomet")
        self.log(f"Generated eddy CSV files: {len(eddy_files)}")
        self.log(f"Generated biomet CSV files: {len(biomet_files)}")

        return summary

    def get_csv_files(self, data_type: str = "all") -> List[Path]:
        """
        Get list of CSV files in the output directory.

        Parameters:
        -----------
        data_type : str
            Data type: 'eddy' (eddy covariance), 'biomet' (biometeorological), 'all' (all CSV files).

        Returns:
        --------
        List[Path]
            List of CSV file paths.
        """
        if data_type == "eddy":
            pattern = "eddy_*.csv"
        elif data_type == "biomet":
            pattern = "biomet_*.csv"
        else:
            pattern = "*.csv"

        return sorted(self.output_dir.glob(pattern))

    def get_dataframe(self, csv_path: Union[str, Path]) -> Optional[pd.DataFrame]:
        """
        Read a CSV file into a pandas DataFrame.

        Parameters:
        -----------
        csv_path : str or Path
            Path to the CSV file.

        Returns:
        --------
        pd.DataFrame or None
            DataFrame containing the data, or None if reading failed.
        """
        try:
            csv_path = Path(csv_path)
            if csv_path.exists():
                return pd.read_csv(csv_path)
            else:
                self.log(f"File does not exist: {csv_path}")
                return None
        except Exception as e:
            self.log(f"Failed to read file: {e}")
            return None

    def save_log(self, log_path: Optional[Union[str, Path]] = None):
        """
        Save processing log to a file.

        Parameters:
        -----------
        log_path : str or Path, optional
            Path for the log file. Default is 'processing_log.txt' in the output directory.
        """
        if log_path is None:
            log_path = self.output_dir / "processing_log.txt"

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.processing_log))

        self.log(f"Processing log saved to: {log_path}")


def load_ghg_eddy_csv(
    csv_path: Union[str, Path],
) -> pd.DataFrame:
    """Read a GHG eddy CSV and set a proper DatetimeIndex.

    The ``Seconds`` column is interpreted as Unix epoch seconds.
    """
    df = pd.read_csv(csv_path)
    if "Seconds" not in df.columns:
        raise ValueError("CSV missing 'Seconds' column — not a valid GHG eddy file")

    df.index = pd.to_datetime(df["Seconds"], unit="s")
    df.index.name = "timestamp"
    return df


# Usage example
if __name__ == "__main__":
    # Initialize the processor
    processor = GHGDataProcessor(output_dir="./GHG_Output", verbose=True)

    # Batch process all .ghg files
    summary = processor.batch_process(ghg_directory="./ghg", pattern="*.ghg")

    # Get all generated CSV files
    eddy_csv_files = processor.get_csv_files(data_type="eddy")
    biomet_csv_files = processor.get_csv_files(data_type="biomet")

    print(f"\nGenerated eddy covariance CSV files: {len(eddy_csv_files)}")
    print(f"Generated biometeorological CSV files: {len(biomet_csv_files)}")

    # Read the first eddy covariance CSV for preview
    if eddy_csv_files:
        df = processor.get_dataframe(eddy_csv_files[0])
        if df is not None:
            print(f"\nFirst eddy covariance data file preview:")
            print(df.head())
            print(f"Data shape: {df.shape}")

    # Save processing log
    processor.save_log()
