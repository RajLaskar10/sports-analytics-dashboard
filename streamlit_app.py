"""
2018 FIFA World Cup Analytics Dashboard
Connects to Supabase and visualises pre-computed KPI views.
"""

import os
from urllib.parse import quote_plus
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def _get_engine():
    """Build SQLAlchemy engine from Streamlit secrets or env vars."""
    try:
        cfg = st.secrets["supabase"]
        host = cfg["host"]
        port = cfg["port"]
        database = cfg["database"]
        user = cfg["user"]
        password = cfg["password"]
    except (KeyError, FileNotFoundError):
        host = os.environ.get("DB_HOST", "localhost")
        port = os.environ.get("DB_PORT", "5432")
        database = os.environ.get("DB_NAME", "postgres")
        user = os.environ.get("DB_USER", "postgres")
        password = os.environ.get("DB_PASSWORD", "")

    # port 6543 = Supabase transaction pooler (used on Streamlit Cloud)
    # port 5432 = direct connection (used locally)
    sslmode = "prefer" if int(port) == 6543 else "require"
    url = f"postgresql+psycopg2://{user}:{quote_plus(password)}@{host}:{port}/{database}?sslmode={sslmode}"
    return create_engine(url, pool_pre_ping=True)


@st.cache_resource
def get_engine():
    return _get_engine()


@st.cache_data(ttl=3600)
def query(sql: str) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="2018 World Cup Analytics",
    page_icon="⚽",
    layout="wide",
)

st.title("⚽ 2018 FIFA World Cup Analytics")
st.caption("Data: StatsBomb open data · Database: Supabase · Source: github.com/statsbomb/open-data")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Tournament Overview",
    "🎯 Player Shooting",
    "🎯 Player Passing",
    "⚡ Pressing",
])

# ── Tab 1: Tournament Overview ──────────────────────────────────────────────

with tab1:
    xg_df = query("SELECT * FROM match_xg_summary ORDER BY match_date")

    total_matches = len(xg_df)
    total_goals = int(xg_df["home_goals"].sum() + xg_df["away_goals"].sum())
    avg_xg = round((xg_df["home_xg"].sum() + xg_df["away_xg"].sum()) / total_matches, 2)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Matches", total_matches)
    c2.metric("Total Goals", total_goals)
    c3.metric("Avg xG per Match", avg_xg)

    st.subheader("Team xG vs Actual Goals")

    # Aggregate by home team then away team
    home = xg_df[["home_team", "home_xg", "home_goals"]].rename(
        columns={"home_team": "team", "home_xg": "xg", "home_goals": "goals"}
    )
    away = xg_df[["away_team", "away_xg", "away_goals"]].rename(
        columns={"away_team": "team", "away_xg": "xg", "away_goals": "goals"}
    )
    team_agg = (
        pd.concat([home, away])
        .groupby("team", as_index=False)
        .sum()
        .sort_values("xg", ascending=False)
    )

    fig = go.Figure()
    fig.add_bar(x=team_agg["team"], y=team_agg["xg"], name="xG (expected)", marker_color="#636EFA")
    fig.add_bar(x=team_agg["team"], y=team_agg["goals"], name="Goals (actual)", marker_color="#EF553B")
    fig.update_layout(barmode="group", xaxis_tickangle=-45, height=420, margin=dict(b=120))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Match xG vs Result — biggest gaps first")
    display = xg_df[["match_date", "home_team", "away_team",
                       "home_xg", "away_xg", "home_goals", "away_goals", "total_xg_diff"]].copy()
    display["abs_diff"] = display["total_xg_diff"].abs()
    display = display.sort_values("abs_diff", ascending=False).drop(columns="abs_diff")
    display.columns = ["Date", "Home", "Away", "Home xG", "Away xG",
                        "Home Goals", "Away Goals", "xG Diff"]
    st.dataframe(display, use_container_width=True, hide_index=True)


# ── Tab 2: Player Shooting ───────────────────────────────────────────────────

