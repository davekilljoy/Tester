"""CLI interface for the Fantasy Football Stats Tool."""

import argparse
import sys

import pandas as pd
from rich.console import Console
from rich.table import Table

from .analysis import (
    air_yards_share,
    compare_players,
    per_game_quarter_breakdown,
    per_quarter_breakdown,
    red_zone_targets,
)
from .sleeper_api import SleeperClient

console = Console()


def _rich_table(df: pd.DataFrame, title: str) -> Table:
    """Convert a DataFrame to a rich Table for pretty terminal output."""
    table = Table(title=title, show_lines=True)
    for col in df.columns:
        table.add_column(str(col), justify="right" if df[col].dtype != object else "left")
    for _, row in df.iterrows():
        table.add_row(*[str(v) for v in row])
    return table


def cmd_player(args):
    """Per-quarter breakdown for a single player."""
    seasons = [args.season] if args.season else None
    weeks = list(range(args.week_start, args.week_end + 1)) if args.week_start else None

    console.print(f"\n[bold cyan]Loading {args.season} play-by-play data...[/bold cyan]")
    df = per_quarter_breakdown(args.name, seasons=seasons, weeks=weeks)
    console.print(_rich_table(df, f"Per-Quarter Breakdown: {args.name}"))


def cmd_game_log(args):
    """Per-game, per-quarter breakdown."""
    seasons = [args.season] if args.season else None

    console.print(f"\n[bold cyan]Loading {args.season} play-by-play data...[/bold cyan]")
    df = per_game_quarter_breakdown(args.name, seasons=seasons)
    console.print(_rich_table(df, f"Game-by-Game Quarter Breakdown: {args.name}"))


def cmd_air_share(args):
    """Air yards share for a team."""
    seasons = [args.season] if args.season else None

    console.print(f"\n[bold cyan]Loading {args.season} play-by-play data...[/bold cyan]")
    df = air_yards_share(args.team, seasons=seasons)
    console.print(_rich_table(df, f"Air Yards Share by Quarter: {args.team.upper()}"))


def cmd_redzone(args):
    """Red zone target breakdown."""
    seasons = [args.season] if args.season else None

    console.print(f"\n[bold cyan]Loading {args.season} play-by-play data...[/bold cyan]")
    df = red_zone_targets(
        player_name=args.name,
        team=args.team,
        seasons=seasons,
    )
    label = args.name or args.team.upper()
    console.print(_rich_table(df, f"Red Zone Targets by Quarter: {label}"))


def cmd_compare(args):
    """Compare multiple players side by side."""
    seasons = [args.season] if args.season else None

    console.print(f"\n[bold cyan]Loading {args.season} play-by-play data...[/bold cyan]")
    df = compare_players(args.names, seasons=seasons)
    console.print(_rich_table(df, f"Player Comparison by Quarter"))


def cmd_sleeper_roster(args):
    """Show rosters from a Sleeper league."""
    client = SleeperClient()

    console.print(f"\n[bold cyan]Fetching league {args.league_id} from Sleeper...[/bold cyan]")
    league = client.get_league(args.league_id)
    console.print(f"[bold]{league.get('name', 'Unknown League')}[/bold]")

    rosters = client.get_roster_player_names(args.league_id)
    for owner, players in rosters.items():
        console.print(f"\n[bold green]{owner}[/bold green]")
        for p in sorted(players):
            console.print(f"  {p}")


def cmd_sleeper_trending(args):
    """Show trending adds/drops from Sleeper."""
    client = SleeperClient()

    console.print(f"\n[bold cyan]Fetching trending {args.type}s from Sleeper...[/bold cyan]")
    trending = client.get_trending(trend_type=args.type, hours=args.hours)
    players = client.get_all_players()

    table = Table(title=f"Trending {args.type.title()}s (last {args.hours}h)", show_lines=True)
    table.add_column("Rank", justify="right")
    table.add_column("Player")
    table.add_column("Position")
    table.add_column("Team")
    table.add_column("Count", justify="right")

    for i, item in enumerate(trending[:args.limit], 1):
        pid = item["player_id"]
        p = players.get(pid, {})
        name = f"{p.get('first_name', '?')} {p.get('last_name', '?')}"
        table.add_row(str(i), name, p.get("position", "?"), p.get("team", "?"), str(item["count"]))

    console.print(table)


