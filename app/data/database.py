"""
EPL Scout 25/26 - Database Manager Module
Handles all database operations with proper abstraction
"""

import sqlite3
from typing import List, Dict, Any, Optional
from contextlib import contextmanager


class DatabaseManager:
    """Database Manager - Handles SQLite operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def initialize_schema(self):
        """Initialize database schema with proper normalization"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
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
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_club ON playersinfo(club_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_position ON playersinfo(position)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_player ON playerstats(player_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_gw ON playerstats(gw)")
    
    def insert_clubs(self, clubs: List[Dict[str, Any]]):
        """Insert clubs data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT OR REPLACE INTO clubs (club_id, club_name) VALUES (?, ?)",
                [(club['club_id'], club['club_name']) for club in clubs]
            )
    
    def insert_players(self, players: List[Dict[str, Any]]):
        """Insert players data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """INSERT OR REPLACE INTO playersinfo 
                   (player_id, first_name, last_name, name, last_season, club_id,
                    country_of_citizenship, date_of_birth, sub_position, position,
                    foot, height_in_cm, contract_expiration_date, image_url,
                    current_club_name, market_value_in_eur)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        p['player_id'], p['first_name'], p['last_name'], p['name'],
                        p.get('last_season'), p.get('club_id'), p.get('country_of_citizenship'),
                        p.get('date_of_birth'), p.get('sub_position'), p.get('position'),
                        p.get('foot'), p.get('height_in_cm'), p.get('contract_expiration_date'),
                        p.get('image_url'), p.get('current_club_name'), p.get('market_value_in_eur')
                    )
                    for p in players
                ]
            )
    
    def insert_player_stats(self, stats: List[Dict[str, Any]]):
        """Insert player statistics data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """INSERT OR REPLACE INTO playerstats 
                   (player_id, gw, expected_goals, expected_assists, expected_goal_involvements,
                    expected_goals_conceded, expected_goals_per_90, expected_assists_per_90,
                    expected_goal_involvements_per_90, expected_goals_conceded_per_90,
                    influence, creativity, threat, ict_index, news, news_added, minutes,
                    goals_scored, assists, clean_sheets, goals_conceded, own_goals,
                    penalties_saved, penalties_missed, yellow_cards, red_cards, saves,
                    starts, defensive_contribution, saves_per_90, clean_sheets_per_90,
                    goals_conceded_per_90, starts_per_90, defensive_contribution_per_90,
                    tackles, clearances_blocks_interceptions, recoveries)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        s['player_id'], s.get('gw', 0), s.get('expected_goals', 0),
                        s.get('expected_assists', 0), s.get('expected_goal_involvements', 0),
                        s.get('expected_goals_conceded', 0), s.get('expected_goals_per_90', 0),
                        s.get('expected_assists_per_90', 0), s.get('expected_goal_involvements_per_90', 0),
                        s.get('expected_goals_conceded_per_90', 0), s.get('influence', 0),
                        s.get('creativity', 0), s.get('threat', 0), s.get('ict_index', 0),
                        s.get('news', ''), s.get('news_added'), s.get('minutes', 0),
                        s.get('goals_scored', 0), s.get('assists', 0), s.get('clean_sheets', 0),
                        s.get('goals_conceded', 0), s.get('own_goals', 0), s.get('penalties_saved', 0),
                        s.get('penalties_missed', 0), s.get('yellow_cards', 0), s.get('red_cards', 0),
                        s.get('saves', 0), s.get('starts', 0), s.get('defensive_contribution', 0),
                        s.get('saves_per_90', 0), s.get('clean_sheets_per_90', 0),
                        s.get('goals_conceded_per_90', 0), s.get('starts_per_90', 0),
                        s.get('defensive_contribution_per_90', 0), s.get('tackles', 0),
                        s.get('clearances_blocks_interceptions', 0), s.get('recoveries', 0)
                    )
                    for s in stats
                ]
            )
    
    def get_all_clubs(self) -> List[Dict[str, Any]]:
        """Get all clubs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clubs ORDER BY club_name")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_players(self) -> List[Dict[str, Any]]:
        """Get all players with basic info"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, c.club_name 
                FROM playersinfo p
                LEFT JOIN clubs c ON p.club_id = c.club_id
                ORDER BY p.name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_player_by_id(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get player by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, c.club_name 
                FROM playersinfo p
                LEFT JOIN clubs c ON p.club_id = c.club_id
                WHERE p.player_id = ?
            """, (player_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_player_stats(self, player_id: str) -> List[Dict[str, Any]]:
        """Get all stats for a player"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM playerstats WHERE player_id = ? ORDER BY gw",
                (player_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_players_by_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get players with dynamic filters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT p.*, c.club_name 
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
            
            if filters.get('min_market_value') is not None:
                query += " AND p.market_value_in_eur >= ?"
                params.append(filters['min_market_value'])
            
            if filters.get('max_market_value') is not None:
                query += " AND p.market_value_in_eur <= ?"
                params.append(filters['max_market_value'])
            
            if filters.get('search_query'):
                query += " AND (p.name LIKE ? OR p.first_name LIKE ? OR p.last_name LIKE ?)"
                search_term = f"%{filters['search_query']}%"
                params.extend([search_term, search_term, search_term])
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # Watchlist operations
    def add_to_watchlist(self, player_id: str, rating: int = 0, notes: str = "") -> bool:
        """Add player to watchlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """INSERT OR REPLACE INTO watchlist (player_id, rating, notes)
                       VALUES (?, ?, ?)""",
                    (player_id, rating, notes)
                )
                return True
            except Exception:
                return False
    
    def remove_from_watchlist(self, player_id: str) -> bool:
        """Remove player from watchlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM watchlist WHERE player_id = ?", (player_id,))
                return True
            except Exception:
                return False
    
    def get_watchlist(self) -> List[Dict[str, Any]]:
        """Get all players in watchlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT w.*, p.name, p.position, p.club_id, c.club_name
                FROM watchlist w
                JOIN playersinfo p ON w.player_id = p.player_id
                LEFT JOIN clubs c ON p.club_id = c.club_id
                ORDER BY w.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_watchlist_rating(self, player_id: str, rating: int) -> bool:
        """Update player rating in watchlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE watchlist SET rating = ? WHERE player_id = ?",
                    (rating, player_id)
                )
                return True
            except Exception:
                return False
    
    def update_watchlist_notes(self, player_id: str, notes: str) -> bool:
        """Update player notes in watchlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE watchlist SET notes = ? WHERE player_id = ?",
                    (notes, player_id)
                )
                return True
            except Exception:
                return False
    
    def clear_watchlist(self) -> bool:
        """Clear entire watchlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM watchlist")
                return True
            except Exception:
                return False
    
    def is_in_watchlist(self, player_id: str) -> bool:
        """Check if player is in watchlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM watchlist WHERE player_id = ?",
                (player_id,)
            )
            return cursor.fetchone()[0] > 0
    
    def get_watchlist_entry(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get watchlist entry for a player"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM watchlist WHERE player_id = ?",
                (player_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
