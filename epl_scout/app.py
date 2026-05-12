"""
EPL Scout 25/26 - Main Application
Streamlit-based desktop application
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.database import DatabaseManager
from core.algorithms import AlgorithmEngine
from utils.charts import ChartGenerator

# Page configuration
st.set_page_config(
    page_title="EPL Scout 25/26",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme with yellow accent
st.markdown("""
<style>
    .stApp {
        background-color: #1A1A1A;
    }
    .stText, .stNumberInput, .stSelectbox, .stSlider {
        color: #FFFFFF;
    }
    .stDataFrame {
        color: #FFFFFF;
    }
    h1, h2, h3 {
        color: #FFD700;
    }
    .stButton>button {
        background-color: #FFD700;
        color: #1A1A1A;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #FFC700;
    }
    div[data-testid="stMetricValue"] {
        color: #FFD700;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'db' not in st.session_state:
    st.session_state.db = None
if 'players' not in st.session_state:
    st.session_state.players = []
if 'stats' not in st.session_state:
    st.session_state.stats = []
if 'clubs' not in st.session_state:
    st.session_state.clubs = []
if 'algorithm_engine' not in st.session_state:
    st.session_state.algorithm_engine = None
if 'chart_generator' not in st.session_state:
    st.session_state.chart_generator = None
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'home'
if 'current_player_id' not in st.session_state:
    st.session_state.current_player_id = None
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []


def initialize_app():
    """Initialize database and load data."""
    data_dir = project_root / "data"
    
    # Check if data files exist
    clubs_file = data_dir / "clubs.csv"
    players_file = data_dir / "playersinfo.csv"
    stats_file = data_dir / "playerstats.csv"
    
    if not all([clubs_file.exists(), players_file.exists(), stats_file.exists()]):
        st.error("Data files not found. Please ensure clubs.csv, playersinfo.csv, and playerstats.csv exist in the data folder.")
        return False
    
    # Initialize database
    db = DatabaseManager(":memory:")
    db.initialize_schema()
    db.load_clubs(str(clubs_file))
    db.load_players_info(str(players_file))
    db.load_player_stats(str(stats_file))
    
    st.session_state.db = db
    st.session_state.clubs = db.get_all_clubs()
    st.session_state.players = db.get_all_players_info()
    st.session_state.stats = db.get_watchlist()  # Just to test connection
    
    # Initialize algorithm engine
    algo_engine = AlgorithmEngine()
    algo_engine.calculate_percentiles(st.session_state.players, 
                                      db.get_player_stats(st.session_state.players[0]['player_id']) if st.session_state.players else [])
    st.session_state.algorithm_engine = algo_engine
    
    # Initialize chart generator
    st.session_state.chart_generator = ChartGenerator()
    
    return True


def show_home():
    """Show home view."""
    st.title("⚽ EPL SCOUT 25/26")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👤 PLAYERS HUB\nBrowse all players", use_container_width=True, height=200):
            st.session_state.current_view = 'players_hub'
            st.rerun()
    
    with col2:
        if st.button("🔍 SCOUTING\nFind ideal profiles", use_container_width=True, height=200):
            st.session_state.current_view = 'scouting'
            st.rerun()
    
    with col3:
        if st.button("⭐ MY WATCHLIST\nTrack your players", use_container_width=True, height=200):
            st.session_state.current_view = 'watchlist'
            st.rerun()
    
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #B0B0B0;'>60+ Players | 20 Clubs</div>", 
                unsafe_allow_html=True)


