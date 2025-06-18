
# Stadium Attendance Dashboard
Interactive, static‑HTML dashboard visualising MLB stadium attendance and sell‑through trends using only public data.

## Quick start

```bash
# 1) Clone and install
git clone https://github.com/<you>/stadium-attendance-dashboard.git
cd stadium-attendance-dashboard
python -m venv .venv && .\.venv\Scripts\Activate.ps1   # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# 2) Download data (1 file, ~90 KB)
python scripts/fetch_data.py

# 3) Build the interactive dashboard
python scripts/build_dashboard.py --team "Dallas Cowboys"

# 4) Open the result
start html\dashboard.html   # macOS: open ..., Linux: xdg-open ...
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

