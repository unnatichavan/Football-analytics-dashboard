"""
app.py
------
Football Player Performance Analytics Dashboard
⚠️  ALL DATA IS SYNTHETIC — not real-world football statistics.

Run:
    streamlit run app.py
"""

import io
import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="⚽ Football Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Shared Plotly dark-green theme
# ---------------------------------------------------------------------------
CHART_LAYOUT = dict(
    paper_bgcolor="#0d1117",
    plot_bgcolor="#161b22",
    font=dict(color="#e6edf3", family="Segoe UI, Arial, sans-serif"),
    title_font=dict(color="#e6edf3", size=15),
    legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
    xaxis=dict(gridcolor="#21262d", zerolinecolor="#30363d", tickfont=dict(color="#8b949e")),
    yaxis=dict(gridcolor="#21262d", zerolinecolor="#30363d", tickfont=dict(color="#8b949e")),
    margin=dict(l=40, r=20, t=50, b=40),
    colorway=["#00c853", "#69f0ae", "#1de9b6", "#64ffda", "#b9f6ca",
               "#f9a825", "#ff6f00", "#e53935"],
)

ACCENT_GREEN = "#00c853"
SECONDARY_GREEN = "#69f0ae"
POSITION_COLORS = {
    "GK": "#f9a825",
    "DEF": "#1de9b6",
    "MID": "#00c853",
    "FWD": "#e53935",
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
REQUIRED_COLUMNS = [
    "player_id", "player_name", "team", "position", "season", "age",
    "appearances", "minutes_played", "goals", "assists", "shots",
    "shots_on_target", "passes", "pass_accuracy", "tackles",
    "interceptions", "yellow_cards", "red_cards", "rating", "nationality",
]

CSV_PATH = os.path.join(os.path.dirname(__file__), "football_players.csv")


@st.cache_data(show_spinner="Loading player data…")
def load_data() -> pd.DataFrame:
    """Read, validate and type-cast the football players CSV."""
    if not os.path.exists(CSV_PATH):
        st.error(
            "⚠️ `football_players.csv` not found. "
            "Run `python generate_data.py` first to create the dataset."
        )
        st.stop()

    df = pd.read_csv(CSV_PATH)

    # Column validation
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        st.error(f"⚠️ CSV is missing required columns: {missing_cols}")
        st.stop()

    # Drop rows where critical identifiers are null
    df.dropna(subset=["player_id", "player_name", "team", "position", "season"], inplace=True)

    # Fill optional numeric nulls with 0
    num_cols = ["goals", "assists", "shots", "shots_on_target", "passes",
                "tackles", "interceptions", "yellow_cards", "red_cards",
                "appearances", "minutes_played"]
    df[num_cols] = df[num_cols].fillna(0)

    # Fill rating nulls with column median
    if df["rating"].isnull().any():
        df["rating"] = df["rating"].fillna(df["rating"].median())

    # Enforce dtypes
    int_cols = ["player_id", "age", "appearances", "minutes_played", "goals",
                "assists", "shots", "shots_on_target", "passes", "tackles",
                "interceptions", "yellow_cards", "red_cards"]
    for col in int_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["pass_accuracy"] = pd.to_numeric(df["pass_accuracy"], errors="coerce").fillna(0.0)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)

    # Clip values to valid ranges
    df["rating"] = df["rating"].clip(0.0, 10.0)
    df["pass_accuracy"] = df["pass_accuracy"].clip(0.0, 1.0)
    df["goals"] = df["goals"].clip(0)
    df["assists"] = df["assists"].clip(0)

    return df


# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
def build_sidebar(df: pd.DataFrame):
    """Render sidebar filters and return filtered DataFrame."""
    st.sidebar.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Soccer_ball.svg/100px-Soccer_ball.svg.png",
        width=60,
    )
    st.sidebar.title("⚽ Football Analytics")
    st.sidebar.caption(
        "⚠️ **Synthetic Data Only** — statistics are randomly generated "
        "and do not represent real players or clubs."
    )
    st.sidebar.divider()

    # Season
    seasons = sorted(df["season"].unique().tolist())
    sel_seasons = st.sidebar.multiselect("🗓️ Season", seasons, default=seasons)
    if not sel_seasons:
        sel_seasons = seasons

    df_f = df[df["season"].isin(sel_seasons)]

    # Team (cascades from season)
    teams = sorted(df_f["team"].unique().tolist())
    sel_teams = st.sidebar.multiselect("🏟️ Team", teams, default=teams)
    if not sel_teams:
        sel_teams = teams

    df_f = df_f[df_f["team"].isin(sel_teams)]

    # Position (cascades from team)
    positions = sorted(df_f["position"].unique().tolist())
    sel_positions = st.sidebar.multiselect("🎽 Position", positions, default=positions)
    if not sel_positions:
        sel_positions = positions

    df_f = df_f[df_f["position"].isin(sel_positions)]

    # Player (cascades from position)
    players = sorted(df_f["player_name"].unique().tolist())
    sel_players = st.sidebar.multiselect("👤 Player", players, default=[])

    if sel_players:
        df_f = df_f[df_f["player_name"].isin(sel_players)]

    st.sidebar.divider()
    st.sidebar.caption(f"**{len(df_f):,}** records after filters")

    if df_f.empty:
        st.warning("⚠️ No data matches the current filters. Please adjust your selections.")
        st.stop()

    return df_f


# ---------------------------------------------------------------------------
# Helper: apply chart layout
# ---------------------------------------------------------------------------
def style_fig(fig: go.Figure) -> go.Figure:
    fig.update_layout(**CHART_LAYOUT)
    return fig


# ---------------------------------------------------------------------------
# Page 1 — Overview
# ---------------------------------------------------------------------------
def render_overview(df: pd.DataFrame, df_all: pd.DataFrame):
    st.header("📊 Overview")
    st.caption("High-level KPIs computed from the filtered dataset.")

    total_players = df["player_id"].nunique()
    total_goals = int(df["goals"].sum())
    total_assists = int(df["assists"].sum())
    total_minutes = int(df["minutes_played"].sum())
    avg_rating = round(float(df["rating"].mean()), 2)

    # Deltas vs full dataset
    all_avg_rating = round(float(df_all["rating"].mean()), 2)
    delta_rating = round(avg_rating - all_avg_rating, 2)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("👥 Total Players", f"{total_players:,}")
    col2.metric("⚽ Total Goals", f"{total_goals:,}")
    col3.metric("🎯 Total Assists", f"{total_assists:,}")
    col4.metric("⏱️ Total Minutes", f"{total_minutes:,}")
    col5.metric("⭐ Avg Rating", f"{avg_rating}", delta=f"{delta_rating:+.2f} vs all")

    st.divider()

    # Top 10 by goals
    top_goals = (
        df.groupby("player_name", as_index=False)["goals"]
        .sum()
        .sort_values("goals", ascending=False)
        .head(10)
    )
    fig_goals = px.bar(
        top_goals,
        x="goals",
        y="player_name",
        orientation="h",
        title="🏆 Top 10 Players by Total Goals",
        labels={"goals": "Goals", "player_name": "Player"},
        color="goals",
        color_continuous_scale=[[0, "#1a472a"], [1, ACCENT_GREEN]],
    )
    fig_goals.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    style_fig(fig_goals)

    # Top 10 by rating
    top_rating = (
        df.groupby("player_name", as_index=False)["rating"]
        .mean()
        .sort_values("rating", ascending=False)
        .head(10)
    )
    top_rating["rating"] = top_rating["rating"].round(2)
    fig_rating = px.bar(
        top_rating,
        x="rating",
        y="player_name",
        orientation="h",
        title="⭐ Top 10 Players by Average Rating",
        labels={"rating": "Avg Rating", "player_name": "Player"},
        color="rating",
        color_continuous_scale=[[0, "#1a472a"], [1, "#f9a825"]],
    )
    fig_rating.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    style_fig(fig_rating)

    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_goals, use_container_width=True)
    c2.plotly_chart(fig_rating, use_container_width=True)


