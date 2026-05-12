"""
EPL Scout 25/26 - Data Loader Module
Handles CSV loading and data processing
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from app.data.database import DatabaseManager


class DataLoader:
    """Data Loader - Handles CSV loading and preprocessing"""
    
    def __init__(self, db: DatabaseManager, clubs_path: str, playersinfo_path: str, playerstats_path: str):
        self.db = db
        self.clubs_path = clubs_path
        self.playersinfo_path = playersinfo_path
        self.playerstats_path = playerstats_path
        
        # In-memory DataFrames for quick access
        self.clubs_df: Optional[pd.DataFrame] = None
        self.playersinfo_df: Optional[pd.DataFrame] = None
        
        # League percentiles cache
        self.league_percentiles: Dict[str, Dict[str, float]] = {}
    
    def load_all_data(self):
        """Load all CSV data into database and memory"""
        # Load clubs
        self._load_clubs()
        
        # Load players info
        self._load_players_info()
        
        # Load player stats
        self._load_player_stats()
    
    def _load_clubs(self):
        """Load clubs from CSV"""
        self.clubs_df = pd.read_csv(self.clubs_path, delimiter='\t')
        clubs_list = self.clubs_df.to_dict('records')
        self.db.insert_clubs(clubs_list)
    
    def _load_players_info(self):
        """Load players info from CSV"""
        self.playersinfo_df = pd.read_csv(self.playersinfo_path, delimiter='\t')
        players_list = self.playersinfo_df.to_dict('records')
        self.db.insert_players(players_list)
    
    def _load_player_stats(self):
        """Load player stats from CSV into SQLite"""
        stats_df = pd.read_csv(self.playerstats_path)
        stats_list = stats_df.to_dict('records')
        self.db.insert_player_stats(stats_list)
    
    def calculate_league_percentiles(self) -> Dict[str, Dict[str, float]]:
        """Calculate league percentiles for per_90 stats and indices"""
        if self.playersinfo_df is None:
            return {}
        
        # Get player stats from DB
        with self.db.get_connection() as conn:
            stats_df = pd.read_sql_query("SELECT * FROM playerstats", conn)
        
        # Ensure player_id is string type
        stats_df['player_id'] = stats_df['player_id'].astype(str)
        
        # Filter players with total_minutes >= 450
        player_minutes = stats_df.groupby('player_id')['minutes'].sum()
        eligible_players = player_minutes[player_minutes >= 450].index.tolist()
        
        if not eligible_players:
            # If no eligible players, use all players
            eligible_players = stats_df['player_id'].unique().tolist()
        
        filtered_stats = stats_df[stats_df['player_id'].isin(eligible_players)]
        
        percentiles = {}
        
        # Stats to calculate percentiles for
        stat_columns = [
            'expected_goals_per_90', 'expected_assists_per_90', 
            'expected_goal_involvements_per_90', 'expected_goals_conceded_per_90',
            'influence', 'creativity', 'threat', 'ict_index',
            'saves_per_90', 'clean_sheets_per_90', 'goals_conceded_per_90',
            'starts_per_90', 'defensive_contribution_per_90',
            'tackles', 'clearances_blocks_interceptions', 'recoveries'
        ]
        
        # Get positions for each player
        players_df = self.playersinfo_df[['player_id', 'position']].copy()
        players_df['player_id'] = players_df['player_id'].astype(str)
        merged_stats = filtered_stats.merge(players_df, on='player_id', how='left')
        
        # Calculate percentiles per position
        positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
        percentile_levels = [50, 75, 90, 95]
        
        for position in positions:
            pos_stats = merged_stats[merged_stats['position'] == position]
            
            for stat in stat_columns:
                if stat in pos_stats.columns and len(pos_stats[stat].dropna()) > 0:
                    key = f"{position}_{stat}"
                    percentiles[key] = {}
                    
                    for p in percentile_levels:
                        percentiles[key][str(p)] = pos_stats[stat].dropna().quantile(p / 100)
        
        self.league_percentiles = percentiles
        return percentiles
    
    def get_position_group(self, position: str) -> str:
        """Map sub-position to position group (GK, DEF, MID, FWD)"""
        position_lower = position.lower() if position else ""
        
        if 'goalkeeper' in position_lower or 'gk' in position_lower:
            return 'GK'
        elif 'defender' in position_lower or 'back' in position_lower or 'centre' in position_lower:
            return 'DEF'
        elif 'midfielder' in position_lower or 'winger' in position_lower:
            return 'MID'
        elif 'forward' in position_lower or 'striker' in position_lower:
            return 'FWD'
        else:
            return 'MID'  # Default
    
    def get_eligible_players(self) -> List[str]:
        """Get list of players with total minutes >= 450"""
        with self.db.get_connection() as conn:
            query = """
                SELECT player_id, SUM(minutes) as total_minutes
                FROM playerstats
                GROUP BY player_id
                HAVING total_minutes >= 450
            """
            df = pd.read_sql_query(query, conn)
        return df['player_id'].tolist()
    
    def get_player_aggregated_stats(self, player_id: str) -> Dict[str, Any]:
        """Get aggregated stats for a player"""
        with self.db.get_connection() as conn:
            query = """
                SELECT 
                    SUM(minutes) as total_minutes,
                    SUM(goals_scored) as total_goals,
                    SUM(assists) as total_assists,
                    SUM(clean_sheets) as total_clean_sheets,
                    SUM(tackles) as total_tackles,
                    SUM(recoveries) as total_recoveries,
                    AVG(expected_goals_per_90) as avg_xg_per_90,
                    AVG(expected_assists_per_90) as avg_xa_per_90,
                    AVG(influence) as avg_influence,
                    AVG(creativity) as avg_creativity,
                    AVG(threat) as avg_threat,
                    AVG(ict_index) as avg_ict_index
                FROM playerstats
                WHERE player_id = ?
            """
            cursor = conn.cursor()
            cursor.execute(query, (player_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return {}