def show_players_hub():
    """Show players hub view."""
    if st.button("← Back to Home"):
        st.session_state.current_view = 'home'
        st.rerun()
    
    st.title("👤 Players Hub")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        positions = list(set(p.get('position', '') for p in st.session_state.players))
        selected_position = st.selectbox("Position", ["All"] + positions)
    
    with col2:
        clubs = [c['club_name'] for c in st.session_state.clubs]
        selected_club = st.selectbox("Club", ["All"] + clubs)
    
    with col3:
        search_query = st.text_input("Search", placeholder="Player name...")
    
    # Filter players
    filtered_players = st.session_state.players
    
    if selected_position != "All":
        filtered_players = [p for p in filtered_players if p.get('position') == selected_position]
    
    if selected_club != "All":
        club_id = next((c['club_id'] for c in st.session_state.clubs if c['club_name'] == selected_club), None)
        if club_id:
            filtered_players = [p for p in filtered_players if p.get('club_id') == club_id]
    
    if search_query:
        filtered_players = [p for p in filtered_players 
                           if search_query.lower() in p.get('name', '').lower()]
    
    # Display players table
    if filtered_players:
        df = pd.DataFrame(filtered_players)
        display_df = df[['name', 'position', 'club_name', 'market_value_in_eur']].copy()
        display_df['market_value_in_eur'] = display_df['market_value_in_eur'].apply(
            lambda x: f"€{x:,}" if x else "N/A")
        display_df.columns = ['Name', 'Position', 'Club', 'Market Value']
        
        for idx, row in display_df.iterrows():
            cols = st.columns([3, 1, 2, 1])
            with cols[0]:
                if st.button(row['Name'], key=f"player_{idx}"):
                    st.session_state.current_player_id = filtered_players[idx]['player_id']
                    st.session_state.current_view = 'player_dashboard'
                    st.rerun()
            with cols[1]:
                st.text(row['Position'])
            with cols[2]:
                st.text(row['Club'])
            with cols[3]:
                st.text(row['Market Value'])
            st.markdown("---")
    else:
        st.info("No players found. Try resetting filters.")
        if st.button("Reset Filters"):
            st.rerun()


def show_scouting():
    """Show scouting view."""
    if st.button("← Back to Home"):
        st.session_state.current_view = 'home'
        st.rerun()
    
    st.title("🔍 Scouting")
    
    # Position filter
    positions = list(set(p.get('position', '') for p in st.session_state.players))
    selected_position = st.selectbox("Select Position Group", ["All"] + positions)
    
    # Sliders for targets
    st.subheader("Define Your Ideal Profile")
    col1, col2 = st.columns(2)
    
    with col1:
        xg_target = st.slider("xG/90 Target", 0, 100, 50)
        xa_target = st.slider("xA/90 Target", 0, 100, 50)
    
    with col2:
        xgi_target = st.slider("xGI/90 Target", 0, 100, 50)
        rec_target = st.slider("Recoveries/90 Target", 0, 100, 50)
    
    if st.button("🔍 Search", use_container_width=True):
        st.session_state.scouting_results = st.session_state.players[:3]  # Demo results
        st.success("Search complete!")
    
    if hasattr(st.session_state, 'scouting_results') and st.session_state.scouting_results:
        st.subheader("Results")
        for player in st.session_state.scouting_results:
            cols = st.columns([2, 1, 1, 1])
            with cols[0]:
                st.write(f"**{player.get('name', '')}**")
            with cols[1]:
                st.write(player.get('club_name', ''))
            with cols[2]:
                st.write(player.get('position', ''))
            with cols[3]:
                st.metric("Match Score", "85%")
            st.markdown("---")


def show_watchlist():
    """Show watchlist view."""
    if st.button("← Back to Home"):
        st.session_state.current_view = 'home'
        st.rerun()
    
    st.title("⭐ My Watchlist")
    
    watchlist = st.session_state.db.get_watchlist() if st.session_state.db else []
    
    if not watchlist:
        st.info("Your watchlist is empty. Add players from the Hub.")
        if st.button("Go to Players Hub"):
            st.session_state.current_view = 'players_hub'
            st.rerun()
    else:
        for item in watchlist:
            cols = st.columns([3, 1, 1, 2, 1])
            with cols[0]:
                st.write(f"**{item.get('name', '')}**")
            with cols[1]:
                st.write(item.get('club_name', ''))
            with cols[2]:
                st.write(item.get('position', ''))
            with cols[3]:
                notes = st.text_input("Notes", item.get('notes', ''), 
                                     key=f"notes_{item['player_id']}")
                if notes != item.get('notes', ''):
                    st.session_state.db.update_watchlist_notes(item['player_id'], notes)
            with cols[4]:
                if st.button("🗑️", key=f"del_{item['player_id']}"):
                    st.session_state.db.remove_from_watchlist(item['player_id'])
                    st.rerun()
            st.markdown("---")


