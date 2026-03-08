"""NFL play-by-play data module using nfl_data_py (Python wrapper for nflreadr)."""

import nfl_data_py as nfl
import pandas as pd


def load_pbp(seasons: list[int] | None = None) -> pd.DataFrame:
    """Load play-by-play data for given seasons.

    Uses nfl_data_py which pulls from nflreadr's play-by-play dataset,
    giving us access to advanced metrics like air_yards, yac, etc.
    """
    if seasons is None:
        seasons = [2024]
    return nfl.import_pbp_data(seasons)


def load_weekly_stats(seasons: list[int] | None = None) -> pd.DataFrame:
    """Load weekly player stats."""
    if seasons is None:
        seasons = [2024]
    return nfl.import_weekly_data(seasons)


def load_rosters(seasons: list[int] | None = None) -> pd.DataFrame:
    """Load roster data with player IDs for cross-referencing with Sleeper."""
    if seasons is None:
        seasons = [2024]
    return nfl.import_rosters(seasons)


def get_passing_plays(pbp: pd.DataFrame) -> pd.DataFrame:
    """Filter to passing plays with valid target data."""
    mask = (
        (pbp["play_type"] == "pass")
        & (pbp["air_yards"].notna())
        & (pbp["receiver_player_name"].notna())
    )
    return pbp.loc[mask].copy()


def get_quarter_column(pbp: pd.DataFrame) -> pd.Series:
    """Normalize quarter values (OT periods become 5)."""
    return pbp["qtr"].clip(upper=5)


ADVANCED_RECEIVING_COLS = [
    "game_id",
    "week",
    "posteam",
    "defteam",
    "qtr",
    "receiver_player_id",
    "receiver_player_name",
    "passer_player_name",
    "air_yards",
    "yards_after_catch",
    "yards_gained",
    "complete_pass",
    "touchdown",
    "interception",
    "pass_length",
    "pass_location",
    "cp",           # completion probability (from nflreadr)
    "cpoe",         # completion probability over expected
    "epa",          # expected points added
    "wpa",          # win probability added
    "target_dist",  # depth of target (may be named differently)
]


def extract_receiving_data(pbp: pd.DataFrame) -> pd.DataFrame:
    """Extract receiving-relevant columns from play-by-play data."""
    passing = get_passing_plays(pbp)
    available = [c for c in ADVANCED_RECEIVING_COLS if c in passing.columns]
    df = passing[available].copy()
    df["quarter"] = get_quarter_column(df)
    # aDOT is just air_yards per target — we compute it in aggregation
    return df
