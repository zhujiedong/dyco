from dyco import Dyco

# --- Test 1: simulated data (known lag = 5 records) ---
result = Dyco(
    var_reference="W_[R350-B]_TURB",
    var_lagged="CH4_DRY_[QCL-C2]_TURB",
    var_target=["CH4_DRY_[QCL-C2]_TURB"],
    indir="./input",
    outdir="./output",
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
    indir="./input",
    outdir="./output_example",
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
