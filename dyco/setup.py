from setuptools import setup, find_packages

setup(
    name="dyco",
    version="0.2.0",
    description="Eddy-covariance lag-time detection and correction",
    license="GPL-3.0",
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.5",
        "numpy>=1.23",
        "scipy>=1.9",
        "matplotlib>=3.6",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
