import numpy as np
import pandas as pd
from pathlib import Path

input_dir = Path(__file__).resolve().parent

# 使用用户提供的完整 header
header = [
    "TIMESTAMP", "U_[R350-B]", "V_[R350-B]", "W_[R350-B]", "T_SONIC_[R350-B]",
    "SA_DIAG_TYPE_[R350-B]", "SA_DIAG_VAL_[R350-B]", "INC_XY_[R350-B]",
    "DATA_SIZE_[IRGA75-A]", "STATUS_CODE_[IRGA75-A]", "GA_DIAG_CODE_[IRGA75-A]",
    "AGC_[IRGA75-A]", "H2O_CONC_[IRGA75-A]", "CO2_CONC_[IRGA75-A]", "T_BOX_[IRGA75-A]",
    "PRESS_BOX_[IRGA75-A]", "COOLER_V_[IRGA75-A]", "DATA_SIZE_[QCL-C2]",
    "STATUS_CODE_[QCL-C2]", "CH4_DRY_[QCL-C2]", "EMPTY_1_[QCL-C2]", "EMPTY_2_[QCL-C2]",
    "H2O_DRY_[QCL-C2]", "T_CELL_[QCL-C2]", "PRESS_CELL_[QCL-C2]", "STATUS_WORD_[QCL-C2]",
    "VICI_[QCL-C2]", "index", "U_[R350-B]_TURB", "V_[R350-B]_TURB", "W_[R350-B]_TURB",
    "CH4_DRY_[QCL-C2]_TURB"
]

# 生成 30min @ 20Hz = 36000 行
n_rows = 36000
dt = 0.05  # seconds
total_time = n_rows * dt  # 1800s = 30min

# 时间戳列：从 00:00.0 开始，每行增加 0.05s
timestamps = []
for i in range(n_rows):
    total_sec = i * dt
    m = int(total_sec // 60)
    s = total_sec % 60
    timestamps.append(f"{m:02d}:{s:06.3f}")

# 生成合成湍流信号
np.random.seed(42)
t = np.arange(n_rows) * dt

# W: 参考信号 = 低频正弦 + 高频噪声
w_turb = 0.5 * np.sin(2 * np.pi * 0.1 * t) + 0.2 * np.random.randn(n_rows)

# CH4: 滞后信号 = W 滞后 5 个记录 (0.25s) + 噪声
lag_records = 5
ch4_turb = np.zeros_like(w_turb)
ch4_turb[lag_records:] = w_turb[:-lag_records]
ch4_turb += 0.15 * np.random.randn(n_rows)

# 构建 DataFrame，其他列填 0 或常数
df = pd.DataFrame(0.0, index=range(n_rows), columns=header)
df["TIMESTAMP"] = timestamps
df["index"] = timestamps  # 原示例中 index 列和 TIMESTAMP 相同
df["U_[R350-B]"] = np.random.randn(n_rows) * 0.1
df["V_[R350-B]"] = np.random.randn(n_rows) * 0.1
df["W_[R350-B]"] = w_turb + np.random.randn(n_rows) * 0.05
df["T_SONIC_[R350-B]"] = 288.0 + np.random.randn(n_rows) * 0.5
df["CH4_DRY_[QCL-C2]"] = 2000.0 + ch4_turb * 0.01
df["U_[R350-B]_TURB"] = df["U_[R350-B]"]
df["V_[R350-B]_TURB"] = df["V_[R350-B]"]
df["W_[R350-B]_TURB"] = w_turb
df["CH4_DRY_[QCL-C2]_TURB"] = ch4_turb

# 保存为 CSV，不带索引（因为header已包含所有列）
filename = "CH-DAS_sim_20230101120000_30MIN-SPLIT_ROT_TRIM.csv"
filepath = input_dir / filename
df.to_csv(filepath, index=False)

print(f"Test file created: {filepath}")
print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
print(f"Known lag: {lag_records} records ({lag_records * dt}s)")
print("\nFirst 3 rows of key columns:")
print(df[["TIMESTAMP", "W_[R350-B]_TURB", "CH4_DRY_[QCL-C2]_TURB"]].head(3))
