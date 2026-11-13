# Bold North State — nightly stats

Keeps the school records on the Bold North State Basketball Bible current during the season.

- `data/baseline.json` — each school's official all-time record through the 2025-26 season.
- `scripts/update.py` — adds this season's finished games from [CollegeBasketballData.com](https://collegebasketballdata.com) and writes `docs/stats.json`.
- `.github/workflows/update.yml` — runs the update every morning; it can also be run by hand from the Actions tab.
- `docs/stats.json` — the published numbers, served by GitHub Pages and read by the Squarespace page.

If an update fails, GitHub emails the repo owner and the page keeps showing the last good numbers.

Each April, after the Final Four, the baseline gets the finished season added and the NCAA appearances, Final Fours and titles updated.

Data provided by CollegeBasketballData.com.
