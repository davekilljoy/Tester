"""Flask web interface for Fantasy Football Stats Tool.

Tablet-friendly UI that wraps the existing CLI functionality.
Run with: ff-stats-web  (or python -m fantasy_stats.web)
"""

import json
import traceback

from flask import Flask, render_template_string, request, jsonify
import pandas as pd

from .analysis import (
    air_yards_share,
    compare_players,
    per_game_quarter_breakdown,
    per_quarter_breakdown,
    red_zone_targets,
)
from .sleeper_api import SleeperClient

app = Flask(__name__)

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FF Stats</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,system-ui,sans-serif;background:#0f172a;color:#e2e8f0;padding:12px;max-width:1200px;margin:auto}
h1{font-size:1.4rem;text-align:center;padding:16px 0;color:#38bdf8}
.tabs{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-bottom:16px}
.tab{padding:8px 16px;border-radius:8px;border:1px solid #334155;background:#1e293b;color:#94a3b8;cursor:pointer;font-size:.9rem;transition:.2s}
.tab.active,.tab:hover{background:#334155;color:#38bdf8;border-color:#38bdf8}
.panel{display:none;background:#1e293b;border-radius:12px;padding:16px;margin-bottom:16px}
.panel.active{display:block}
label{display:block;font-size:.85rem;color:#94a3b8;margin:8px 0 4px}
input,select{width:100%;padding:10px;border-radius:8px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;font-size:1rem}
button.go{width:100%;padding:12px;margin-top:12px;border:none;border-radius:8px;background:#2563eb;color:#fff;font-size:1rem;font-weight:600;cursor:pointer;transition:.2s}
button.go:hover{background:#3b82f6}
button.go:disabled{opacity:.5;cursor:wait}
#results{margin-top:16px}
.result-card{background:#1e293b;border-radius:12px;padding:16px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.82rem}
th{background:#334155;color:#38bdf8;padding:8px 6px;text-align:right;position:sticky;top:0;white-space:nowrap}
th:first-child{text-align:left}
td{padding:6px;border-bottom:1px solid #1e293b;text-align:right;white-space:nowrap}
td:first-child{text-align:left;color:#f1f5f9;font-weight:500}
tr:nth-child(even){background:#0f172a}
tr:hover{background:#334155}
.error{color:#f87171;padding:12px;background:#1e293b;border-radius:8px;border:1px solid #f87171}
.loading{text-align:center;padding:24px;color:#94a3b8}
.loading::after{content:'';display:inline-block;width:18px;height:18px;border:2px solid #38bdf8;border-top-color:transparent;border-radius:50%;animation:spin .8s linear infinite;margin-left:8px;vertical-align:middle}
@keyframes spin{to{transform:rotate(360deg)}}
.info{font-size:.8rem;color:#64748b;margin-top:4px}
</style>
</head>
<body>
<h1>Fantasy Football Stats</h1>

<div class="tabs">
  <div class="tab active" data-panel="p-player">Player</div>
  <div class="tab" data-panel="p-gamelog">Game Log</div>
  <div class="tab" data-panel="p-airshare">Air Share</div>
  <div class="tab" data-panel="p-redzone">Red Zone</div>
  <div class="tab" data-panel="p-compare">Compare</div>
  <div class="tab" data-panel="p-trending">Trending</div>
  <div class="tab" data-panel="p-leagues">Leagues</div>
</div>

<!-- Player -->
<div class="panel active" id="p-player">
  <label>Player Name</label>
  <input id="player-name" placeholder="e.g. J.Chase">
  <label>Season</label>
  <input id="player-season" type="number" value="2024">
  <label>Week Start (optional)</label>
  <input id="player-ws" type="number" placeholder="1">
  <label>Week End (optional)</label>
  <input id="player-we" type="number" placeholder="18">
  <button class="go" onclick="runQuery('player')">Get Stats</button>
</div>

<!-- Game Log -->
<div class="panel" id="p-gamelog">
  <label>Player Name</label>
  <input id="gl-name" placeholder="e.g. A.St.Brown">
  <label>Season</label>
  <input id="gl-season" type="number" value="2024">
  <button class="go" onclick="runQuery('gamelog')">Get Game Log</button>
</div>

<!-- Air Share -->
<div class="panel" id="p-airshare">
  <label>Team Abbreviation</label>
  <input id="air-team" placeholder="e.g. CIN, KC, SF">
  <label>Season</label>
  <input id="air-season" type="number" value="2024">
  <button class="go" onclick="runQuery('airshare')">Get Air Yards Share</button>
</div>

<!-- Red Zone -->
<div class="panel" id="p-redzone">
  <label>Player Name (optional)</label>
  <input id="rz-name" placeholder="e.g. T.Kelce">
  <label>Team (optional, used if no player)</label>
  <input id="rz-team" placeholder="e.g. KC">
  <label>Season</label>
  <input id="rz-season" type="number" value="2024">
  <button class="go" onclick="runQuery('redzone')">Get Red Zone Stats</button>
</div>

<!-- Compare -->
<div class="panel" id="p-compare">
  <label>Player Names (comma-separated)</label>
  <input id="cmp-names" placeholder="e.g. J.Chase, T.Hill, A.St.Brown">
  <label>Season</label>
  <input id="cmp-season" type="number" value="2024">
  <button class="go" onclick="runQuery('compare')">Compare</button>
</div>

<!-- Trending -->
<div class="panel" id="p-trending">
  <label>Type</label>
  <select id="tr-type"><option value="add">Adds</option><option value="drop">Drops</option></select>
  <label>Hours</label>
  <input id="tr-hours" type="number" value="24">
  <label>Limit</label>
  <input id="tr-limit" type="number" value="25">
  <button class="go" onclick="runQuery('trending')">Get Trending</button>
</div>

<!-- Leagues -->
<div class="panel" id="p-leagues">
  <label>Sleeper Username</label>
  <input id="lg-user" placeholder="your_username">
  <label>Season</label>
  <input id="lg-season" type="number" value="2024">
  <button class="go" onclick="runQuery('leagues')">Find Leagues</button>
</div>

<div id="results"></div>

<script>
document.querySelectorAll('.tab').forEach(t=>{
  t.addEventListener('click',()=>{
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
    t.classList.add('active');
    document.getElementById(t.dataset.panel).classList.add('active');
  });
});

function val(id){return document.getElementById(id)?.value?.trim()||''}

function buildParams(cmd){
  switch(cmd){
    case 'player': return {name:val('player-name'),season:val('player-season'),week_start:val('player-ws'),week_end:val('player-we')};
    case 'gamelog': return {name:val('gl-name'),season:val('gl-season')};
    case 'airshare': return {team:val('air-team'),season:val('air-season')};
    case 'redzone': return {name:val('rz-name'),team:val('rz-team'),season:val('rz-season')};
    case 'compare': return {names:val('cmp-names'),season:val('cmp-season')};
    case 'trending': return {type:val('tr-type'),hours:val('tr-hours'),limit:val('tr-limit')};
    case 'leagues': return {username:val('lg-user'),season:val('lg-season')};
  }
}

async function runQuery(cmd){
  const res=document.getElementById('results');
  res.innerHTML='<div class="loading">Loading data</div>';
  document.querySelectorAll('button.go').forEach(b=>b.disabled=true);
  try{
    const r=await fetch('/api/'+cmd,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(buildParams(cmd))});
    const d=await r.json();
    if(d.error){res.innerHTML='<div class="error">'+d.error+'</div>';return;}
    res.innerHTML='<div class="result-card"><h3 style="color:#38bdf8;margin-bottom:10px">'+d.title+'</h3>'+makeTable(d.columns,d.rows)+'</div>';
  }catch(e){res.innerHTML='<div class="error">Request failed: '+e.message+'</div>';}
  finally{document.querySelectorAll('button.go').forEach(b=>b.disabled=false);}
}

function makeTable(cols,rows){
  let h='<table><thead><tr>'+cols.map(c=>'<th>'+c+'</th>').join('')+'</tr></thead><tbody>';
  rows.forEach(r=>{h+='<tr>'+r.map(v=>'<td>'+v+'</td>').join('')+'</tr>';});
  return h+'</tbody></table>';
}
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


def _df_to_response(df: pd.DataFrame, title: str) -> dict:
    """Convert a DataFrame to a JSON-serializable table response."""
    return {
        "title": title,
        "columns": list(df.columns),
        "rows": [[str(v) for v in row] for _, row in df.iterrows()],
    }


@app.post("/api/player")
def api_player():
    data = request.json
    try:
        name = data.get("name", "")
        if not name:
            return jsonify(error="Player name is required.")
        season = int(data.get("season") or 2024)
        weeks = None
        ws, we = data.get("week_start"), data.get("week_end")
        if ws and we:
            weeks = list(range(int(ws), int(we) + 1))
        df = per_quarter_breakdown(name, seasons=[season], weeks=weeks)
        return jsonify(_df_to_response(df, f"Per-Quarter Breakdown: {name}"))
    except ValueError as e:
        return jsonify(error=str(e))
    except Exception as e:
        return jsonify(error=f"Unexpected error: {e}")


@app.post("/api/gamelog")
def api_gamelog():
    data = request.json
    try:
        name = data.get("name", "")
        if not name:
            return jsonify(error="Player name is required.")
        season = int(data.get("season") or 2024)
        df = per_game_quarter_breakdown(name, seasons=[season])
        return jsonify(_df_to_response(df, f"Game Log: {name}"))
    except ValueError as e:
        return jsonify(error=str(e))
    except Exception as e:
        return jsonify(error=f"Unexpected error: {e}")


@app.post("/api/airshare")
def api_airshare():
    data = request.json
    try:
        team = data.get("team", "")
        if not team:
            return jsonify(error="Team abbreviation is required.")
        season = int(data.get("season") or 2024)
        df = air_yards_share(team, seasons=[season])
        return jsonify(_df_to_response(df, f"Air Yards Share: {team.upper()}"))
    except ValueError as e:
        return jsonify(error=str(e))
    except Exception as e:
        return jsonify(error=f"Unexpected error: {e}")


@app.post("/api/redzone")
def api_redzone():
    data = request.json
    try:
        name = data.get("name") or None
        team = data.get("team") or None
        if not name and not team:
            return jsonify(error="Provide a player name or team.")
        season = int(data.get("season") or 2024)
        df = red_zone_targets(player_name=name, team=team, seasons=[season])
        label = name or team.upper()
        return jsonify(_df_to_response(df, f"Red Zone Targets: {label}"))
    except ValueError as e:
        return jsonify(error=str(e))
    except Exception as e:
        return jsonify(error=f"Unexpected error: {e}")


@app.post("/api/compare")
def api_compare():
    data = request.json
    try:
        raw = data.get("names", "")
        names = [n.strip() for n in raw.split(",") if n.strip()]
        if len(names) < 2:
            return jsonify(error="Provide at least 2 player names, comma-separated.")
        season = int(data.get("season") or 2024)
        df = compare_players(names, seasons=[season])
        return jsonify(_df_to_response(df, f"Comparison: {', '.join(names)}"))
    except ValueError as e:
        return jsonify(error=str(e))
    except Exception as e:
        return jsonify(error=f"Unexpected error: {e}")


@app.post("/api/trending")
def api_trending():
    try:
        data = request.json
        client = SleeperClient()
        trend_type = data.get("type", "add")
        hours = int(data.get("hours") or 24)
        limit = int(data.get("limit") or 25)

        trending = client.get_trending(trend_type=trend_type, hours=hours)
        players = client.get_all_players()

        rows = []
        for i, item in enumerate(trending[:limit], 1):
            pid = item["player_id"]
            p = players.get(pid, {})
            name = f"{p.get('first_name', '?')} {p.get('last_name', '?')}"
            rows.append([str(i), name, p.get("position", "?"), p.get("team", "?"), str(item["count"])])

        return jsonify({
            "title": f"Trending {trend_type.title()}s (last {hours}h)",
            "columns": ["Rank", "Player", "Pos", "Team", "Count"],
            "rows": rows,
        })
    except Exception as e:
        return jsonify(error=f"Sleeper API error: {e}")


@app.post("/api/leagues")
def api_leagues():
    try:
        data = request.json
        username = data.get("username", "")
        if not username:
            return jsonify(error="Sleeper username is required.")
        season = str(data.get("season") or 2024)
        client = SleeperClient()
        user = client.get_user(username)
        leagues = client.get_user_leagues(user["user_id"], season=season)

        rows = []
        for lg in leagues:
            scoring = lg.get("scoring_settings", {})
            fmt = "PPR" if scoring.get("rec", 0) == 1 else "Half PPR" if scoring.get("rec", 0) == 0.5 else "Standard"
            rows.append([lg["league_id"], lg.get("name", "?"), str(lg.get("total_rosters", "?")), fmt])

        return jsonify({
            "title": f"Leagues for {username} ({season})",
            "columns": ["League ID", "Name", "Teams", "Scoring"],
            "rows": rows,
        })
    except Exception as e:
        return jsonify(error=f"Sleeper API error: {e}")


def run_web():
    """Entry point for the ff-stats-web command."""
    import argparse
    parser = argparse.ArgumentParser(description="Fantasy Football Stats - Web UI")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5050, help="Port (default: 5050)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    print(f"\n  Fantasy Football Stats Web UI")
    print(f"  Open in your browser: http://localhost:{args.port}\n")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    run_web()
