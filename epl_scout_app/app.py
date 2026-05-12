"""
Main Streamlit Application for EPL Scout 25/26
Orchestrates all views and manages application state.
"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import DatabaseManager
from core.algorithms import AlgorithmManager
from utils.charts import ChartGenerator

# Page configuration
st.set_page_config(
    page_title="EPL Scout 25/26",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme and yellow accent
st.markdown("""
<style>
    .stApp {
        background-color: #1A1A1A;
        color: #FFFFFF;
    }
    .stButton > button {
        background-color: #FFD700;
        color: #1A1A1A;
        font-weight: bold;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
    }
    .stButton > button:hover {
        background-color: #FFC700;
    }
    .stTextInput > div > div > input {
        background-color: #2D2D2D;
        color: #FFFFFF;
        border: 1px solid #4A4A4A;
    }
    .stSelectbox > div > div > select {
        background-color: #2D2D2D;
        color: #FFFFFF;
        border: 1px solid #4A4A4A;
    }
    .stSlider > div {
        color: #FFFFFF;
    }
    h1, h2, h3 {
        color: #FFD700 !important;
    }
    [data-testid="stMetricValue"] {
        color: #FFD700;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state for global application state."""
    if "current_view" not in st.session_state:
        st.session_state.current_view = "home"
    if "current_player_id" not in st.session_state:
        st.session_state.current_player_id = None
    if "previous_view" not in st.session_state:
        st.session_state.previous_view = "home"
    if "db" not in st.session_state:
        st.session_state.db = DatabaseManager()
        st.session_state.db.load_csv_data("data")
    if "algorithms" not in st.session_state:
        st.session_state.algorithms = AlgorithmManager()
    if "charts" not in st.session_state:
        st.session_state.charts = ChartGenerator()


def navigate_to(view: str, player_id: str = None):
    """Navigate to a specific view."""
    st.session_state.previous_view = st.session_state.current_view
    st.session_state.current_view = view
    if player_id:
        st.session_state.current_player_id = player_id


def render_home():
    """Render Home View with Bento Grid layout."""
    st.title("⚽ EPL Scout 25/26")
    st.markdown("### Main Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background-color: #2D2D2D; padding: 30px; border-radius: 10px; text-align: center; height: 200px; display: flex; flex-direction: column; justify-content: center;">
            <h2 style="color: #FFD700;">👥 PLAYERS HUB</h2>
            <p>Browse all players</p>
            <p style="color: #B0B0B0;">6+ Players</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Players Hub", key="hub_btn", use_container_width=True):
            navigate_to("players_hub")
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="background-color: #2D2D2D; padding: 30px; border-radius: 10px; text-align: center; height: 200px; display: flex; flex-direction: column; justify-content: center;">
            <h2 style="color: #FFD700;">🔍 SCOUTING</h2>
            <p>Find ideal players</p>
            <p style="color: #B0B0B0;">Role Search</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Scouting", key="scout_btn", use_container_width=True):
            navigate_to("scouting")
            st.rerun()
    
    with col3:
        st.markdown("""
        <div style="background-color: #2D2D2D; padding: 30px; border-radius: 10px; text-align: center; height: 200px; display: flex; flex-direction: column; justify-content: center;">
            <h2 style="color: #FFD700;">⭐ MY WATCHLIST</h2>
            <p>Track your prospects</p>
            <p style="color: #B0B0B0;">Personal List</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Watchlist", key="watch_btn", use_container_width=True):
            navigate_to("watchlist")
            st.rerun()


def render_players_hub():
    """Render Players Hub View with filters and results table."""
    if st.button("← Back to Home"):
        navigate_to("home")
        st.rerun()
    
    st.title("👥 Players Hub")
    
    # Filters row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        positions = ["All", "Goalkeeper", "Defender", "Midfielder", "Forward"]
        position_filter = st.selectbox("Position", positions, key="pos_filter")
    
    with col2:
        clubs = st.session_state.db.get_all_clubs()
        club_options = ["All"] + [c["club_name"] for c in clubs]
        club_filter = st.selectbox("Club", club_options, key="club_filter")
    
    with col3:
        market_range = st.slider("Market Value (€M)", 0, 100, (0, 100), key="market_filter")
    
    with col4:
        search_query = st.text_input("Search", "", key="search_input")
    
    # Build filters dict
    filters = {}
    if position_filter != "All":
        filters["position"] = position_filter
    if club_filter != "All":
        club_id = next((c["club_id"] for c in clubs if c["club_name"] == club_filter), None)
        if club_id:
            filters["club_id"] = club_id
    filters["min_market_value"] = market_range[0] * 1_000_000
    filters["max_market_value"] = market_range[1] * 1_000_000
    if search_query:
        filters["search_query"] = search_query
    
    # Get filtered players
    players = st.session_state.db.search_players(filters)
    
    if not players:
        st.warning("No players found matching your criteria.")
        if st.button("Reset Filters"):
            st.session_state.pos_filter = "All"
            st.session_state.club_filter = "All"
            st.session_state.market_filter = (0, 100)
            st.session_state.search_input = ""
            st.rerun()
    else:
        # Display results table
        st.write(f"Found {len(players)} players")
        
        for player in players:
            cols = st.columns([3, 1, 2, 2])
            cols[0].write(f"**{player['name']}**")
            cols[1].write(player.get("position", "N/A"))
            cols[2].write(player.get("club_name", "N/A"))
            mv = player.get("market_value_in_eur", 0) or 0
            cols[3].write(f"€{mv/1_000_000:.1f}M")
            
            if cols[0].button("View Profile", key=f"view_{player['player_id']}"):
                navigate_to("player_dashboard", player["player_id"])
                st.rerun()
            
            st.divider()


def render_scouting():
    """Render Scouting View with role search."""
    if st.button("← Back to Home"):
        navigate_to("home")
        st.rerun()
    
    st.title("🔍 Scouting - Role Search")
    
    # Section 1: Position Group
    position_group = st.selectbox(
        "Select Position Group",
        ["GK", "DEF", "MID", "FWD"],
        key="scout_position"
    )
    
    # Section 2: Ideal Profile Sliders
    st.subheader("Define Your Ideal Profile")
    col1, col2 = st.columns(2)
    
    with col1:
        xg_target = st.slider("xG/90 Target (%)", 50, 95, 70, key="xg_slider")
        xa_target = st.slider("xA/90 Target (%)", 50, 95, 70, key="xa_slider")
    
    with col2:
        xgi_target = st.slider("xGI/90 Target (%)", 50, 95, 70, key="xgi_slider")
        rec_target = st.slider("Recoveries/90 Target (%)", 50, 95, 70, key="rec_slider")
    
    # Section 3: Hard Filters
    with st.expander("Hard Filters"):
        col1, col2, col3 = st.columns(3)
        with col1:
            age_min = st.number_input("Min Age", 16, 40, 18, key="age_min")
            age_max = st.number_input("Max Age", 16, 40, 35, key="age_max")
        with col2:
            mv_min = st.number_input("Min Value (€M)", 0, 100, 0, key="mv_min")
            mv_max = st.number_input("Max Value (€M)", 0, 100, 100, key="mv_max")
        with col3:
            contract_year = st.number_input("Contract Year", 2025, 2030, 2025, key="contract_yr")
    
    if st.button("🔍 SEARCH", use_container_width=True, key="search_btn"):
        # Get candidates
        candidates = st.session_state.db.get_players_for_scouting(position_group)
        
        # Build player stats dict
        all_stats = {}
        for p in candidates:
            stats = st.session_state.db.get_latest_player_stats(p["player_id"])
            if stats:
                all_stats[p["player_id"]] = stats
        
        # Run scouting algorithm
        targets = {
            "expected_goals_per_90": xg_target,
            "expected_assists_per_90": xa_target,
            "expected_goal_involvements_per_90": xgi_target,
            "recoveries": rec_target
        }
        
        hard_filters = {
            "min_age": age_min,
            "max_age": age_max,
            "min_market_value": mv_min * 1_000_000,
            "max_market_value": mv_max * 1_000_000,
            "contract_year": contract_year
        }
        
        results = st.session_state.algorithms.scout_players(
            candidates, all_stats, targets, hard_filters
        )
        
        # Store results in session
        st.session_state.scout_results = results
    
    # Display results
    if hasattr(st.session_state, "scout_results") and st.session_state.scout_results:
        st.subheader("Search Results")
        results = st.session_state.scout_results
        
        for i, player in enumerate(results[:10], 1):
            cols = st.columns([1, 3, 2, 1])
            cols[0].write(f"**#{i}**")
            cols[1].write(f"**{player['name']}**")
            cols[2].write(player.get("club_name", "N/A"))
            score = player.get("match_score", 0)
            cols[3].write(f"**{score:.1f}%**")
            
            if cols[1].button("View Profile", key=f"scout_view_{player['player_id']}"):
                navigate_to("player_dashboard", player["player_id"])
                st.rerun()
            
            st.divider()


def render_watchlist():
    """Render Watchlist View."""
    if st.button("← Back to Home"):
        navigate_to("home")
        st.rerun()
    
    st.title("⭐ My Watchlist")
    
    # Top toolbar
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_wl = st.text_input("Search Watchlist", "", key="wl_search")
    
    with col2:
        wl_players = st.session_state.db.get_watchlist()
        if wl_players:
            if st.button("🗑️ Delete All", key="del_all"):
                st.session_state.db.clear_watchlist()
                st.rerun()
    
    if not wl_players:
        st.info("Your watchlist is empty. Add players from the Hub.")
        if st.button("Go to Players Hub"):
            navigate_to("players_hub")
            st.rerun()
    else:
        # Filter watchlist
        if search_wl:
            wl_players = [p for p in wl_players if search_wl.lower() in p["name"].lower()]
        
        for player in wl_players:
            cols = st.columns([3, 2, 1, 2, 1, 1])
            
            cols[0].write(f"**{player['name']}**")
            cols[1].write(player.get("club_name", "N/A"))
            cols[2].write(player.get("position", "N/A"))
            
            # Notes input
            notes = cols[3].text_input("Notes", player.get("notes", ""), key=f"notes_{player['player_id']}")
            if notes != player.get("notes", ""):
                st.session_state.db.update_watchlist_notes(player["player_id"], notes)
            
            # Rating stars
            rating = player.get("rating", 0) or 0
            new_rating = cols[4].selectbox("Rating", list(range(6)), index=rating, key=f"rate_{player['player_id']}")
            if new_rating != rating:
                st.session_state.db.update_watchlist_rating(player["player_id"], new_rating)
            
            # Delete button
            if cols[5].button("🗑️", key=f"del_{player['player_id']}"):
                st.session_state.db.remove_from_watchlist(player["player_id"])
                st.rerun()
            
            if cols[0].button("View Profile", key=f"wl_view_{player['player_id']}"):
                navigate_to("player_dashboard", player["player_id"])
                st.rerun()
            
            st.divider()


def render_player_dashboard():
    """Render Player Dashboard View with tabs."""
    player_id = st.session_state.current_player_id
    if not player_id:
        st.error("No player selected")
        if st.button("Back to Home"):
            navigate_to("home")
            st.rerun()
        return
    
    player = st.session_state.db.get_player_by_id(player_id)
    if not player:
        st.error("Player not found")
        if st.button("Back to Home"):
            navigate_to("home")
            st.rerun()
        return
    
    # Header
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back"):
            navigate_to(st.session_state.previous_view)
            st.rerun()
    
    with col2:
        st.title(player["name"])
        st.write(f"{player.get('position', 'N/A')} | {player.get('club_name', 'N/A')}")
    
    # Get stats
    gw_stats = st.session_state.db.get_player_stats(player_id)
    latest_stats = st.session_state.db.get_latest_player_stats(player_id) or {}
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Overview", "GW Records", "Performance"])
    
    with tab1:
        render_overview_tab(player, latest_stats, gw_stats)
    
    with tab2:
        render_gw_records_tab(player, gw_stats)
    
    with tab3:
        render_performance_tab(player, gw_stats)


def render_overview_tab(player: dict, stats: dict, gw_stats: list):
    """Render Overview Tab content."""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Player image
        image_url = player.get("image_url", "")
        if image_url:
            st.image(image_url, width=200)
        else:
            st.markdown("👤 No Image")
        
        # Info grid
        st.markdown("### Player Info")
        st.write(f"**Nationality:** {player.get('country_of_citizenship', 'N/A')}")
        st.write(f"**Age:** {calculate_age(player.get('date_of_birth'))}")
        st.write(f"**Position:** {player.get('position', 'N/A')}")
        st.write(f"**Club:** {player.get('club_name', 'N/A')}")
        st.write(f"**Contract:** {player.get('contract_expiration_date', 'N/A')}")
        mv = player.get("market_value_in_eur", 0) or 0
        st.write(f"**Market Value:** €{mv/1_000_000:.1f}M")
        
        # Add to watchlist button
        in_watchlist = st.session_state.db.is_in_watchlist(player["player_id"])
        if in_watchlist:
            st.success("✓ In Watchlist")
        else:
            if st.button("⭐ Add to Watchlist", use_container_width=True):
                st.session_state.db.add_to_watchlist(player["player_id"])
                st.rerun()
    
    with col2:
        # Radar chart
        if stats:
            radar_img = st.session_state.charts.create_radar_chart(
                player["name"], stats, player.get("position", "")
            )
            st.image(radar_img, caption="Performance Radar")
            
            # Find Similar button
            if st.button("🔍 Find Similar Players"):
                similar = st.session_state.algorithms.find_similar_players(
                    player["player_id"],
                    stats,
                    player.get("position", ""),
                    st.session_state.db.get_all_players(),
                    {p["player_id"]: st.session_state.db.get_latest_player_stats(p["player_id"]) or {} 
                     for p in st.session_state.db.get_all_players()}
                )
                st.session_state.similar_players = similar
                st.rerun()
        
        # Show similar players if available
        if hasattr(st.session_state, "similar_players") and st.session_state.similar_players:
            st.subheader("Similar Players")
            for sim in st.session_state.similar_players:
                cols = st.columns([3, 2, 1])
                cols[0].write(f"**{sim['name']}**")
                cols[1].write(sim.get("club_name", "N/A"))
                cols[2].write(f"**{sim['match_score']:.1f}%**")
            if st.button("Close Similar Players"):
                del st.session_state.similar_players
                st.rerun()
        
        # Season statistics
        st.subheader("Season Statistics")
        if stats:
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Minutes", int(stats.get("minutes", 0) or 0))
                st.metric("Goals", int(stats.get("goals_scored", 0) or 0))
                st.metric("Assists", int(stats.get("assists", 0) or 0))
                st.metric("xG", f"{stats.get('expected_goals', 0):.2f}")
                st.metric("xA", f"{stats.get('expected_assists', 0):.2f}")
            with col_b:
                st.metric("ICT Index", f"{stats.get('ict_index', 0):.1f}")
                st.metric("Influence", f"{stats.get('influence', 0):.1f}")
                st.metric("Creativity", f"{stats.get('creativity', 0):.1f}")
                st.metric("Threat", f"{stats.get('threat', 0):.1f}")


def render_gw_records_tab(player: dict, gw_stats: list):
    """Render GW Records Tab content."""
    if not gw_stats:
        st.info("No gameweek records available")
        return
    
    # Summary
    total_mins = sum(s.get("minutes", 0) or 0 for s in gw_stats)
    total_goals = sum(s.get("goals_scored", 0) or 0 for s in gw_stats)
    total_assists = sum(s.get("assists", 0) or 0 for s in gw_stats)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Games Played", len(gw_stats))
    col2.metric("Total Goals", total_goals)
    col3.metric("Total Assists", total_assists)
    
    st.divider()
    
    # Table
    st.dataframe({
        "GW": [s.get("gw", 0) for s in gw_stats],
        "Min": [int(s.get("minutes", 0) or 0) for s in gw_stats],
        "G": [int(s.get("goals_scored", 0) or 0) for s in gw_stats],
        "A": [int(s.get("assists", 0) or 0) for s in gw_stats],
        "CS": [int(s.get("clean_sheets", 0) or 0) for s in gw_stats],
        "xG": [f"{s.get('expected_goals', 0):.2f}" for s in gw_stats],
        "xA": [f"{s.get('expected_assists', 0):.2f}" for s in gw_stats],
        "ICT": [f"{s.get('ict_index', 0):.1f}" for s in gw_stats]
    }, use_container_width=True)


def render_performance_tab(player: dict, gw_stats: list):
    """Render Performance Tab content."""
    if not gw_stats:
        st.info("No performance data available")
        return
    
    # Chart 1: Minutes per GW
    minutes_chart = st.session_state.charts.create_gw_minutes_chart(player["name"], gw_stats)
    st.image(minutes_chart, caption="Minutes per Gameweek")
    
    # Chart 2: Goals vs xG
    goals_chart = st.session_state.charts.create_cumulative_line_chart(
        player["name"], gw_stats, "goals_scored", "expected_goals", "Goals vs Expected Goals"
    )
    st.image(goals_chart, caption="Cumulative Goals vs xG")
    
    # Chart 3: Assists vs xA
    assists_chart = st.session_state.charts.create_cumulative_line_chart(
        player["name"], gw_stats, "assists", "expected_assists", "Assists vs Expected Assists"
    )
    st.image(assists_chart, caption="Cumulative Assists vs xA")
    
    # Chart 4: ICT Components
    ict_chart = st.session_state.charts.create_ict_chart(player["name"], gw_stats)
    st.image(ict_chart, caption="ICT Index Components")
    
    # Chart 5: GK only
    if player.get("position") == "Goalkeeper":
        gk_chart = st.session_state.charts.create_gk_saves_chart(player["name"], gw_stats)
        st.image(gk_chart, caption="Saves vs Goals Conceded")


def calculate_age(birth_date_str: str) -> int:
    """Calculate age from birth date string."""
    if not birth_date_str:
        return 0
    try:
        from datetime import datetime
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age
    except Exception:
        return 0


# ==================== Main App ====================

def main():
    """Main application entry point."""
    initialize_session_state()
    
    # Route to current view
    view = st.session_state.current_view
    
    if view == "home":
        render_home()
    elif view == "players_hub":
        render_players_hub()
    elif view == "scouting":
        render_scouting()
    elif view == "watchlist":
        render_watchlist()
    elif view == "player_dashboard":
        render_player_dashboard()
    else:
        render_home()


if __name__ == "__main__":
    main()