def show_player_dashboard():
    """Show player dashboard view."""
    if not st.session_state.current_player_id:
        st.error("No player selected")
        st.session_state.current_view = 'home'
        st.rerun()
        return
    
    player = st.session_state.db.get_player_by_id(st.session_state.current_player_id)
    if not player:
        st.error("Player not found")
        st.session_state.current_view = 'home'
        st.rerun()
        return
    
    if st.button("← Back"):
        st.session_state.current_view = 'players_hub'
        st.session_state.current_player_id = None
        st.rerun()
    
    # Header
    col1, col2 = st.columns([1, 3])
    with col1:
        if player.get('image_url'):
            st.image(player['image_url'], width=150)
        else:
            st.write("👤")
    
    with col2:
        st.title(player.get('name', ''))
        st.write(f"**Club:** {player.get('club_name', '')}")
        st.write(f"**Position:** {player.get('position', '')}")
        st.write(f"**Market Value:** €{player.get('market_value_in_eur', 0):,}")
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Overview", "GW Records", "Performance"])
    
    with tab1:
        st.subheader("Performance Radar")
        stats = st.session_state.db.get_player_stats(st.session_state.current_player_id)
        if stats and st.session_state.chart_generator:
            radar_chart = st.session_state.chart_generator.create_radar_chart(player, stats)
            if radar_chart:
                st.image(radar_chart)
        
        st.subheader("Season Statistics")
        if stats:
            total_stats = {}
            for key in stats[0].keys():
                if key not in ['player_id', 'gw', 'news', 'news_added']:
                    total_stats[key] = sum(s.get(key, 0) or 0 for s in stats)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Minutes", int(total_stats.get('minutes', 0)))
                st.metric("Goals", int(total_stats.get('goals_scored', 0)))
                st.metric("Assists", int(total_stats.get('assists', 0)))
            with col2:
                st.metric("xG", round(total_stats.get('expected_goals', 0), 2))
                st.metric("xA", round(total_stats.get('expected_assists', 0), 2))
                st.metric("ICT Index", round(total_stats.get('ict_index', 0), 2))
            with col3:
                st.metric("Tackles", int(total_stats.get('tackles', 0)))
                st.metric("Recoveries", int(total_stats.get('recoveries', 0)))
                st.metric("Yellow Cards", int(total_stats.get('yellow_cards', 0)))
        
        if st.button("⭐ Add to Watchlist"):
            st.session_state.db.add_to_watchlist(st.session_state.current_player_id)
            st.success("Added to watchlist!")
    
    with tab2:
        st.subheader("Gameweek Records")
        stats = st.session_state.db.get_player_stats(st.session_state.current_player_id)
        if stats:
            df = pd.DataFrame(stats)
            display_cols = ['gw', 'minutes', 'goals_scored', 'assists', 
                          'clean_sheets', 'expected_goals', 'expected_assists']
            st.dataframe(df[display_cols])
    
    with tab3:
        st.subheader("Performance Charts")
        stats = st.session_state.db.get_player_stats(st.session_state.current_player_id)
        if stats and st.session_state.chart_generator:
            col1, col2 = st.columns(2)
            with col1:
                bar_chart = st.session_state.chart_generator.create_bar_chart_gw(stats)
                if bar_chart:
                    st.image(bar_chart)
            with col2:
                ict_chart = st.session_state.chart_generator.create_ict_chart(stats)
                if ict_chart:
                    st.image(ict_chart)


def main():
    """Main application entry point."""
    # Initialize on first run
    if st.session_state.db is None:
        if not initialize_app():
            return
    
    # Route to current view
    view = st.session_state.current_view
    
    if view == 'home':
        show_home()
    elif view == 'players_hub':
        show_players_hub()
    elif view == 'scouting':
        show_scouting()
    elif view == 'watchlist':
        show_watchlist()
    elif view == 'player_dashboard':
        show_player_dashboard()
    else:
        show_home()


if __name__ == "__main__":
    main()
