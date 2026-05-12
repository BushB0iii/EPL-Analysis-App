"""
Database Manager for EPL Scout Application
Handles all SQLite database operations with proper schema and foreign keys.
"""
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any


class DatabaseManager:
    """Manages SQLite database operations with loose coupling from UI."""
    
    def __init__(self, db_path: str = "epl_scout.db"):
        self.db_path = db_path
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize database schema with proper foreign keys."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Create clubs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clubs (
                club_id VARCHAR(2) PRIMARY KEY,
                club_name VARCHAR(50) NOT NULL
            )
        """)
        
        # Create playersinfo table
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
        
        # Create playerstats table
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
        
        # Create watchlist table
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
    
    def load_csv_data(self, data_dir: str = "data"):
        """Load CSV files into database."""
        data_path = Path(data_dir)
        
        # Load clubs
        clubs_file = data_path / "clubs.csv"
        if clubs_file.exists():
            df_clubs = pd.read_csv(clubs_file)
            self._insert_dataframe(df_clubs, "clubs")
        
        # Load playersinfo
        players_file = data_path / "playersinfo.csv"
        if players_file.exists():
            df_players = pd.read_csv(players_file)
            self._insert_dataframe(df_players, "playersinfo")
        
        # Load playerstats
        stats_file = data_path / "playerstats.csv"
        if stats_file.exists():
            df_stats = pd.read_csv(stats_file)
            self._insert_dataframe(df_stats, "playerstats")
    
    def _insert_dataframe(self, df: pd.DataFrame, table_name: str):
        """Insert DataFrame into table, replacing existing data."""
        conn = self._get_connection()
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.commit()
        conn.close()
    
    # ==================== Query Methods (Return Dict/List only) ====================
    
    def get_all_clubs(self) -> List[Dict[str, Any]]:
        """Get all clubs as list of dicts."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clubs ORDER BY club_name")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_all_players(self) -> List[Dict[str, Any]]:
        """Get all players with basic info as list of dicts."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, c.club_name 
            FROM playersinfo p 
            LEFT JOIN clubs c ON p.club_id = c.club_id 
            ORDER BY p.name
        """)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_player_by_id(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get single player by ID as dict."""
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
        return dict(row) if row else None
    
    def get_player_stats(self, player_id: str) -> List[Dict[str, Any]]:
        """Get all gameweek stats for a player as list of dicts."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM playerstats 
            WHERE player_id = ? 
            ORDER BY gw
        """, (player_id,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_latest_player_stats(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get latest gameweek stats for a player as dict."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM playerstats 
            WHERE player_id = ? 
            ORDER BY gw DESC 
            LIMIT 1
        """, (player_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def search_players(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search players with dynamic filters. Returns list of dicts."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT p.*, c.club_name 
            FROM playersinfo p 
            LEFT JOIN clubs c ON p.club_id = c.club_id 
            WHERE 1=1
        """
        params = []
        
        if filters.get("position"):
            query += " AND p.position = ?"
            params.append(filters["position"])
        
        if filters.get("club_id"):
            query += " AND p.club_id = ?"
            params.append(filters["club_id"])
        
        if filters.get("min_market_value") is not None:
            query += " AND p.market_value_in_eur >= ?"
            params.append(filters["min_market_value"])
        
        if filters.get("max_market_value") is not None:
            query += " AND p.market_value_in_eur <= ?"
            params.append(filters["max_market_value"])
        
        if filters.get("search_query"):
            query += " AND (p.name LIKE ? OR p.first_name LIKE ? OR p.last_name LIKE ?)"
            search_term = f"%{filters['search_query']}%"
            params.extend([search_term, search_term, search_term])
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_players_for_scouting(self, position_group: str) -> List[Dict[str, Any]]:
        """Get players filtered by position group for scouting algorithm."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Map position group to positions
        position_map = {
            "GK": ["Goalkeeper"],
            "DEF": ["Defender"],
            "MID": ["Midfielder"],
            "FWD": ["Forward"]
        }
        
        positions = position_map.get(position_group, [])
        if not positions:
            conn.close()
            return []
        
        placeholders = ",".join("?" * len(positions))
        query = f"""
            SELECT p.*, c.club_name 
            FROM playersinfo p 
            LEFT JOIN clubs c ON p.club_id = c.club_id 
            WHERE p.position IN ({placeholders})
        """
        
        cursor.execute(query, positions)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    # ==================== Watchlist Methods ====================
    
    def get_watchlist(self) -> List[Dict[str, Any]]:
        """Get full watchlist with player info as list of dicts."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT w.*, p.name, p.club_id, p.position, c.club_name 
            FROM watchlist w 
            JOIN playersinfo p ON w.player_id = p.player_id 
            LEFT JOIN clubs c ON p.club_id = c.club_id 
            ORDER BY w.created_at DESC
        """)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def add_to_watchlist(self, player_id: str, rating: int = 0, notes: str = "") -> bool:
        """Add player to watchlist. Returns success status."""
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
        except Exception:
            return False
    
    def update_watchlist_rating(self, player_id: str, rating: int) -> bool:
        """Update player rating in watchlist. Returns success status."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE watchlist SET rating = ? WHERE player_id = ?
            """, (rating, player_id))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def update_watchlist_notes(self, player_id: str, notes: str) -> bool:
        """Update player notes in watchlist. Returns success status."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE watchlist SET notes = ? WHERE player_id = ?
            """, (notes, player_id))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def remove_from_watchlist(self, player_id: str) -> bool:
        """Remove player from watchlist. Returns success status."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watchlist WHERE player_id = ?", (player_id,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def clear_watchlist(self) -> bool:
        """Clear entire watchlist. Returns success status."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watchlist")
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def is_in_watchlist(self, player_id: str) -> bool:
        """Check if player is in watchlist. Returns boolean."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM watchlist WHERE player_id = ?", (player_id,))
        result = cursor.fetchone() is not None
        conn.close()
        return result
