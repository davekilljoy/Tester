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
# Core install (Sleeper features only)
pip install -e .

# Full install with NFL stats (desktop/server)
pip install -e ".[nfl]"
```

### Termux / Android

numpy/pandas don't have pre-built Termux wheels, so extra steps are needed.

**Option A — proot-distro (recommended, easiest):**

```bash
pkg install proot-distro
proot-distro install ubuntu
proot-distro login ubuntu

# Inside Ubuntu — pre-built aarch64 wheels just work
apt update && apt install -y python3 python3-venv git
python3 -m venv ~/ff && source ~/ff/bin/activate
pip install fantasy-football-stats[nfl]
```

**Option B — native Termux (build from source):**

```bash
# 1. Install build dependencies
pkg install python build-essential cmake ninja libopenblas libandroid-execinfo patchelf

# 2. Install Python build tools
pip install setuptools wheel packaging pyproject_metadata cython meson-python versioneer

# 3. Build numpy (replace 3.12 with your Python version)
MATHLIB=m LDFLAGS="-lpython3.12" pip install --no-build-isolation --no-cache-dir numpy

# 4. Build pandas
LDFLAGS="-lpython3.12" pip install --no-build-isolation --no-cache-dir pandas

# 5. Install this tool
pip install nfl_data_py
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
