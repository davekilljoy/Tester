from setuptools import setup, find_packages

setup(
    name="fantasy-football-stats",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "nfl_data_py>=0.3.0",
        "requests>=2.28.0",
        "pandas>=1.5.0",
        "tabulate>=0.9.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ff-stats=fantasy_stats.cli:main",
        ],
    },
    python_requires=">=3.10",
)
