
# Stadium Attendance Dashboard
Interactive, static‑HTML dashboard visualising MLB stadium attendance and sell‑through trends using only public data.

## Quick start
```bash
# 1Create env
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt                    # or: conda env create -f environment.yml

# Download raw CSVs
python scripts/fetch_data.py

# Build DuckDB + dashboard.html
python scripts/build_dashboard.py --team "Atlanta Braves"

# Open html/dashboard.html in a browser
```

## Directory tree
```text
# data/
#   raw/          # original CSVs
#   stadium.duckdb
# html/
#   dashboard.html
# notebooks/
#   exploration.ipynb
# scripts/
#   fetch_data.py
#   build_dashboard.py
# .github/workflows/pages.yml
```

## Data sources
* **Attendance 2023** – <https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2023/2023-03-28/attendance.csv>
* **Schedules 2019‑2023** – <https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2023/2023-03-28/schedule_2019_2023.csv>
Both are published under the MIT licence in the TidyTuesday repo.

## Plots
1. Rolling 3‑game attendance vs stadium capacity
2. Day‑of‑week heatmap (game × weekday)
3. Season‑over‑season sell‑through line chart

## GitHub Pages
A workflow converts the dashboard to `html/dashboard.html` and pushes the `html/` folder to the `gh-pages` branch so it’s viewable at `https://<username>.github.io/<repo>/dashboard.html`.

