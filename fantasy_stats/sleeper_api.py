"""Sleeper API integration for fantasy league context."""

import requests

BASE_URL = "https://api.sleeper.app/v1"


class SleeperClient:
    """Client for the Sleeper fantasy football API."""

    def __init__(self):
        self._session = requests.Session()
        self._players_cache = None

    def _get(self, path: str) -> dict | list:
        resp = self._session.get(f"{BASE_URL}{path}")
        resp.raise_for_status()
        return resp.json()

    # ── Players ──────────────────────────────────────────────────────────

    def get_all_players(self) -> dict:
        """Fetch the full Sleeper player database (cached after first call)."""
        if self._players_cache is None:
            self._players_cache = self._get("/players/nfl")
        return self._players_cache

    def get_player(self, player_id: str) -> dict | None:
        """Look up a single player by Sleeper ID."""
        return self.get_all_players().get(player_id)

    def search_players(self, name: str) -> list[dict]:
        """Search players by name (case-insensitive substring match)."""
        name_lower = name.lower()
        results = []
        for pid, info in self.get_all_players().items():
            full = f"{info.get('first_name', '')} {info.get('last_name', '')}".lower()
            if name_lower in full:
                info["sleeper_id"] = pid
                results.append(info)
        return results

    # ── Leagues / Rosters ────────────────────────────────────────────────

    def get_user(self, username: str) -> dict:
        """Get Sleeper user by username."""
        return self._get(f"/user/{username}")

    def get_user_leagues(self, user_id: str, sport: str = "nfl", season: str = "2024") -> list:
        """Get all leagues for a user in a given season."""
        return self._get(f"/user/{user_id}/leagues/{sport}/{season}")

    def get_league(self, league_id: str) -> dict:
        """Get league metadata."""
        return self._get(f"/league/{league_id}")

    def get_rosters(self, league_id: str) -> list:
        """Get all rosters in a league."""
        return self._get(f"/league/{league_id}/rosters")

    def get_league_users(self, league_id: str) -> list:
        """Get all users in a league."""
        return self._get(f"/league/{league_id}/users")

    def get_matchups(self, league_id: str, week: int) -> list:
        """Get matchups for a specific week."""
        return self._get(f"/league/{league_id}/matchups/{week}")

    # ── Trending ─────────────────────────────────────────────────────────

    def get_trending(self, sport: str = "nfl", trend_type: str = "add", hours: int = 24) -> list:
        """Get trending adds/drops."""
        return self._get(f"/players/{sport}/trending/{trend_type}?lookback_hours={hours}")

    # ── Helpers ──────────────────────────────────────────────────────────

    def get_roster_player_names(self, league_id: str) -> dict[str, list[str]]:
        """Return {owner_display_name: [player_names]} for a league."""
        rosters = self.get_rosters(league_id)
        users = self.get_league_users(league_id)
        players = self.get_all_players()

        owner_map = {u["user_id"]: u.get("display_name", u["user_id"]) for u in users}

        result = {}
        for roster in rosters:
            owner = owner_map.get(roster.get("owner_id"), "Unknown")
            names = []
            for pid in roster.get("players") or []:
                p = players.get(pid, {})
                names.append(f"{p.get('first_name', '?')} {p.get('last_name', '?')}")
            result[owner] = names
        return result
