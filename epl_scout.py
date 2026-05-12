"""
EPL Scout 25/26 - Main Application
Single-file Streamlit app với modular architecture
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import sqlite3
import os
from io import BytesIO
import base64
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections import polar
from matplotlib.projections.polar import PolarAxes
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D

# ============================================================================
# CONFIGURATION
# ============================================================================
DB_PATH = "epl_scout.db"
DATA_DIR = "data"
COLORS = {
    "bg": "#1A1A1A",
    "surface": "#2D2D2D",
    "primary": "#FFD700",
    "secondary": "#4A4A4A",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B0B0B0",
    "success": "#4CAF50",
    "error": "#F44336",
}

st.set_page_config(
    page_title="EPL Scout 25/26",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# DATABASE LAYER (Data Access Layer)
# ============================================================================
class DatabaseManager:
    """Quản lý database - chỉ làm việc với SQL, không có UI logic"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Khởi tạo database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clubs (
                club_id VARCHAR(2) PRIMARY KEY,
                club_name VARCHAR(50) NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playersinfo (
                player_id VARCHAR(4) PRIMARY KEY,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                name VARCHAR(100),
                last_season INTEGER,
                club_id VARCHAR(2),
                country_of_citizenship VARCHAR(50),
                date_of_birth DATE,
                sub_position VARCHAR(50),
                position VARCHAR(20),
                foot VARCHAR(10),
                height_in_cm INTEGER,
                contract_expiration_date DATE,
                image_url TEXT,
                current_club_name VARCHAR(100),
                market_value_in_eur INTEGER,
                FOREIGN KEY (club_id) REFERENCES clubs(club_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playerstats (
                player_id VARCHAR(4),
                gw INTEGER,
                expected_goals REAL,
                expected_assists REAL,
                expected_goal_involvements REAL,
                expected_goals_conceded REAL,
                expected_goals_per_90 REAL,
                expected_assists_per_90 REAL,
                expected_goal_involvements_per_90 REAL,
                expected_goals_conceded_per_90 REAL,
                influence REAL,
                creativity REAL,
                threat REAL,
                ict_index REAL,
                news TEXT,
                news_added DATE,
                minutes REAL,
                goals_scored REAL,
                assists REAL,
                clean_sheets REAL,
                goals_conceded REAL,
                own_goals REAL,
                penalties_saved REAL,
                penalties_missed REAL,
                yellow_cards REAL,
                red_cards REAL,
                saves REAL,
                starts REAL,
                defensive_contribution REAL,
                saves_per_90 REAL,
                clean_sheets_per_90 REAL,
                goals_conceded_per_90 REAL,
                starts_per_90 REAL,
                defensive_contribution_per_90 REAL,
                tackles REAL,
                clearances_blocks_interceptions REAL,
                recoveries REAL,
                PRIMARY KEY (player_id, gw),
                FOREIGN KEY (player_id) REFERENCES playersinfo(player_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                watchlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id VARCHAR(4) UNIQUE,
                rating INTEGER DEFAULT 0 CHECK(rating BETWEEN 1 AND 5),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES playersinfo(player_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def load_csv_to_db(self, csv_path: str, table_name: str):
        """Load CSV file vào database table"""
        if not os.path.exists(csv_path):
            return False
            
        df = pd.read_csv(csv_path)
        conn = self._get_connection()
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()
        return True
    
    def get_all_clubs(self) -> list:
        """Lấy danh sách tất cả clubs"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT club_id, club_name FROM clubs")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_all_players(self) -> list:
        """Lấy danh sách tất cả players với info cơ bản"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.player_id, p.name, p.position, p.club_id, 
                   p.market_value_in_eur, c.club_name, p.image_url
            FROM playersinfo p
            LEFT JOIN clubs c ON p.club_id = c.club_id
        """)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_player_info(self, player_id: str) -> dict:
        """Lấy thông tin chi tiết của một player"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, c.club_name
            FROM playersinfo p
            LEFT JOIN clubs c ON p.club_id = c.club_id
            WHERE p.player_id = ?
        """, (player_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else {}
    
    def get_player_stats(self, player_id: str) -> list:
        """Lấy tất cả stats của một player theo GW"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM playerstats WHERE player_id = ? ORDER BY gw
        """, (player_id,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_player_latest_stats(self, player_id: str) -> dict:
        """Lấy stats mới nhất của player"""
        stats = self.get_player_stats(player_id)
        if stats:
            # Group by và lấy total
            total_minutes = sum(s.get('minutes', 0) for s in stats)
            if total_minutes < 450:
                return {}
            
            # Lấy stats mới nhất hoặc tính total
            latest = stats[-1] if stats else {}
            total = {
                'goals_scored': sum(s.get('goals_scored', 0) for s in stats),
                'assists': sum(s.get('assists', 0) for s in stats),
                'minutes': total_minutes,
                'xG_per_90': latest.get('expected_goals_per_90', 0),
                'xA_per_90': latest.get('expected_assists_per_90', 0),
                'xGI_per_90': latest.get('expected_goal_involvements_per_90', 0),
                'recoveries_per_90': (sum(s.get('recoveries', 0) for s in stats) / total_minutes * 90) if total_minutes > 0 else 0,
            }
            total.update(latest)
            return total
        return {}
    
    def search_players(self, filters: dict) -> list:
        """Search players với filters"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT p.player_id, p.name, p.position, p.club_id, 
                   p.market_value_in_eur, c.club_name, p.image_url
            FROM playersinfo p
            LEFT JOIN clubs c ON p.club_id = c.club_id
            WHERE 1=1
        """
        params = []
        
        if filters.get('position'):
            query += " AND p.position = ?"
            params.append(filters['position'])
        
        if filters.get('club_id'):
            query += " AND p.club_id = ?"
            params.append(filters['club_id'])
        
        if filters.get('min_value'):
            query += " AND p.market_value_in_eur >= ?"
            params.append(filters['min_value'])
        
        if filters.get('max_value'):
            query += " AND p.market_value_in_eur <= ?"
            params.append(filters['max_value'])
        
        if filters.get('search'):
            query += " AND (p.name LIKE ? OR p.first_name LIKE ? OR p.last_name LIKE ?)"
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term, search_term])
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def add_to_watchlist(self, player_id: str, rating: int = 0, notes: str = "") -> bool:
        """Thêm player vào watchlist"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO watchlist (player_id, rating, notes)
                VALUES (?, ?, ?)
            """, (player_id, rating, notes))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding to watchlist: {e}")
            return False
    
    def get_watchlist(self) -> list:
        """Lấy danh sách watchlist với player info"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT w.*, p.name, p.position, p.club_id, c.club_name
            FROM watchlist w
            JOIN playersinfo p ON w.player_id = p.player_id
            LEFT JOIN clubs c ON p.club_id = c.club_id
            ORDER BY w.created_at DESC
        """)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def update_watchlist_rating(self, player_id: str, rating: int) -> bool:
        """Cập nhật rating trong watchlist"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE watchlist SET rating = ? WHERE player_id = ?", (rating, player_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating rating: {e}")
            return False
    
    def update_watchlist_notes(self, player_id: str, notes: str) -> bool:
        """Cập nhật notes trong watchlist"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE watchlist SET notes = ? WHERE player_id = ?", (notes, player_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating notes: {e}")
            return False
    
    def remove_from_watchlist(self, player_id: str) -> bool:
        """Xóa player khỏi watchlist"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watchlist WHERE player_id = ?", (player_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error removing from watchlist: {e}")
            return False
    
    def clear_watchlist(self) -> bool:
        """Xóa toàn bộ watchlist"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watchlist")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error clearing watchlist: {e}")
            return False


# ============================================================================
# ALGORITHMS LAYER (Business Logic Layer)
# ============================================================================
class Algorithms:
    """Các thuật toán xử lý - không phụ thuộc vào UI hay DB trực tiếp"""
    
    @staticmethod
    def calculate_percentiles(data: list, key: str) -> dict:
        """Tính percentile cho một stat"""
        values = [item.get(key, 0) for item in data if item.get(key, 0) is not None]
        if not values:
            return {}
        
        percentiles = {}
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        for i, item in enumerate(data):
            val = item.get(key, 0)
            if val is not None:
                percentile = sum(1 for v in sorted_values if v <= val) / n * 100
                percentiles[item.get('player_id')] = percentile
        
        return percentiles
    
    @staticmethod
    def find_similar_players(target_player_id: str, all_players_stats: list, 
                            positions_map: dict, top_n: int = 5) -> list:
        """Tìm similar players dùng cosine similarity"""
        if target_player_id not in positions_map:
            return []
        
        target_position = positions_map[target_player_id]
        position_group = Algorithms.get_position_group(target_position)
        
        # Filter players cùng position group
        candidates = [
            p for p in all_players_stats 
            if positions_map.get(p.get('player_id')) and 
            Algorithms.get_position_group(positions_map[p.get('player_id')]) == position_group and
            p.get('player_id') != target_player_id and
            p.get('minutes', 0) >= 450
        ]
        
        if not candidates:
            return []
        
        # Chọn features dựa trên position
        features = Algorithms.get_features_for_position(position_group)
        
        # Tính vector cho target
        target_stats = next((p for p in all_players_stats if p.get('player_id') == target_player_id), {})
        target_vector = [target_stats.get(f, 0) for f in features]
        
        # Normalize vectors (Z-score đơn giản)
        def normalize(vec):
            norm = np.linalg.norm(vec)
            return vec / norm if norm > 0 else vec
        
        target_vector = normalize(np.array(target_vector))
        
        # Tính similarity với từng candidate
        similarities = []
        for candidate in candidates:
            candidate_vector = normalize(np.array([candidate.get(f, 0) for f in features]))
            similarity = np.dot(target_vector, candidate_vector)
            score = ((similarity + 1) / 2) * 100  # Convert to 0-100 scale
            similarities.append({
                'player_id': candidate.get('player_id'),
                'score': round(score, 1)
            })
        
        # Sort và lấy top N
        similarities.sort(key=lambda x: x['score'], reverse=True)
        return similarities[:top_n]
    
    @staticmethod
    def get_position_group(position: str) -> str:
        """Map position sang position group"""
        position_lower = position.lower() if position else ""
        if 'goalkeeper' in position_lower or 'gk' in position_lower:
            return 'GK'
        elif 'defender' in position_lower or 'def' in position_lower or 'back' in position_lower:
            return 'DEF'
        elif 'midfield' in position_lower or 'mid' in position_lower:
            return 'MID'
        elif 'forward' in position_lower or 'fwd' in position_lower or 'striker' in position_lower or 'winger' in position_lower:
            return 'FWD'
        return 'MID'  # Default
    
    @staticmethod
    def get_features_for_position(position_group: str) -> list:
        """Lấy features đặc trưng cho từng position group"""
        features_map = {
            'GK': ['saves_per_90', 'clean_sheets_per_90', 'penalties_saved', 
                   'goals_conceded_per_90', 'expected_goals_conceded_per_90'],
            'DEF': ['tackles', 'clearances_blocks_interceptions', 'defensive_contribution_per_90',
                    'expected_goals_conceded_per_90', 'influence'],
            'MID': ['creativity', 'expected_assists_per_90', 'recoveries',
                    'expected_goal_involvements_per_90', 'ict_index'],
            'FWD': ['expected_goals_per_90', 'goals_scored', 'threat',
                    'expected_goal_involvements_per_90', 'ict_index']
        }
        return features_map.get(position_group, features_map['MID'])
    
    @staticmethod
    def scout_players(all_players_stats: list, position_group: str, 
                     sliders: dict, hard_filters: dict) -> list:
        """Scouting algorithm với sliders và hard filters"""
        features = ['expected_goals_per_90', 'expected_assists_per_90', 
                   'expected_goal_involvements_per_90', 'recoveries']
        
        # Tính percentiles
        percentiles_data = {}
        for feature in features:
            percentiles_data[feature] = Algorithms.calculate_percentiles(all_players_stats, feature)
        
        results = []
        for player in all_players_stats:
            player_id = player.get('player_id')
            player_position = player.get('position', '')
            
            # Filter theo position group
            if Algorithms.get_position_group(player_position) != position_group:
                continue
            
            # Hard filters
            if hard_filters.get('min_age') and player.get('age', 0) < hard_filters['min_age']:
                continue
            if hard_filters.get('max_age') and player.get('age', 100) > hard_filters['max_age']:
                continue
            if hard_filters.get('min_value') and player.get('market_value_in_eur', 0) < hard_filters['min_value']:
                continue
            if hard_filters.get('max_value') and player.get('market_value_in_eur', float('inf')) > hard_filters['max_value']:
                continue
            
            # Tính match score
            scores = []
            for feature in features:
                player_percentile = percentiles_data[feature].get(player_id, 50)
                target_percentile = sliders.get(feature, 50)
                score = 100 - abs(player_percentile - target_percentile)
                scores.append(score)
            
            match_score = sum(scores) / len(scores) if scores else 0
            
            results.append({
                'player_id': player_id,
                'match_score': round(match_score, 1),
                'name': player.get('name', ''),
                'club': player.get('club_name', '')
            })
        
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results


# ============================================================================
# CHARTS LAYER (Visualization Layer)
# ============================================================================
class ChartGenerator:
    """Tạo charts - trả về base64 string để hiển thị"""
    
    @staticmethod
    def create_radar_chart(stats: dict, position: str) -> str:
        """Tạo radar chart cho player"""
        position_group = Algorithms.get_position_group(position)
        
        features_map = {
            'GK': ['saves_per_90', 'clean_sheets_per_90', 'penalties_saved', 
                   'goals_conceded_per_90', 'expected_goals_conceded_per_90'],
            'DEF': ['tackles', 'clearances_blocks_interceptions', 'defensive_contribution_per_90',
                    'expected_goals_conceded_per_90', 'influence'],
            'MID': ['creativity', 'expected_assists_per_90', 'recoveries',
                    'expected_goal_involvements_per_90', 'ict_index'],
            'FWD': ['expected_goals_per_90', 'goals_scored', 'threat',
                    'expected_goal_involvements_per_90', 'ict_index']
        }
        
        labels = features_map.get(position_group, features_map['MID'])
        values = [stats.get(label, 0) for label in labels]
        
        # Normalize values to 0-1 scale for better visualization
        max_values = {
            'saves_per_90': 5, 'clean_sheets_per_90': 0.5, 'penalties_saved': 5,
            'goals_conceded_per_90': 2, 'expected_goals_conceded_per_90': 2,
            'tackles': 50, 'clearances_blocks_interceptions': 80, 'defensive_contribution_per_90': 20,
            'influence': 400, 'creativity': 400, 'recoveries': 100,
            'expected_assists_per_90': 1, 'expected_goal_involvements_per_90': 2,
            'ict_index': 100, 'expected_goals_per_90': 1.5, 'goals_scored': 25, 'threat': 500
        }
        
        normalized_values = []
        for i, val in enumerate(values):
            max_val = max_values.get(labels[i], 100)
            normalized_values.append(min(val / max_val * 100, 100) if max_val > 0 else 0)
        
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
        
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        angles += angles[:1]
        normalized_values += normalized_values[:1]
        
        ax.plot(angles, normalized_values, 'o-', linewidth=2, color='#FFD700')
        ax.fill(angles, normalized_values, alpha=0.25, color='#FFD700')
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_thetagrids(np.degrees(angles[:-1]), labels)
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
        
        # Set color
        ax.tick_params(colors='white')
        for label in ax.get_xticklabels():
            label.set_color('white')
        ax.set_facecolor('#2D2D2D')
        fig.patch.set_facecolor('#2D2D2D')
        
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
        buf.seek(0)
        plt.close(fig)
        
        return base64.b64encode(buf.getvalue()).decode()
    
    @staticmethod
    def create_bar_chart(data: list, x_key: str, y_key: str, title: str) -> str:
        """Tạo bar chart đơn giản"""
        fig, ax = plt.subplots(figsize=(10, 5))
        
        x_vals = [item.get(x_key, 0) for item in data]
        y_vals = [item.get(y_key, 0) for item in data]
        
        bars = ax.bar(range(len(x_vals)), y_vals, color='#FFD700', alpha=0.8)
        ax.set_xlabel(x_key, color='white')
        ax.set_ylabel(y_key, color='white')
        ax.set_title(title, color='white')
        ax.set_xticks(range(len(x_vals)))
        ax.set_xticklabels(x_vals, rotation=45)
        
        ax.tick_params(colors='white')
        ax.set_facecolor('#2D2D2D')
        fig.patch.set_facecolor('#1A1A1A')
        
        for spine in ax.spines.values():
            spine.set_color('white')
        
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
        buf.seek(0)
        plt.close(fig)
        
        return base64.b64encode(buf.getvalue()).decode()
    
    @staticmethod
    def create_line_chart(data: list, x_key: str, y_keys: list, title: str) -> str:
        """Tạo line chart với nhiều lines"""
        fig, ax = plt.subplots(figsize=(10, 5))
        
        x_vals = [item.get(x_key, 0) for item in data]
        
        colors = ['#FFD700', '#4CAF50', '#F44336', '#2196F3']
        for i, y_key in enumerate(y_keys):
            y_vals = [item.get(y_key, 0) for item in data]
            ax.plot(x_vals, y_vals, marker='o', label=y_key, color=colors[i % len(colors)])
        
        ax.set_xlabel(x_key, color='white')
        ax.set_title(title, color='white')
        ax.legend(facecolor='#2D2D2D', labelcolor='white')
        
        ax.tick_params(colors='white')
        ax.set_facecolor('#2D2D2D')
        fig.patch.set_facecolor('#1A1A1A')
        
        for spine in ax.spines.values():
            spine.set_color('white')
        
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
        buf.seek(0)
        plt.close(fig)
        
        return base64.b64encode(buf.getvalue()).decode()


# ============================================================================
# STATE MANAGEMENT
# ============================================================================
def init_session_state():
    """Khởi tạo session state"""
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'home'
    if 'current_player_id' not in st.session_state:
        st.session_state.current_player_id = None
    if 'previous_view' not in st.session_state:
        st.session_state.previous_view = None
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager(DB_PATH)
    if 'players_cache' not in st.session_state:
        st.session_state.players_cache = []
    if 'percentiles_cache' not in st.session_state:
        st.session_state.percentiles_cache = {}


def navigate_to(view: str, player_id: str = None):
    """Điều hướng đến view khác"""
    st.session_state.previous_view = st.session_state.current_view
    st.session_state.current_view = view
    if player_id:
        st.session_state.current_player_id = player_id


def go_back():
    """Quay lại view trước"""
    if st.session_state.previous_view:
        st.session_state.current_view = st.session_state.previous_view
        st.session_state.previous_view = None
    else:
        st.session_state.current_view = 'home'


# ============================================================================
# UI COMPONENTS
# ============================================================================
def render_header():
    """Render header với navigation"""
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.session_state.current_view != 'home':
            if st.button("← Back", use_container_width=True):
                go_back()
                st.rerun()
    with col2:
        st.title("⚽ EPL Scout 25/26")


def render_home_view():
    """Home View - Bento Grid Dashboard"""
    st.header("Welcome to EPL Scout")
    st.write("Select a module to get started")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background-color: #2D2D2D; padding: 30px; border-radius: 10px; text-align: center; height: 200px; display: flex; flex-direction: column; justify-content: center;">
            <h2 style="color: #FFD700;">👥 PLAYERS HUB</h2>
            <p style="color: #B0B0B0;">Browse 60+ players</p>
            <p style="color: #B0B0B0;">20 Clubs</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Players Hub", key="hub_btn", use_container_width=True):
            navigate_to('players_hub')
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="background-color: #2D2D2D; padding: 30px; border-radius: 10px; text-align: center; height: 200px; display: flex; flex-direction: column; justify-content: center;">
            <h2 style="color: #FFD700;">🔍 SCOUTING</h2>
            <p style="color: #B0B0B0;">Find your ideal player</p>
            <p style="color: #B0B0B0;">Role-based search</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Scouting", key="scout_btn", use_container_width=True):
            navigate_to('scouting')
            st.rerun()
    
    with col3:
        watchlist_count = len(st.session_state.db.get_watchlist())
        st.markdown(f"""
        <div style="background-color: #2D2D2D; padding: 30px; border-radius: 10px; text-align: center; height: 200px; display: flex; flex-direction: column; justify-content: center;">
            <h2 style="color: #FFD700;">⭐ MY WATCHLIST</h2>
            <p style="color: #B0B0B0;">{watchlist_count} players tracked</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Watchlist", key="watch_btn", use_container_width=True):
            navigate_to('watchlist')
            st.rerun()


def render_players_hub_view():
    """Players Hub View"""
    st.header("Players Hub")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        positions = ['All', 'Goalkeeper', 'Defender', 'Midfielder', 'Forward']
        selected_position = st.selectbox("Position", positions, key="pos_filter")
    
    with col2:
        clubs = st.session_state.db.get_all_clubs()
        club_options = ['All'] + [c['club_name'] for c in clubs]
        selected_club = st.selectbox("Club", club_options, key="club_filter")
    
    with col3:
        min_value = st.number_input("Min Value (€)", min_value=0, value=0, step=1000000, key="min_val")
    
    with col4:
        search_term = st.text_input("Search", "", key="search_input")
    
    # Build filters
    filters = {}
    if selected_position != 'All':
        filters['position'] = selected_position
    
    if selected_club != 'All':
        club_id = next((c['club_id'] for c in clubs if c['club_name'] == selected_club), None)
        if club_id:
            filters['club_id'] = club_id
    
    if min_value > 0:
        filters['min_value'] = min_value
    
    if search_term:
        filters['search'] = search_term
    
    # Search
    players = st.session_state.db.search_players(filters)
    
    if not players:
        st.info("No players found. Try adjusting your filters.")
        if st.button("Reset Filters"):
            st.cache_data.clear()
            st.rerun()
        return
    
    # Display results
    st.subheader(f"Results: {len(players)} players")
    
    # Pagination
    page_size = 25
    total_pages = (len(players) + page_size - 1) // page_size
    
    if total_pages > 1:
        page = st.slider("Page", 1, total_pages, 1, key="page_slider")
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, len(players))
        page_players = players[start_idx:end_idx]
    else:
        page_players = players
    
    # Table
    for player in page_players:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
        with col1:
            if st.button(f"{player.get('name', 'N/A')}", key=f"player_{player.get('player_id')}"):
                navigate_to('player_dashboard', player.get('player_id'))
                st.rerun()
        with col2:
            st.text(player.get('position', 'N/A'))
        with col3:
            st.text(player.get('club_name', 'N/A'))
        with col4:
            value = player.get('market_value_in_eur', 0)
            st.text(f"€{value:,}" if value else "N/A")
        with col5:
            if player.get('image_url'):
                st.image(player['image_url'], width=50)
        
        st.divider()


def render_scouting_view():
    """Scouting View"""
    st.header("Scouting - Role Search")
    
    # Section 1: Position Group
    position_groups = ['GK', 'DEF', 'MID', 'FWD']
    selected_group = st.selectbox("Select Position Group", position_groups)
    
    # Section 2: Sliders
    st.subheader("Define Your Ideal Profile")
    
    col1, col2 = st.columns(2)
    with col1:
        xg_slider = st.slider("xG/90 Percentile", 0, 100, 75, key="xg_slide")
        xa_slider = st.slider("xA/90 Percentile", 0, 100, 75, key="xa_slide")
    with col2:
        xgi_slider = st.slider("xGI/90 Percentile", 0, 100, 75, key="xgi_slide")
        rec_slider = st.slider("Recoveries/90 Percentile", 0, 100, 75, key="rec_slide")
    
    sliders = {
        'expected_goals_per_90': xg_slider,
        'expected_assists_per_90': xa_slider,
        'expected_goal_involvements_per_90': xgi_slider,
        'recoveries': rec_slider
    }
    
    # Section 3: Hard Filters
    with st.expander("Hard Filters"):
        col1, col2, col3 = st.columns(3)
        with col1:
            min_age = st.number_input("Min Age", 16, 40, 18, key="min_age")
            max_age = st.number_input("Max Age", 16, 40, 35, key="max_age")
        with col2:
            min_value = st.number_input("Min Value (€)", 0, 200000000, 0, step=1000000, key="scout_min_val")
            max_value = st.number_input("Max Value (€)", 0, 200000000, 200000000, step=1000000, key="scout_max_val")
        with col3:
            contract_year = st.selectbox("Contract Until", ["Any", "2025", "2026", "2027", "2028", "2029", "2030"], key="contract_yr")
    
    hard_filters = {
        'min_age': min_age,
        'max_age': max_age,
        'min_value': min_value,
        'max_value': max_value
    }
    
    if st.button("🔍 Search", use_container_width=True, type="primary"):
        # Get all players stats
        all_players = st.session_state.db.get_all_players()
        all_stats = []
        positions_map = {}
        
        for player in all_players:
            player_id = player.get('player_id')
            stats = st.session_state.db.get_player_latest_stats(player_id)
            if stats:
                stats['player_id'] = player_id
                stats['name'] = player.get('name')
                stats['club_name'] = player.get('club_name')
                all_stats.append(stats)
            
            player_info = st.session_state.db.get_player_info(player_id)
            if player_info:
                positions_map[player_id] = player_info.get('position', '')
        
        results = Algorithms.scout_players(all_stats, selected_group, sliders, hard_filters)
        
        st.session_state.scouting_results = results
        st.session_state.selected_group = selected_group
    
    # Display results
    if hasattr(st.session_state, 'scouting_results'):
        results = st.session_state.scouting_results
        st.subheader(f"Results: {len(results)} players")
        
        for result in results[:10]:  # Top 10
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.text(f"#{result.get('match_score', 0)}% - {result.get('name', 'N/A')}")
            with col2:
                st.text(result.get('club', 'N/A'))
            with col3:
                if st.button("View Profile", key=f"view_{result.get('player_id')}"):
                    navigate_to('player_dashboard', result.get('player_id'))
                    st.rerun()
            st.divider()


def render_watchlist_view():
    """Watchlist View"""
    st.header("My Watchlist")
    
    watchlist = st.session_state.db.get_watchlist()
    
    if not watchlist:
        st.info("Your watchlist is empty. Add players from the Hub.")
        if st.button("Go to Players Hub", type="primary"):
            navigate_to('players_hub')
            st.rerun()
        return
    
    # Toolbar
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("Search in watchlist", "", key="wl_search")
    with col3:
        if st.button("🗑️ Delete All", type="secondary"):
            st.session_state.db.clear_watchlist()
            st.rerun()
    
    # Filter
    filtered_watchlist = watchlist
    if search_term:
        filtered_watchlist = [p for p in watchlist if search_term.lower() in p.get('name', '').lower()]
    
    st.subheader(f"{len(filtered_watchlist)} players")
    
    for player in filtered_watchlist:
        col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 2, 3, 2, 1, 1])
        
        with col1:
            st.text(player.get('name', 'N/A'))
        with col2:
            st.text(player.get('club_name', 'N/A'))
        with col3:
            st.text(player.get('position', 'N/A'))
        with col4:
            notes = st.text_input("Notes", player.get('notes', ''), key=f"notes_{player.get('player_id')}", label_visibility="collapsed")
            if notes != player.get('notes', ''):
                st.session_state.db.update_watchlist_notes(player.get('player_id'), notes)
        with col5:
            rating = st.selectbox("Rating", [0, 1, 2, 3, 4, 5], index=player.get('rating', 0), key=f"rating_{player.get('player_id')}")
            if rating != player.get('rating', 0):
                st.session_state.db.update_watchlist_rating(player.get('player_id'), rating)
        with col6:
            if st.button("👁️", key=f"view_{player.get('player_id')}"):
                navigate_to('player_dashboard', player.get('player_id'))
                st.rerun()
        with col7:
            if st.button("🗑️", key=f"del_{player.get('player_id')}"):
                st.session_state.db.remove_from_watchlist(player.get('player_id'))
                st.rerun()
        
        st.divider()


def render_player_dashboard_view():
    """Player Dashboard View"""
    player_id = st.session_state.current_player_id
    if not player_id:
        st.error("No player selected")
        return
    
    player_info = st.session_state.db.get_player_info(player_id)
    if not player_info:
        st.error("Player not found")
        return
    
    player_stats = st.session_state.db.get_player_latest_stats(player_id)
    all_stats = st.session_state.db.get_player_stats(player_id)
    
    # Header
    col1, col2 = st.columns([1, 4])
    with col1:
        if player_info.get('image_url'):
            st.image(player_info['image_url'], width=150)
    with col2:
        st.title(player_info.get('name', 'Unknown'))
        st.write(f"**{player_info.get('position', 'N/A')}** | {player_info.get('club_name', 'N/A')}")
        st.write(f"Market Value: €{player_info.get('market_value_in_eur', 0):,}")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Overview", "GW Records", "Performance"])
    
    with tab1:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Player Info")
            st.write(f"**Nationality:** {player_info.get('country_of_citizenship', 'N/A')}")
            st.write(f"**Age:** {calculate_age(player_info.get('date_of_birth'))}")
            st.write(f"**Height:** {player_info.get('height_in_cm', 'N/A')} cm")
            st.write(f"**Foot:** {player_info.get('foot', 'N/A')}")
            st.write(f"**Contract:** {player_info.get('contract_expiration_date', 'N/A')}")
            
            # Add to watchlist button
            in_watchlist = any(w['player_id'] == player_id for w in st.session_state.db.get_watchlist())
            if in_watchlist:
                st.success("✓ In Watchlist")
            else:
                if st.button("⭐ Add to Watchlist", use_container_width=True):
                    st.session_state.db.add_to_watchlist(player_id)
                    st.success("Added!")
                    st.rerun()
        
        with col2:
            st.subheader("Performance Radar")
            if player_stats:
                radar_chart = ChartGenerator.create_radar_chart(player_stats, player_info.get('position', ''))
                st.image(f"data:image/png;base64,{radar_chart}")
                
                # Find Similar button
                if st.button("🔍 Find Similar Players"):
                    similar = Algorithms.find_similar_players(
                        player_id, 
                        all_stats, 
                        {p['player_id']: p.get('position', '') for p in st.session_state.db.get_all_players()}
                    )
                    st.session_state.similar_players = similar
                
                if hasattr(st.session_state, 'similar_players') and st.session_state.similar_players:
                    st.subheader("Similar Players")
                    for sim in st.session_state.similar_players:
                        sim_player = st.session_state.db.get_player_info(sim['player_id'])
                        st.write(f"- **{sim_player.get('name', 'N/A')}** ({sim_player.get('club_name', '')}) - {sim['score']}% match")
            
            # Season Statistics
            st.subheader("Season Statistics")
            if player_stats:
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Goals", player_stats.get('goals_scored', 0))
                    st.metric("Assists", player_stats.get('assists', 0))
                    st.metric("Minutes", player_stats.get('minutes', 0))
                with col_b:
                    st.metric("xG/90", f"{player_stats.get('expected_goals_per_90', 0):.2f}")
                    st.metric("xA/90", f"{player_stats.get('expected_assists_per_90', 0):.2f}")
                    st.metric("ICT Index", f"{player_stats.get('ict_index', 0):.1f}")
                with col_c:
                    st.metric("Tackles", player_stats.get('tackles', 0))
                    st.metric("Recoveries", player_stats.get('recoveries', 0))
    
    with tab2:
        st.subheader("Gameweek Records")
        if all_stats:
            # Create DataFrame
            df_stats = pd.DataFrame(all_stats)
            display_cols = ['gw', 'minutes', 'starts', 'goals_scored', 'assists', 
                           'clean_sheets', 'yellow_cards', 'red_cards', 
                           'expected_goals', 'expected_assists', 'ict_index']
            available_cols = [c for c in display_cols if c in df_stats.columns]
            st.dataframe(df_stats[available_cols], use_container_width=True)
            
            # Footer summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Games Played", len(all_stats))
            with col2:
                st.metric("Total Goals", df_stats['goals_scored'].sum())
            with col3:
                st.metric("Total Assists", df_stats['assists'].sum())
    
    with tab3:
        st.subheader("Performance Charts")
        if all_stats:
            col1, col2 = st.columns(2)
            
            with col1:
                # Minutes per GW
                chart_data = [{'gw': s.get('gw'), 'minutes': s.get('minutes', 0)} for s in all_stats]
                bar_chart = ChartGenerator.create_bar_chart(chart_data, 'gw', 'minutes', 'Minutes per GW')
                st.image(f"data:image/png;base64,{bar_chart}")
            
            with col2:
                # Cumulative Goals vs xG
                cumulative_data = []
                cum_goals, cum_xg = 0, 0
                for s in all_stats:
                    cum_goals += s.get('goals_scored', 0)
                    cum_xg += s.get('expected_goals', 0)
                    cumulative_data.append({
                        'gw': s.get('gw'),
                        'cumulative_goals': cum_goals,
                        'cumulative_xg': cum_xg
                    })
                line_chart = ChartGenerator.create_line_chart(
                    cumulative_data, 'gw', ['cumulative_goals', 'cumulative_xg'], 'Goals vs Expected Goals'
                )
                st.image(f"data:image/png;base64,{line_chart}")


def calculate_age(birth_date_str):
    """Tính tuổi từ ngày sinh"""
    if not birth_date_str:
        return "N/A"
    try:
        birth_date = datetime.strptime(str(birth_date_str), "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age
    except:
        return "N/A"


# ============================================================================
# MAIN APP
# ============================================================================
def main():
    # Initialize
    init_session_state()
    
    # Load data if needed
    if not st.session_state.players_cache:
        clubs_loaded = st.session_state.db.load_csv_to_db(f"{DATA_DIR}/clubs.csv", "clubs")
        players_loaded = st.session_state.db.load_csv_to_db(f"{DATA_DIR}/playersinfo.csv", "playersinfo")
        stats_loaded = st.session_state.db.load_csv_to_db(f"{DATA_DIR}/playerstats.csv", "playerstats")
        
        if clubs_loaded and players_loaded and stats_loaded:
            st.session_state.players_cache = st.session_state.db.get_all_players()
    
    # Render header
    render_header()
    
    # Route to current view
    if st.session_state.current_view == 'home':
        render_home_view()
    elif st.session_state.current_view == 'players_hub':
        render_players_hub_view()
    elif st.session_state.current_view == 'scouting':
        render_scouting_view()
    elif st.session_state.current_view == 'watchlist':
        render_watchlist_view()
    elif st.session_state.current_view == 'player_dashboard':
        render_player_dashboard_view()
    else:
        render_home_view()


if __name__ == "__main__":
    main()
