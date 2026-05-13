This is a fork of [dyco](https://github.com/holukas/dyco). My primary goal was to fork the repository and make the code usable with Python 3.13 (the original is restricted to Python 3.11). However, since I made substantial changes to the original codebase, I felt it would be inappropriate and potentially offensive to submit a pull request to the original author. Fortunately, the code now works perfectly with Python 3.13, so this repository is intended primarily for my own use. But if you find it helpful (dyco follows GPL 3, meaning modifications are permitted), please also cite the original reference:

@article{Hrtnagl2021,
title = {DYCO: A Python package to dynamically detect and compensate for time lags in ecosystem time series},
volume = {6},
ISSN = {2475-9066},
url = {http://dx.doi.org/10.21105/joss.02575},
DOI = {10.21105/joss.02575},
number = {62},
journal = {Journal of Open Source Software},
publisher = {The Open Journal},
author = {H"{o}rtnagl, Lukas},
year = {2021},
month = June,
pages = {2575}
}

The input folder contains a simulated data file with a lag of 5 data points, as well as a data file from the original dyco repository.
