# ⚽ Football Player Performance Analytics Dashboard

> **⚠️ Synthetic Data Notice:** All player names, club names, and statistics in this project are
> randomly generated for demonstration purposes. They do **not** represent real players, clubs,
> or football results.

---

## 🗂️ Project Overview

An interactive football (soccer) analytics dashboard built with **Python** and **Streamlit**,
designed as a portfolio project demonstrating data visualisation, filtering, and KPI reporting.

### Features

| Feature | Description |
|---|---|
| 📊 Overview | KPI cards (players, goals, assists, minutes, rating) + Top-10 charts |
| 🔍 Player Analysis | Multi-player comparison, Goals vs Assists scatter, Shots vs Goals trendline |
| 🏟️ Team Analysis | Team-level goals, assists, player counts, avg rating |
| 🎽 Position Analysis | GK / DEF / MID / FWD breakdown: donut, box plot, grouped bar |
| 📋 Data Table | Searchable, sortable player table with CSV download |
| 🎛️ Sidebar Filters | Cascading season → team → position → player filters |
| 🎨 Dark UI | Football-inspired dark green theme via `.streamlit/config.toml` |

---

## 📁 File Structure

```
football-analytics-dashboard/
│
├── app.py                      # Main Streamlit application (all pages)
├── generate_data.py            # Reproducible synthetic dataset generator
├── football_players.csv        # Pre-generated synthetic dataset (360 rows)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── .streamlit/
    └── config.toml             # Streamlit dark-green theme
```

---

## 📦 Dataset Schema

The CSV contains **360 rows** (120 synthetic players × 3 seasons).

| Column | Type | Description |
|---|---|---|
| `player_id` | int | Unique player identifier |
| `player_name` | str | Synthetic full name |
| `team` | str | One of 8 fictional club names |
| `position` | str | GK / DEF / MID / FWD |
| `season` | str | 2021-22, 2022-23, or 2023-24 |
| `age` | int | 17–38 |
| `appearances` | int | 1–38 |
| `minutes_played` | int | ~30–90 min per appearance |
| `goals` | int | Position-weighted |
| `assists` | int | Position-weighted |
| `shots` | int | Always ≥ goals |
| `shots_on_target` | int | Between goals and shots |
| `passes` | int | Position-weighted |
| `pass_accuracy` | float | 0.62–0.95 |
| `tackles` | int | Position-weighted |
| `interceptions` | int | Correlated with tackles |
| `yellow_cards` | int | 0–8 |
| `red_cards` | int | 0–2 |
| `rating` | float | 5.0–9.5 |
| `nationality` | str | One of 20 synthetic nationalities |

---

## 🚀 Local Setup & Run

### Prerequisites

- Python **3.9+**
- `pip`

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/football-analytics-dashboard.git
cd football-analytics-dashboard

# 2. (Optional but recommended) Create a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Re-generate the synthetic dataset
python generate_data.py

# 5. Run the dashboard
streamlit run app.py
```

The app will open automatically at **http://localhost:8501**.

---

## ☁️ Deploy to Streamlit Community Cloud

1. Push this repository to **GitHub** (ensure `football_players.csv` is committed).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**.
4. Set **Repository** to your repo, **Branch** to `main`, **Main file path** to `app.py`.
5. Click **Deploy**. Streamlit Cloud installs `requirements.txt` automatically.

> **Note:** The `football_players.csv` file must be committed to the repo so the cloud
> environment can read it. No external API keys are required.

---

## 🛠️ Customisation

- **Add more players/seasons:** Edit `generate_data.py` and re-run it.
- **Change colours:** Update `CHART_LAYOUT` in `app.py` and `.streamlit/config.toml`.
- **Add a new page:** Create a `render_<page>()` function in `app.py` and add it to the
  `st.sidebar.radio` list in `main()`.

---

## 📜 Disclaimer

All data in `football_players.csv` is **synthetically generated** using `numpy.random` with seed 42.
Names, clubs, and statistics are fictional. Do not cite or use this data as real-world football results.