# ---------------------------------------------------------------------------
# Page 2 — Player Analysis
# ---------------------------------------------------------------------------
def render_player_analysis(df: pd.DataFrame):
    st.header("🔍 Player Analysis")

    # ── Player comparison ──────────────────────────────────────────────────
    st.subheader("Player Comparison")
    all_players = sorted(df["player_name"].unique().tolist())

    # Default: top 3 scorers
    top3 = (
        df.groupby("player_name")["goals"].sum()
        .sort_values(ascending=False)
        .head(3)
        .index.tolist()
    )
    default_sel = [p for p in top3 if p in all_players]

    selected = st.multiselect(
        "Select 2–5 players to compare",
        all_players,
        default=default_sel,
        max_selections=5,
    )

    if len(selected) < 2:
        st.info("ℹ️ Select at least 2 players to display the comparison chart.")
    else:
        cmp = (
            df[df["player_name"].isin(selected)]
            .groupby("player_name", as_index=False)
            .agg(
                goals=("goals", "sum"),
                assists=("assists", "sum"),
                shots=("shots", "sum"),
                passes=("passes", "sum"),
                tackles=("tackles", "sum"),
                rating=("rating", "mean"),
            )
        )
        cmp["rating"] = cmp["rating"].round(2)

        metrics = ["goals", "assists", "shots", "passes", "tackles", "rating"]
        fig_cmp = go.Figure()
        colors = CHART_LAYOUT["colorway"]
        for idx, row in cmp.iterrows():
            fig_cmp.add_trace(go.Bar(
                name=row["player_name"],
                x=metrics,
                y=[row[m] for m in metrics],
                marker_color=colors[idx % len(colors)],
            ))
        fig_cmp.update_layout(
            barmode="group",
            title="Player Stats Comparison",
            xaxis_title="Metric",
            yaxis_title="Value",
        )
        style_fig(fig_cmp)
        st.plotly_chart(fig_cmp, use_container_width=True)

    st.divider()

    # ── Goals vs Assists scatter ───────────────────────────────────────────
    st.subheader("Goals vs Assists")
    scatter_df = (
        df.groupby(["player_name", "position", "team"], as_index=False)
        .agg(goals=("goals", "sum"), assists=("assists", "sum"),
             minutes_played=("minutes_played", "sum"))
    )
    scatter_df["pos_color"] = scatter_df["position"].map(POSITION_COLORS)

    fig_ga = px.scatter(
        scatter_df,
        x="assists",
        y="goals",
        color="position",
        size="minutes_played",
        hover_name="player_name",
        hover_data={"team": True, "minutes_played": True, "position": False},
        title="Goals vs Assists (bubble size = minutes played)",
        labels={"goals": "Total Goals", "assists": "Total Assists"},
        color_discrete_map=POSITION_COLORS,
        size_max=30,
    )
    style_fig(fig_ga)
    st.plotly_chart(fig_ga, use_container_width=True)

    st.divider()

    # ── Shots vs Goals scatter + trendline ───────────────────────────────
    st.subheader("Shots vs Goals")
    sg_df = (
        df.groupby(["player_name", "position"], as_index=False)
        .agg(goals=("goals", "sum"), shots=("shots", "sum"))
    )
    sg_df = sg_df[sg_df["shots"] > 0]

    fig_sg = go.Figure()

    # Scatter points coloured by position
    for pos, grp in sg_df.groupby("position"):
        fig_sg.add_trace(go.Scatter(
            x=grp["shots"],
            y=grp["goals"],
            mode="markers",
            name=pos,
            marker=dict(color=POSITION_COLORS.get(pos, ACCENT_GREEN), size=8, opacity=0.75),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Shots: %{x}<br>"
                "Goals: %{y}<extra></extra>"
            ),
            text=grp["player_name"],
        ))

    # Manual OLS trendline via numpy.polyfit
    if len(sg_df) >= 2:
        coeffs = np.polyfit(sg_df["shots"], sg_df["goals"], 1)
        x_line = np.linspace(sg_df["shots"].min(), sg_df["shots"].max(), 100)
        y_line = np.polyval(coeffs, x_line)
        fig_sg.add_trace(go.Scatter(
            x=x_line,
            y=y_line,
            mode="lines",
            name="Trend",
            line=dict(color="#f9a825", width=2, dash="dash"),
        ))

    fig_sg.update_layout(
        title="Shots vs Goals with Trendline",
        xaxis_title="Total Shots",
        yaxis_title="Total Goals",
    )
    style_fig(fig_sg)
    st.plotly_chart(fig_sg, use_container_width=True)