with tab2:
    shoot_df = query("SELECT * FROM player_shooting_stats ORDER BY total_xg DESC")

    teams = ["All teams"] + sorted(shoot_df["team"].unique().tolist())
    selected_team = st.selectbox("Filter by team", teams, key="shoot_team")
    if selected_team != "All teams":
        shoot_df = shoot_df[shoot_df["team"] == selected_team]

    st.subheader("xG vs Goals — each dot is a player")
    st.caption("Players above the diagonal scored more than expected (overperformed xG); below = underperformed.")

    fig = px.scatter(
        shoot_df,
        x="total_xg",
        y="goals",
        hover_name="player_name",
        hover_data={"team": True, "total_shots": True, "total_xg": ":.2f"},
        color="team",
        labels={"total_xg": "Total xG", "goals": "Goals"},
        height=460,
    )
    max_val = max(shoot_df["total_xg"].max(), shoot_df["goals"].max()) + 0.5
    fig.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val,
                  line=dict(dash="dash", color="grey", width=1))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 10 Players by xG")
    top10 = shoot_df.head(10)
    fig2 = go.Figure()
    fig2.add_bar(x=top10["player_name"], y=top10["total_xg"], name="xG", marker_color="#636EFA")
    fig2.add_bar(x=top10["player_name"], y=top10["goals"], name="Goals", marker_color="#EF553B")
    fig2.update_layout(barmode="group", xaxis_tickangle=-35, height=380, margin=dict(b=100))
    st.plotly_chart(fig2, use_container_width=True)


# ── Tab 3: Player Passing ────────────────────────────────────────────────────

with tab3:
    pass_df = query("SELECT * FROM player_passing_stats")
    creators_df = query("SELECT * FROM top_chance_creators ORDER BY key_passes DESC")

    teams_p = ["All teams"] + sorted(pass_df["team"].unique().tolist())
    selected_team_p = st.selectbox("Filter by team", teams_p, key="pass_team")
    if selected_team_p != "All teams":
        pass_df = pass_df[pass_df["team"] == selected_team_p]
        creators_df = creators_df[creators_df["team"] == selected_team_p]

    st.subheader("Pass Completion Rate — top 20 players (min. 50 passes)")
    completion = (
        pass_df[pass_df["total_passes"] >= 50]
        .sort_values("completion_rate_pct", ascending=False)
        .head(20)
    )
    fig3 = px.bar(
        completion,
        x="player_name",
        y="completion_rate_pct",
        color="team",
        labels={"player_name": "Player", "completion_rate_pct": "Completion %"},
        height=400,
    )
    fig3.update_layout(xaxis_tickangle=-40, margin=dict(b=110))
    st.plotly_chart(fig3, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Through Balls Leaderboard")
        through = pass_df.sort_values("through_balls", ascending=False).head(15)
        fig4 = px.bar(through, x="player_name", y="through_balls",
                      color="team", height=360,
                      labels={"player_name": "Player", "through_balls": "Through Balls"})
        fig4.update_layout(xaxis_tickangle=-40, margin=dict(b=110))
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        st.subheader("Switches Leaderboard")
        switches = pass_df.sort_values("switches", ascending=False).head(15)
        fig5 = px.bar(switches, x="player_name", y="switches",
                      color="team", height=360,
                      labels={"player_name": "Player", "switches": "Switches"})
        fig5.update_layout(xaxis_tickangle=-40, margin=dict(b=110))
        st.plotly_chart(fig5, use_container_width=True)


# ── Tab 4: Pressing ──────────────────────────────────────────────────────────

with tab4:
    press_df = query("SELECT * FROM team_pressing_stats ORDER BY avg_pressures_per_match DESC")

    st.subheader("Pressing Intensity — average pressures per match")
    fig6 = px.bar(
        press_df,
        x="team",
        y="avg_pressures_per_match",
        color="avg_pressures_per_match",
        color_continuous_scale="Blues",
        labels={"team": "Team", "avg_pressures_per_match": "Avg Pressures / Match"},
        height=420,
    )
    fig6.update_layout(xaxis_tickangle=-45, margin=dict(b=120), coloraxis_showscale=False)
    st.plotly_chart(fig6, use_container_width=True)

    st.subheader("Pressing Success Rate by Team")
    st.caption(
        "Estimated: a pressure counts as successful if the same team wins the ball back "
        "within 5 events. This is a rough proxy — see docs/kpi-definitions.md for caveats."
    )
    press_sorted = press_df.sort_values("press_success_rate_pct", ascending=False)
    fig7 = px.bar(
        press_sorted,
        x="team",
        y="press_success_rate_pct",
        color="press_success_rate_pct",
        color_continuous_scale="Greens",
        labels={"team": "Team", "press_success_rate_pct": "Success Rate (%)"},
        height=420,
    )
    fig7.update_layout(xaxis_tickangle=-45, margin=dict(b=120), coloraxis_showscale=False)
    st.plotly_chart(fig7, use_container_width=True)

    with st.expander("Raw pressing data"):
        st.dataframe(press_df, use_container_width=True, hide_index=True)
