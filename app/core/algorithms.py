"""
EPL Scout 25/26 - Algorithms Module
Contains Similar Players and Scouting algorithms
"""

import numpy as np
from typing import Dict, List, Any, Tuple
from app.data.database import DatabaseManager
from app.data.data_loader import DataLoader


class SimilarPlayersAlgorithm:
    """Find similar players using Cosine Similarity"""
    
    def __init__(self, db: DatabaseManager, data_loader: DataLoader):
        self.db = db
        self.data_loader = data_loader
    
    def find_similar_players(self, player_id: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Find top N similar players based on playing style
        
        Args:
            player_id: ID of the reference player
            top_n: Number of similar players to return
        
        Returns:
            List of similar players with match scores
        """
        # Get target player info
        player_info = self.db.get_player_by_id(player_id)
        if not player_info:
            return []
        
        position = player_info.get('position', '')
        position_group = self.data_loader.get_position_group(position)
        
        # Get all players in same position group
        all_players = self.db.get_all_players()
        eligible_players = self.data_loader.get_eligible_players()
        
        # Filter by position group and exclude target player
        candidate_ids = []
        for p in all_players:
            if p['player_id'] == player_id:
                continue
            if p['player_id'] not in eligible_players:
                continue
            if self.data_loader.get_position_group(p.get('position', '')) == position_group:
                candidate_ids.append(p['player_id'])
        
        if not candidate_ids:
            return []
        
        # Get feature vectors based on position group
        target_vector = self._get_feature_vector(player_id, position_group)
        if target_vector is None or len(target_vector) == 0:
            return []
        
        # Calculate similarity scores
        similarities = []
        for candidate_id in candidate_ids:
            candidate_vector = self._get_feature_vector(candidate_id, position_group)
            if candidate_vector is not None and len(candidate_vector) > 0:
                similarity = self._cosine_similarity(target_vector, candidate_vector)
                score = ((similarity + 1) / 2) * 100
                
                candidate_info = self.db.get_player_by_id(candidate_id)
                if candidate_info:
                    similarities.append({
                        'player_id': candidate_id,
                        'name': candidate_info.get('name', ''),
                        'club_name': candidate_info.get('club_name', ''),
                        'position': candidate_info.get('position', ''),
                        'match_score': round(score, 2)
                    })
        
        # Sort by match score descending
        similarities.sort(key=lambda x: x['match_score'], reverse=True)
        
        return similarities[:top_n]
    
    def _get_feature_vector(self, player_id: str, position_group: str) -> np.ndarray:
        """Get normalized feature vector for a player based on position group"""
        stats = self.db.get_player_stats(player_id)
        
        if not stats:
            return None
        
        # Aggregate stats (sum or average across all GWs)
        total_minutes = sum(s.get('minutes', 0) for s in stats)
        
        if total_minutes == 0:
            return None
        
        # Select features based on position group
        if position_group == 'GK':
            features = [
                self._safe_avg(stats, 'saves_per_90'),
                self._safe_avg(stats, 'clean_sheets_per_90'),
                self._safe_avg(stats, 'penalties_saved'),
                self._safe_avg(stats, 'goals_conceded_per_90') * -1,  # Invert (lower is better)
                self._safe_avg(stats, 'expected_goals_conceded_per_90') * -1,
            ]
        elif position_group == 'DEF':
            features = [
                self._safe_avg(stats, 'tackles'),
                self._safe_avg(stats, 'clearances_blocks_interceptions'),
                self._safe_avg(stats, 'defensive_contribution_per_90'),
                self._safe_avg(stats, 'expected_goals_conceded_per_90') * -1,
                self._safe_avg(stats, 'influence'),
            ]
        elif position_group == 'MID':
            features = [
                self._safe_avg(stats, 'creativity'),
                self._safe_avg(stats, 'expected_assists_per_90'),
                self._safe_avg(stats, 'recoveries'),
                self._safe_avg(stats, 'expected_goal_involvements_per_90'),
                self._safe_avg(stats, 'ict_index'),
            ]
        else:  # FWD
            features = [
                self._safe_avg(stats, 'expected_goals_per_90'),
                self._safe_avg(stats, 'goals_scored'),
                self._safe_avg(stats, 'threat'),
                self._safe_avg(stats, 'expected_goal_involvements_per_90'),
                self._safe_avg(stats, 'ict_index'),
            ]
        
        # Convert to numpy array
        vector = np.array(features, dtype=np.float32)
        
        # Handle NaN values
        vector = np.nan_to_num(vector, nan=0.0)
        
        return vector
    
    def _safe_avg(self, stats: List[Dict], field: str) -> float:
        """Safely calculate average of a field"""
        values = [s.get(field, 0) for s in stats if s.get(field) is not None]
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))


class ScoutingAlgorithm:
    """Role-based player search algorithm"""
    
    def __init__(self, db: DatabaseManager, data_loader: DataLoader, league_percentiles: Dict):
        self.db = db
        self.data_loader = data_loader
        self.league_percentiles = league_percentiles
    
    def search_players(
        self,
        position_group: str,
        targets: Dict[str, float],
        hard_filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search for players matching ideal profile
        
        Args:
            position_group: GK, DEF, MID, or FWD
            targets: Dict of stat targets (percentile values)
            hard_filters: Age range, market value, contract filters
        
        Returns:
            List of matching players sorted by match score
        """
        all_players = self.db.get_all_players()
        eligible_players = set(self.data_loader.get_eligible_players())
        
        results = []
        
        for player in all_players:
            player_id = player['player_id']
            
            # Check eligibility
            if player_id not in eligible_players:
                continue
            
            # Check position group
            player_pos_group = self.data_loader.get_position_group(player.get('position', ''))
            if player_pos_group != position_group:
                continue
            
            # Apply hard filters
            if not self._apply_hard_filters(player, hard_filters):
                continue
            
            # Calculate match score
            match_score = self._calculate_match_score(player_id, targets, position_group)
            
            if match_score > 0:
                results.append({
                    'player_id': player_id,
                    'name': player.get('name', ''),
                    'club_name': player.get('club_name', ''),
                    'position': player.get('position', ''),
                    'match_score': round(match_score, 2)
                })
        
        # Sort by match score descending
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return results
    
    def _apply_hard_filters(self, player: Dict, filters: Dict) -> bool:
        """Apply hard filters (age, market value, contract)"""
        # Market value filter
        market_value = player.get('market_value_in_eur', 0) or 0
        
        if filters.get('min_market_value') is not None:
            if market_value < filters['min_market_value']:
                return False
        
        if filters.get('max_market_value') is not None:
            if market_value > filters['max_market_value']:
                return False
        
        # Contract expiration filter
        if filters.get('contract_year'):
            contract_date = player.get('contract_expiration_date', '')
            if contract_date:
                try:
                    year = int(contract_date.split('/')[-1])
                    if year != filters['contract_year']:
                        return False
                except (ValueError, IndexError):
                    pass
        
        return True
    
    def _calculate_match_score(
        self,
        player_id: str,
        targets: Dict[str, float],
        position_group: str
    ) -> float:
        """Calculate match score based on percentile targets"""
        stats = self.db.get_player_stats(player_id)
        
        if not stats:
            return 0.0
        
        scores = []
        
        # Map target names to stat columns
        stat_mapping = {
            'xg_per_90': 'expected_goals_per_90',
            'xa_per_90': 'expected_assists_per_90',
            'xgi_per_90': 'expected_goal_involvements_per_90',
            'recoveries_per_90': 'recoveries'
        }
        
        for target_stat, target_percentile in targets.items():
            stat_column = stat_mapping.get(target_stat, target_stat)
            
            # Get player's actual value
            player_value = self._safe_avg(stats, stat_column)
            
            # Get player's percentile
            player_percentile = self._get_player_percentile(
                player_value, position_group, stat_column
            )
            
            # Calculate score (100 - abs difference)
            score = 100 - abs(player_percentile - target_percentile)
            scores.append(max(0, score))
        
        if not scores:
            return 0.0
        
        return sum(scores) / len(scores)
    
    def _get_player_percentile(
        self,
        value: float,
        position: str,
        stat_name: str
    ) -> float:
        """Get player's percentile for a specific stat"""
        key = f"{position}_{stat_name}"
        
        if key not in self.league_percentiles:
            return 50.0
        
        percentiles = self.league_percentiles[key]
        
        # Find which percentile bracket the value falls into
        sorted_percentiles = sorted(percentiles.items(), key=lambda x: float(x[0]))
        
        for p_str, threshold in sorted_percentiles:
            p = float(p_str)
            if value <= threshold:
                return p
        
        return 95.0
    
    def _safe_avg(self, stats: List[Dict], field: str) -> float:
        """Safely calculate average of a field"""
        values = [s.get(field, 0) for s in stats if s.get(field) is not None]
        if not values:
            return 0.0
        return sum(values) / len(values)
