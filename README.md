# Fantasy Football Stats Tool

Advanced per-quarter NFL analytics for fantasy football decisions. Combines **nfl_data_py** (Python wrapper for nflreadr play-by-play data) with the **Sleeper API** for league context.

## Stats Available

| Stat | Description |
|------|-------------|
| **aDOT** | Average Depth of Target — how far downfield targets go |
| **Air Yards** | Total yards the ball travels in the air to a receiver |
| **YAC** | Yards After Catch — yards gained after the reception |
| **YAC/Rec** | YAC per reception |
| **Catch Rate** | Receptions / Targets |
| **EPA** | Expected Points Added per target |
| **CPOE** | Completion Probability Over Expected |
| **WPA** | Win Probability Added |
| **Air Yard Share** | % of team air yards a receiver commands |

All stats broken down **per quarter** (Q1-Q4 + OT).

## Install

```bash
pip install -e .
```

## Usage

### Per-Quarter Player Breakdown
```bash
ff-stats player "J.Chase"
ff-stats player "T.Hill" --week-start 1 --week-end 8
ff-stats --season 2023 player "D.Adams"
```

### Game-by-Game Quarter Log
```bash
ff-stats gamelog "A.St.Brown"
```

### Team Air Yards Share by Quarter
```bash
ff-stats airshare CIN
ff-stats airshare KC
```

### Red Zone Targets by Quarter
```bash
ff-stats redzone --name "T.Kelce"
ff-stats redzone --team KC
```

### Compare Players
```bash
ff-stats compare "J.Chase" "T.Hill" "A.St.Brown"
```

### Sleeper Integration

```bash
# Find your leagues
ff-stats leagues your_sleeper_username

# View league rosters
ff-stats roster 123456789

# Trending adds/drops
ff-stats trending --type add --hours 24 --limit 25
ff-stats trending --type drop
```

## Data Sources

- **nfl_data_py** — Python interface to nflreadr's play-by-play, weekly stats, and roster data
- **Sleeper API** — Fantasy league rosters, matchups, trending players
