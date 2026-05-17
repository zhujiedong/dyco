# DYCO — Python 3.13 Fork with LI-COR GHG Support

This is a fork of [dyco](https://github.com/holukas/dyco). My primary goal was to make the code usable with Python 3.13 (the original is restricted to Python 3.11) and to add direct support for the LI-COR GHG file format. 

Since I made substantial changes to the original codebase, I felt it would be inappropriate and potentially offensive to submit a pull request to the original author. This repository is therefore intended primarily for my own use. However, if you find it helpful (dyco follows GPL 3, meaning modifications are permitted), please also cite the original reference:

```bibtex
@article{Hrtnagl2021,
  title = {DYCO: A Python package to dynamically detect and compensate for time lags in ecosystem time series},
  volume = {6},
  ISSN = {2475-9066},
  url = {http://dx.doi.org/10.21105/joss.02575},
  DOI = {10.21105/joss.02575},
  number = {62},
  journal = {Journal of Open Source Software},
  publisher = {The Open Journal},
  author = {Hörtnagl, Lukas},
  year = {2021},
  month = June,
  pages = {2575}
}
```

The input folder contains a simulated data file with a lag of 5 data points, as well as a data file from the original [dyco](https://github.com/holukas/dyco)  repository.

# File structure 

```
dyco/
├── api.py              # User-friendly entry point
├── config.py           # Configuration management
├── pipeline.py         # Core workflow orchestration
├── models.py           # Data type definitions
├── protocols.py        # Interface protocols (similar to Java interfaces)
├── exceptions.py       # Custom exceptions
│
├── discovery.py        # File discovery
├── io.py               # Data reading
├── segmentation.py     # Data segmentation
├── correction.py       # Lag correction
├── analysis.py         # Result aggregation and analysis
├── reporting.py        # Visualization and reporting
│
├── lag/                # Lag analysis submodule
│   ├── search.py       # Cross-correlation + peak detection
│   ├── window.py       # Adaptive window adjustment
│   └── peaks.py        # Peak finding utilities
│
└── utils/              # Utility modules
    └── logging.py      # Logging configuration
```

# workflow

```
Raw CSV file
    ↓ [discovery.py] Discover files in chronological order
    ↓ [io.py] Read + parse timestamps
    ↓ [segmentation.py] Split into 10-minute segments
    ↓ [lag/search.py] Compute cross-correlation, find optimal lag
    ↓ [lag/window.py] Adjust search window based on histogram analysis
    ↓ [analysis.py] Aggregate multi-day results, remove outliers
    ↓ [correction.py] Apply lag correction
    ↓ [reporting.py] Generate charts and reports
    ↓
Corrected CSV file
```

This project is based on the work of [Lukas Hörtnagl](https://github.com/holukas/dyco) and the original DYCO package. All modifications are released under the same GPL 3 license.