# ---------------------------------------------------------------------------
# Page 3 — Team Analysis
# ---------------------------------------------------------------------------
def render_team_analysis(df: pd.DataFrame):
    st.header("🏟️ Team Analysis")

    team_agg = (
        df.groupby("team", as_index=False)
        .agg(
            total_goals=("goals", "sum"),
            total_assists=("assists", "sum"),
            total_minutes=("minutes_played", "sum"),
            player_count=("player_id", "nunique"),
            avg_rating=("rating", "mean"),
        )
        .sort_values("total_goals", ascending=False)
    )
    team_agg["avg_rating"] = team_agg["avg_rating"].round(2)

    # Goals + Assists grouped bar
    fig_ga = go.Figure()
    fig_ga.add_trace(go.Bar(
        name="Goals", x=team_agg["team"], y=team_agg["total_goals"],
        marker_color=ACCENT_GREEN,
    ))
    fig_ga.add_trace(go.Bar(
        name="Assists", x=team_agg["team"], y=team_agg["total_assists"],
        marker_color=SECONDARY_GREEN,
    ))
    fig_ga.update_layout(barmode="group", title="Total Goals & Assists by Team",
                         xaxis_title="Team", yaxis_title="Count")
    style_fig(fig_ga)

    # Player count bar
    fig_pc = px.bar(
        team_agg, x="team", y="player_count",
        title="Player Count per Team",
        labels={"player_count": "Players", "team": "Team"},
        color="player_count",
        color_continuous_scale=[[0, "#1a472a"], [1, ACCENT_GREEN]],
    )
    fig_pc.update_layout(coloraxis_showscale=False)
    style_fig(fig_pc)

    # Avg rating bar
    fig_rt = px.bar(
        team_agg, x="team", y="avg_rating",
        title="Average Player Rating by Team",
        labels={"avg_rating": "Avg Rating", "team": "Team"},
        color="avg_rating",
        color_continuous_scale=[[0, "#1a472a"], [1, "#f9a825"]],
    )
    fig_rt.update_layout(coloraxis_showscale=False)
    style_fig(fig_rt)

    st.plotly_chart(fig_ga, use_container_width=True)

    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_pc, use_container_width=True)
    c2.plotly_chart(fig_rt, use_container_width=True)

    st.subheader("Team Summary Table")
    display_cols = {
        "team": "Team",
        "total_goals": "Goals",
        "total_assists": "Assists",
        "player_count": "Players",
        "total_minutes": "Minutes",
        "avg_rating": "Avg Rating",
    }
    st.dataframe(
        team_agg.rename(columns=display_cols)[list(display_cols.values())],
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# Page 4 — Position Analysis
# ---------------------------------------------------------------------------
def render_position_analysis(df: pd.DataFrame):
    st.header("🎽 Position Analysis")

    pos_order = ["GK", "DEF", "MID", "FWD"]

    pos_agg = (
        df.groupby("position", as_index=False)
        .agg(
            player_count=("player_id", "nunique"),
            avg_goals=("goals", "mean"),
            avg_assists=("assists", "mean"),
            avg_tackles=("tackles", "mean"),
            avg_rating=("rating", "mean"),
        )
    )
    pos_agg["avg_goals"] = pos_agg["avg_goals"].round(2)
    pos_agg["avg_assists"] = pos_agg["avg_assists"].round(2)
    pos_agg["avg_tackles"] = pos_agg["avg_tackles"].round(2)
    pos_agg["avg_rating"] = pos_agg["avg_rating"].round(2)

    # Ensure all 4 positions present even if filter excludes some
    for pos in pos_order:
        if pos not in pos_agg["position"].values:
            pos_agg = pd.concat(
                [pos_agg, pd.DataFrame([{"position": pos, "player_count": 0,
                                          "avg_goals": 0, "avg_assists": 0,
                                          "avg_tackles": 0, "avg_rating": 0}])],
                ignore_index=True,
            )
    pos_agg["position"] = pd.Categorical(pos_agg["position"], categories=pos_order, ordered=True)
    pos_agg = pos_agg.sort_values("position")

    # Donut chart — player count
    fig_donut = px.pie(
        pos_agg,
        names="position",
        values="player_count",
        hole=0.45,
        title="Player Distribution by Position",
        color="position",
        color_discrete_map=POSITION_COLORS,
    )
    fig_donut.update_traces(textinfo="label+percent", textfont_color="#e6edf3")
    style_fig(fig_donut)

    # Box plot — rating distribution
    rating_df = df.copy()
    rating_df["position"] = pd.Categorical(rating_df["position"], categories=pos_order, ordered=True)
    fig_box = px.box(
        rating_df.sort_values("position"),
        x="position",
        y="rating",
        color="position",
        title="Rating Distribution by Position",
        labels={"rating": "Player Rating", "position": "Position"},
        color_discrete_map=POSITION_COLORS,
    )
    style_fig(fig_box)

    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_donut, use_container_width=True)
    c2.plotly_chart(fig_box, use_container_width=True)

    # Avg stats grouped bar
    fig_avg = go.Figure()
    fig_avg.add_trace(go.Bar(
        name="Avg Goals", x=pos_agg["position"].astype(str), y=pos_agg["avg_goals"],
        marker_color=ACCENT_GREEN,
    ))
    fig_avg.add_trace(go.Bar(
        name="Avg Assists", x=pos_agg["position"].astype(str), y=pos_agg["avg_assists"],
        marker_color=SECONDARY_GREEN,
    ))
    fig_avg.add_trace(go.Bar(
        name="Avg Tackles", x=pos_agg["position"].astype(str), y=pos_agg["avg_tackles"],
        marker_color="#f9a825",
    ))
    fig_avg.update_layout(
        barmode="group",
        title="Average Goals, Assists & Tackles by Position",
        xaxis_title="Position",
        yaxis_title="Average",
    )
    style_fig(fig_avg)
    st.plotly_chart(fig_avg, use_container_width=True)


