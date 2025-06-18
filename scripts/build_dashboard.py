"""Build DuckDB, run SQL analytics & generate dashboard.html."""
import argparse
from pathlib import Path
import duckdb as ddb
import pandas as pd
import plotly.express as px
from jinja2 import Template

ATT_CSV = Path("data/raw/attendance.csv")
SCHED_CSV = Path("data/raw/schedule_2019_2023.csv")
DB_PATH = Path("data/stadium.duckdb")
HTML_OUT = Path("html/dashboard.html")

TEMPLATE_STR = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Stadium Attendance Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <style>
    body {font-family: Arial, sans-serif; margin: 0; padding: 0;}
    .plot {width: 90%; margin: 40px auto;}
  </style>
</head>
<body>
  <h1 style="text-align:center;">Stadium Attendance Dashboard – {{ team }}</h1>
  <div class="plot" id="fig1"></div>
  <div class="plot" id="fig2"></div>
  <div class="plot" id="fig3"></div>
<script>
  const fig1 = {{ fig1 | safe }};
  const fig2 = {{ fig2 | safe }};
  const fig3 = {{ fig3 | safe }};
  Plotly.newPlot('fig1', fig1.data, fig1.layout);
  Plotly.newPlot('fig2', fig2.data, fig2.layout);
  Plotly.newPlot('fig3', fig3.data, fig3.layout);
</script>
</body>
</html>
"""

def prepare_duckdb():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = ddb.connect(DB_PATH)
    con.execute("INSTALL httpfs; LOAD httpfs;")
    # create tables
    con.execute("CREATE OR REPLACE TABLE attendance AS SELECT * FROM read_csv_auto(?)", (str(ATT_CSV),))
    con.execute("CREATE OR REPLACE TABLE schedule   AS SELECT * FROM read_csv_auto(?)", (str(SCHED_CSV),))
    con.close()


def rolling_attendance(con, team):
    query = f"""
    WITH t AS (
        SELECT date, attendance, capacity,
               attendance * 1.0 / capacity AS pct,
               ROW_NUMBER() OVER (ORDER BY date) AS rn
        FROM attendance
        WHERE team = '{team}'
    )
    SELECT date,
           AVG(attendance) OVER (ORDER BY rn ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS roll_att,
           AVG(capacity)   OVER (ORDER BY rn ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS roll_cap
    FROM t
    ORDER BY date;
    """
    return con.execute(query).df()


def weekday_heatmap(con, team):
    query = f"""
    SELECT strftime(date, '%w') AS weekday,
           CAST(strftime(date, '%Y') AS INT) AS YEAR,
           AVG(attendance * 1.0 / capacity) AS sellthrough
    FROM attendance
    WHERE team = '{team}'
    GROUP BY 1, 2
    ORDER BY 2,1;
    """
    return con.execute(query).df()


def sos_line(con, team):
    query = f"""
    SELECT CAST(strftime(date,'%Y') AS INT) AS year,
           AVG(attendance * 1.0 / capacity) AS avg_sellthrough
    FROM attendance
    WHERE team = '{team}'
    GROUP BY 1 ORDER BY 1;
    """
    return con.execute(query).df()


def build_dashboard(team: str = "Atlanta Braves"):
    if not DB_PATH.exists():
        prepare_duckdb()
    con = ddb.connect(DB_PATH, read_only=True)

    # -------------------------------- plots ---------------------------------
    # 1 Rolling attendance
    df_roll = rolling_attendance(con, team)
    fig1 = px.line(df_roll, x="date", y=["roll_att", "roll_cap"], labels={"value": "3‑game avg"})
    fig1.update_layout(title="Rolling 3‑game Attendance vs Capacity")

    # 2 Heatmap weekday
    df_hm = weekday_heatmap(con, team)
    fig2 = px.imshow(df_hm.pivot("weekday", "YEAR", "sellthrough"),
                     aspect="auto", labels=dict(color="Sell‑through"), title="Day‑of‑Week Effect")

    # 3 Season over season
    df_sos = sos_line(con, team)
    fig3 = px.line(df_sos, x="year", y="avg_sellthrough", markers=True, title="Season‑over‑Season Sell‑Through")

    con.close()

    # --------------------------- render HTML ----------------------------
    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    html = Template(TEMPLATE_STR).render(team=team, fig1=fig1.to_json(), fig2=fig2.to_json(), fig3=fig3.to_json())
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"✔ Dashboard written to {HTML_OUT.relative_to(Path.cwd())}")


def cli():
    parser = argparse.ArgumentParser(description="Build stadium attendance dashboard")
    parser.add_argument("--team", default="Atlanta Braves", help="Team name as it appears in the CSVs")
    args = parser.parse_args()
    build_dashboard(args.team)

if __name__ == "__main__":
    cli()
