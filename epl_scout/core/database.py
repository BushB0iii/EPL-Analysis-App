"""
EPL Scout 25/26 - Core Module
Database initialization and data access layer
"""
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any


class DatabaseManager:
    """Manages SQLite database operations with loose coupling."""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
    def initialize_schema(self):
        """Create database tables."""
        cursor = self.conn.cursor()
        
        # Clubs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clubs (
                club_id VARCHAR(2) PRIMARY KEY,
                club_name VARCHAR(50) NOT NULL
            )
        """)
        
        # Players info table
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
        
        # Player stats table
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
        
        # Watchlist table
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
        
        self.conn.commit()
    
    def load_clubs(self, csv_path: str):
        """Load clubs from CSV into database."""
        df = pd.read_csv(csv_path)
        df.to_sql('clubs', self.conn, if_exists='replace', index=False)
        
    def load_players_info(self, csv_path: str):
        """Load players info from CSV into database."""
        df = pd.read_csv(csv_path)
        df.to_sql('playersinfo', self.conn, if_exists='replace', index=False)
        
    def load_player_stats(self, csv_path: str):
        """Load player stats from CSV into database."""
        df = pd.read_csv(csv_path)
        df.to_sql('playerstats', self.conn, if_exists='replace', index=False)
    
    def get_all_clubs(self) -> List[Dict[str, Any]]:
        """Get all clubs as list of dicts."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT club_id, club_name FROM clubs")
        columns = ['club_id', 'club_name']
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_all_players_info(self) -> List[Dict[str, Any]]:
        """Get all players info as list of dicts."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.*, c.club_name 
            FROM playersinfo p 
            LEFT JOIN clubs c ON p.club_id = c.club_id
        """)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_player_by_id(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get single player info by ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.*, c.club_name 
            FROM playersinfo p 
            LEFT JOIN clubs c ON p.club_id = c.club_id
            WHERE p.player_id = ?
        """, (player_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def get_player_stats(self, player_id: str) -> List[Dict[str, Any]]:
        """Get all stats for a player."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM playerstats WHERE player_id = ? ORDER BY gw
        """, (player_id,))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_players_with_stats(self, min_minutes: int = 0) -> List[Dict[str, Any]]:
        """Get players with their aggregated stats."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.*, 
                   SUM(ps.minutes) as total_minutes,
                   SUM(ps.goals_scored) as total_goals,
                   SUM(ps.assists) as total_assists,
                   AVG(ps.expected_goals_per_90) as avg_xg_per_90,
                   AVG(ps.expected_assists_per_90) as avg_xa_per_90,
                   AVG(ps.recoveries) as avg_recoveries
            FROM playersinfo p
            LEFT JOIN playerstats ps ON p.player_id = ps.player_id
            GROUP BY p.player_id
            HAVING total_minutes >= ?
        """, (min_minutes,))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def add_to_watchlist(self, player_id: str, rating: int = 0, notes: str = "") -> bool:
        """Add player to watchlist."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO watchlist (player_id, rating, notes)
                VALUES (?, ?, ?)
            """, (player_id, rating, notes))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding to watchlist: {e}")
            return False
    
    def remove_from_watchlist(self, player_id: str) -> bool:
        """Remove player from watchlist."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM watchlist WHERE player_id = ?", (player_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error removing from watchlist: {e}")
            return False
    
    def get_watchlist(self) -> List[Dict[str, Any]]:
        """Get all players in watchlist with their info."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT w.*, p.name, p.position, c.club_name
            FROM watchlist w
            JOIN playersinfo p ON w.player_id = p.player_id
            LEFT JOIN clubs c ON p.club_id = c.club_id
            ORDER BY w.created_at DESC
        """)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_watchlist_rating(self, player_id: str, rating: int) -> bool:
        """Update player rating in watchlist."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE watchlist SET rating = ? WHERE player_id = ?
            """, (rating, player_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating rating: {e}")
            return False
    
    def update_watchlist_notes(self, player_id: str, notes: str) -> bool:
        """Update player notes in watchlist."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE watchlist SET notes = ? WHERE player_id = ?
            """, (notes, player_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating notes: {e}")
            return False
    
    def clear_watchlist(self) -> bool:
        """Clear entire watchlist."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM watchlist")
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error clearing watchlist: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        self.conn.close()