# ---------------------------------------------------------------------------
# Page 5 — Data Table
# ---------------------------------------------------------------------------
def render_data_table(df: pd.DataFrame):
    st.header("📋 Player Statistics Table")
    st.caption("⚠️ Synthetic data only — not real player statistics.")

    search = st.text_input("🔍 Search player name", placeholder="e.g. Lucas Silva")

    display_df = df.copy()
    if search.strip():
        mask = display_df["player_name"].str.contains(search.strip(), case=False, na=False)
        display_df = display_df[mask]

    total = len(df)
    shown = len(display_df)
    st.caption(f"Showing **{shown:,}** of **{total:,}** records")

    if display_df.empty:
        st.warning("⚠️ No players match the search term.")
    else:
        st.dataframe(
            display_df.reset_index(drop=True),
            use_container_width=True,
            height=500,
        )

    csv_bytes = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download filtered data as CSV",
        data=csv_bytes,
        file_name="football_players_filtered.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# Main app router
# ---------------------------------------------------------------------------
def main():
    df_all = load_data()
    df_filtered = build_sidebar(df_all)

    page = st.sidebar.radio(
        "📂 Navigate",
        ["📊 Overview", "🔍 Player Analysis", "🏟️ Team Analysis",
         "🎽 Position Analysis", "📋 Data Table"],
        index=0,
    )

    if page == "📊 Overview":
        render_overview(df_filtered, df_all)
    elif page == "🔍 Player Analysis":
        render_player_analysis(df_filtered)
    elif page == "🏟️ Team Analysis":
        render_team_analysis(df_filtered)
    elif page == "🎽 Position Analysis":
        render_position_analysis(df_filtered)
    elif page == "📋 Data Table":
        render_data_table(df_filtered)


if __name__ == "__main__":
    main()
