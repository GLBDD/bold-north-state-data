"""Nightly stats update for the Bold North State Basketball Bible.

Adds this season's finished games (from CollegeBasketballData.com) to each
school's all-time baseline and writes docs/stats.json, which the Squarespace
page reads. If anything looks wrong it exits with an error and leaves the
previous stats.json in place, so the page keeps showing the last good numbers.

Usage:
  python scripts/update.py              # nightly update
  python scripts/update.py --validate   # check the feed against last season's official records
Needs the CBBD_API_KEY environment variable (a GitHub Actions secret).
"""
import json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / 'data' / 'baseline.json'
OUT = ROOT / 'docs' / 'stats.json'
API = 'https://api.collegebasketballdata.com'

# Official 2025-26 records, used by --validate to confirm the feed counts games the way the schools do.
OFFICIAL_2025_26 = {'North Carolina': (24, 9), 'Duke': (35, 3), 'NC State': (20, 14), 'Wake Forest': (18, 17)}


def fetch_games(team, season):
    key = os.environ.get('CBBD_API_KEY')
    if not key:
        sys.exit('CBBD_API_KEY is not set')
    url = f'{API}/games?' + urllib.parse.urlencode({'team': team, 'season': season})
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def season_record(team, games):
    """Wins and losses in finished games for `team`; exhibitions are skipped."""
    w = l = 0
    for g in games:
        if str(g.get('status', '')).lower() != 'final':
            continue
        if 'exhibition' in str(g.get('gameType') or '').lower() or str(g.get('seasonType', '')).lower() == 'preseason':
            continue
        if g.get('homeTeam') == team:
            won = g.get('homeWinner')
        elif g.get('awayTeam') == team:
            won = g.get('awayWinner')
        else:
            continue
        if won is None:
            continue
        w, l = (w + 1, l) if won else (w, l + 1)
    return w, l


def current_season(now):
    # The feed labels a season by the year it ends: 2026-27 is season 2027.
    return now.year + 1 if now.month >= 7 else now.year


def validate():
    problems = []
    for team, (ow, ol) in OFFICIAL_2025_26.items():
        w, l = season_record(team, fetch_games(team, 2026))
        flag = 'OK' if (w, l) == (ow, ol) else 'MISMATCH'
        print(f'{team}: feed {w}-{l}, official {ow}-{ol}  {flag}')
        if flag != 'OK':
            problems.append(team)
    if problems:
        sys.exit('Feed does not match official records for: ' + ', '.join(problems))


def update():
    base = json.loads(BASELINE.read_text(encoding='utf-8'))
    now = datetime.now(timezone.utc)
    season = current_season(now)
    schools = []
    for s in base['schools']:
        games = fetch_games(s['feedTeam'], season)
        w, l = season_record(s['feedTeam'], games)
        if w + l > 45:  # no team plays this many games; the feed or filters are off
            sys.exit(f"{s['feedTeam']}: {w}-{l} this season looks wrong, keeping the previous numbers")
        wins, losses = s['wins'] + w, s['losses'] + l
        schools.append({
            'name': s['name'], 'firstSeason': s['firstSeason'], 'conference': s['conference'],
            'wins': wins, 'losses': losses, 'games': wins + losses,
            'winPct': round(wins / (wins + losses), 3),
            'seasonWins': w, 'seasonLosses': l,
            'ncaaApps': s['ncaaApps'], 'finalFours': s['finalFours'], 'titles': s['titles'], 'notes': s['notes'],
        })
    schools.sort(key=lambda x: x['wins'], reverse=True)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        'updated': now.strftime('%Y-%m-%d'),
        'season': f'{season - 1}-{str(season)[2:]}',
        'schools': schools,
    }, indent=2) + '\n', encoding='utf-8')
    for s in schools:
        print(f"{s['name']}: {s['wins']}-{s['losses']} (this season {s['seasonWins']}-{s['seasonLosses']})")


if __name__ == '__main__':
    validate() if '--validate' in sys.argv else update()
