"""Per-quarter advanced stats analysis engine."""

import pandas as pd

from .nfl_data import extract_receiving_data, load_pbp


def _agg_receiving(group: pd.DataFrame) -> pd.Series:
    """Compute advanced receiving aggregates for a group of targets."""
    targets = len(group)
    receptions = int(group["complete_pass"].sum())
    total_yards = group["yards_gained"].sum()
    air = group["air_yards"].sum()
    yac = group.get("yards_after_catch")
    yac_total = yac.sum() if yac is not None else 0.0
    tds = int(group["touchdown"].sum()) if "touchdown" in group.columns else 0

    adot = air / targets if targets else 0.0
    yac_per_rec = yac_total / receptions if receptions else 0.0
    catch_rate = receptions / targets if targets else 0.0

    result = {
        "targets": targets,
        "receptions": receptions,
        "catch_rate": round(catch_rate, 3),
        "total_yards": round(total_yards, 1),
        "air_yards": round(air, 1),
        "yac": round(yac_total, 1),
        "adot": round(adot, 1),
        "yac_per_rec": round(yac_per_rec, 1),
        "tds": tds,
    }

    if "epa" in group.columns:
        result["total_epa"] = round(group["epa"].sum(), 2)
        result["epa_per_target"] = round(group["epa"].mean(), 2)

    if "cpoe" in group.columns and group["cpoe"].notna().any():
        result["avg_cpoe"] = round(group["cpoe"].mean(), 2)

    if "wpa" in group.columns:
        result["total_wpa"] = round(group["wpa"].sum(), 3)

    return pd.Series(result)


def per_quarter_breakdown(
    player_name: str,
    seasons: list[int] | None = None,
    weeks: list[int] | None = None,
    pbp: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Get per-quarter receiving stats for a player.

    Returns a DataFrame indexed by quarter (1-5, where 5 = OT) with columns:
    targets, receptions, catch_rate, total_yards, air_yards, yac,
    adot, yac_per_rec, tds, total_epa, epa_per_target, avg_cpoe, total_wpa
    """
    if pbp is None:
        pbp = load_pbp(seasons)

    recv = extract_receiving_data(pbp)

    # Filter to player
    mask = recv["receiver_player_name"].str.contains(player_name, case=False, na=False)
    player_data = recv.loc[mask]

    if player_data.empty:
        raise ValueError(f"No data found for player: {player_name}")

    if weeks:
        player_data = player_data[player_data["week"].isin(weeks)]

    return player_data.groupby("quarter").apply(_agg_receiving).reset_index()


def per_game_quarter_breakdown(
    player_name: str,
    seasons: list[int] | None = None,
    pbp: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Get per-game, per-quarter breakdown for a player.

    Returns DataFrame with columns: game_id, week, quarter, + all stat columns.
    Great for seeing which quarters a player dominates week to week.
    """
    if pbp is None:
        pbp = load_pbp(seasons)

    recv = extract_receiving_data(pbp)
    mask = recv["receiver_player_name"].str.contains(player_name, case=False, na=False)
    player_data = recv.loc[mask]

    if player_data.empty:
        raise ValueError(f"No data found for player: {player_name}")

    return (
        player_data.groupby(["game_id", "week", "quarter"])
        .apply(_agg_receiving)
        .reset_index()
        .sort_values(["week", "quarter"])
    )


def air_yards_share(
    team: str,
    seasons: list[int] | None = None,
    pbp: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Air yards share by receiver for a team, broken down by quarter.

    Shows which receivers get the deep looks and in which quarters.
    """
    if pbp is None:
        pbp = load_pbp(seasons)

    recv = extract_receiving_data(pbp)
    team_data = recv[recv["posteam"] == team.upper()]

    if team_data.empty:
        raise ValueError(f"No data found for team: {team}")

    grouped = (
        team_data.groupby(["receiver_player_name", "quarter"])
        .apply(_agg_receiving)
        .reset_index()
    )

    # Calculate air yard share within each quarter
    quarter_totals = grouped.groupby("quarter")["air_yards"].transform("sum")
    grouped["air_yard_share"] = (grouped["air_yards"] / quarter_totals).round(3)

    return grouped.sort_values(["quarter", "air_yard_share"], ascending=[True, False])


def red_zone_targets(
    player_name: str | None = None,
    team: str | None = None,
    seasons: list[int] | None = None,
    pbp: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Red zone target analysis by quarter.

    Filters to plays inside the 20-yard line and shows target distribution.
    """
    if pbp is None:
        pbp = load_pbp(seasons)

    recv = extract_receiving_data(pbp)

    # Red zone: yardline_100 <= 20
    if "yardline_100" in pbp.columns:
        rz_game_ids = pbp.loc[pbp["yardline_100"] <= 20, "game_id"]
        # Re-extract with red zone filter on original pbp
        rz_pbp = pbp[pbp["yardline_100"] <= 20]
        recv = extract_receiving_data(rz_pbp)

    if player_name:
        mask = recv["receiver_player_name"].str.contains(player_name, case=False, na=False)
        recv = recv[mask]
    elif team:
        recv = recv[recv["posteam"] == team.upper()]

    if recv.empty:
        raise ValueError("No red zone data found for the given filters.")

    return (
        recv.groupby(["receiver_player_name", "quarter"])
        .apply(_agg_receiving)
        .reset_index()
        .sort_values(["quarter", "targets"], ascending=[True, False])
    )


def compare_players(
    player_names: list[str],
    seasons: list[int] | None = None,
    pbp: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Side-by-side per-quarter comparison of multiple players."""
    if pbp is None:
        pbp = load_pbp(seasons)

    frames = []
    for name in player_names:
        try:
            df = per_quarter_breakdown(name, pbp=pbp)
            df.insert(0, "player", name)
            frames.append(df)
        except ValueError:
            continue

    if not frames:
        raise ValueError("No data found for any of the provided players.")

    return pd.concat(frames, ignore_index=True)