def cmd_sleeper_league_search(args):
    """Look up a user's leagues on Sleeper."""
    client = SleeperClient()

    console.print(f"\n[bold cyan]Looking up Sleeper user: {args.username}[/bold cyan]")
    user = client.get_user(args.username)
    user_id = user["user_id"]

    leagues = client.get_user_leagues(user_id, season=str(args.season))
    table = Table(title=f"Leagues for {args.username} ({args.season})", show_lines=True)
    table.add_column("League ID")
    table.add_column("Name")
    table.add_column("Teams", justify="right")
    table.add_column("Scoring")

    for lg in leagues:
        scoring = lg.get("scoring_settings", {})
        fmt = "PPR" if scoring.get("rec", 0) == 1 else "Half PPR" if scoring.get("rec", 0) == 0.5 else "Standard"
        table.add_row(lg["league_id"], lg.get("name", "?"), str(lg.get("total_rosters", "?")), fmt)

    console.print(table)


def main():
    parser = argparse.ArgumentParser(
        prog="ff-stats",
        description="Fantasy Football Stats Tool - Advanced per-quarter NFL analytics",
    )
    parser.add_argument("--season", type=int, default=2024, help="NFL season year (default: 2024)")
    sub = parser.add_subparsers(dest="command", required=True)

    # ── NFL Stats commands ───────────────────────────────────────────────

    p_player = sub.add_parser("player", help="Per-quarter breakdown for a player")
    p_player.add_argument("name", help="Player name (e.g. 'J.Chase')")
    p_player.add_argument("--week-start", type=int, help="Start week filter")
    p_player.add_argument("--week-end", type=int, help="End week filter")
    p_player.set_defaults(func=cmd_player)

    p_gamelog = sub.add_parser("gamelog", help="Per-game quarter breakdown")
    p_gamelog.add_argument("name", help="Player name")
    p_gamelog.set_defaults(func=cmd_game_log)

    p_air = sub.add_parser("airshare", help="Air yards share by team")
    p_air.add_argument("team", help="Team abbreviation (e.g. CIN, KC)")
    p_air.set_defaults(func=cmd_air_share)

    p_rz = sub.add_parser("redzone", help="Red zone targets by quarter")
    p_rz.add_argument("--name", help="Player name")
    p_rz.add_argument("--team", help="Team abbreviation")
    p_rz.set_defaults(func=cmd_redzone)

    p_cmp = sub.add_parser("compare", help="Compare players side by side")
    p_cmp.add_argument("names", nargs="+", help="Player names to compare")
    p_cmp.set_defaults(func=cmd_compare)

    # ── Sleeper commands ─────────────────────────────────────────────────

    p_roster = sub.add_parser("roster", help="Show Sleeper league rosters")
    p_roster.add_argument("league_id", help="Sleeper league ID")
    p_roster.set_defaults(func=cmd_sleeper_roster)

    p_trend = sub.add_parser("trending", help="Sleeper trending adds/drops")
    p_trend.add_argument("--type", choices=["add", "drop"], default="add")
    p_trend.add_argument("--hours", type=int, default=24)
    p_trend.add_argument("--limit", type=int, default=25)
    p_trend.set_defaults(func=cmd_sleeper_trending)

    p_leagues = sub.add_parser("leagues", help="Find your Sleeper leagues")
    p_leagues.add_argument("username", help="Sleeper username")
    p_leagues.set_defaults(func=cmd_sleeper_league_search)

    args = parser.parse_args()
    try:
        args.func(args)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
        sys.exit(0)


if __name__ == "__main__":
    main()
