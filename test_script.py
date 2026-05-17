import zipfile
from pathlib import Path
import pandas as pd
from dyco import Dyco

# --- Test 1: simulated data (known lag = 5 records) ---
result = Dyco(
    var_reference="W_[R350-B]_TURB",
    var_lagged="CH4_DRY_[QCL-C2]_TURB",
    var_target=["CH4_DRY_[QCL-C2]_TURB"],
    indir="./data/csv/",
    outdir="./output/output_example/simulate/",
    filename_date_format="CH-DAS_sim_%Y%m%d%H%M%S_30MIN-SPLIT_ROT_TRIM",
    filename_pattern="CH-DAS_*_30MIN-SPLIT_ROT_TRIM.csv",
    data_timestamp_format=None,
    data_nominal_timeres=0.05,
    lag_segment_dur="10min",
    lag_winsize=100,
    lag_n_iter=2,
    lag_hist_remove_fringe_bins=True,
    lag_hist_perc_thres=0.9,
    target_lag=0,
    del_previous_results=True,
).run()

print("\n" + "=" * 60)
print("TEST RESULTS (simulated data)")
print("=" * 60)
print(f"Total lag search results: {len(result.lag_results)}")
print(f"Corrected files: {result.corrected_files}")
print("\nDaily LUT (first few rows):")
print(result.analysis.daily_lut.head())
print("\nHigh-quality peaks (detected lags):")
print(result.analysis.high_quality_peaks.head(10))


# --- Test 2: example data from original dyco ---
result = Dyco(
    var_reference="W_[R350-B]_TURB",
    var_lagged="CH4_DRY_[QCL-C2]_TURB",
    var_target=["CH4_DRY_[QCL-C2]_TURB"],
    indir="./data/csv/",
    outdir="./output/output_example/example/",
    filename_date_format="CH-DAS_example_%Y%m%d%H%M%S_30MIN-SPLIT_ROT_TRIM",
    filename_pattern="CH-DAS_*_30MIN-SPLIT_ROT_TRIM.csv",
    data_timestamp_format=None,
    data_nominal_timeres=0.05,
    lag_segment_dur="10min",
    lag_winsize=100,
    lag_n_iter=2,
    lag_hist_remove_fringe_bins=True,
    lag_hist_perc_thres=0.9,
    target_lag=0,
    del_previous_results=True,
).run()

print("\n" + "=" * 60)
print("TEST RESULTS (example data)")
print("=" * 60)
print(f"Total lag search results: {len(result.lag_results)}")
print(f"Corrected files: {result.corrected_files}")
print("\nDaily LUT (first few rows):")
print(result.analysis.daily_lut.head())
print("\nHigh-quality peaks (detected lags):")
print(result.analysis.high_quality_peaks.head(10))


# --- Test 3: GHG (LI-COR) data — one run per instrument ---
from dyco.ghg import GHGDataProcessor, load_ghg_eddy_csv

ghg_base = Path("./data/ghg")
ghg_out_base = Path("./output/ghg_output")

for instr_dir in sorted(ghg_base.iterdir()):
    if not instr_dir.is_dir():
        continue
    inst_id = instr_dir.name  # e.g. "AIU-0737", "smart3-00572"
    inst_out = ghg_out_base / inst_id
    inst_out.mkdir(parents=True, exist_ok=True)

    # Step 1 — decompress .ghg → CSV
    proc = GHGDataProcessor(output_dir=inst_out, verbose=False)
    summary = proc.batch_process(ghg_directory=str(instr_dir), pattern="*.ghg")

    # Step 2 — convert Seconds column to DatetimeIndex, write dyco-friendly CSV
    csv_dir = inst_out / "_dyco_input"
    csv_dir.mkdir(parents=True, exist_ok=True)
    for r in summary["results"]:
        if r["status"] == "success" and r["eddy_csv"]:
            df = load_ghg_eddy_csv(r["eddy_csv"])
            df.reset_index().to_csv(csv_dir / Path(r["eddy_csv"]).name, index=False)

    if summary["success"] == 0:
        print(f"Skipping {inst_id} — no GHG files processed")
        continue

    # Step 3 — run dyco lag correction
    fmt = f"eddy_%Y-%m-%dT%H%M%S_{inst_id}"
    pat = f"eddy_*_{inst_id}.csv"
    res = Dyco(
        var_reference="W (m/s)",
        var_lagged="CO2 (umol/mol)",
        var_target=["CO2 (umol/mol)"],
        indir=str(csv_dir),
        outdir=str(inst_out / "dyco_output"),
        filename_date_format=fmt,
        filename_pattern=pat,
        data_timestamp_format=None,
        data_nominal_timeres=0.1,
        lag_segment_dur="10min",
        lag_winsize=100,
        lag_n_iter=2,
        lag_hist_remove_fringe_bins=True,
        lag_hist_perc_thres=0.9,
        target_lag=0,
        del_previous_results=True,
    ).run()

    print("\n" + "=" * 60)
    print(f"TEST RESULTS (GHG {inst_id})")
    print("=" * 60)
    print(f"Files: {summary['success']}  |  Lag results: {len(res.lag_results)}")
    print(f"Daily LUT:\n{res.analysis.daily_lut}")
    print(f"High-quality peaks:\n{res.analysis.high_quality_peaks.head(10)}")