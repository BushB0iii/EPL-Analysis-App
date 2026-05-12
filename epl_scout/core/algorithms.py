"""
EPL Scout 25/26 - Algorithms Module
Business logic for similar players, scouting, and calculations
"""
import numpy as np
from typing import Dict, List, Any, Optional
from collections import defaultdict


class AlgorithmEngine:
    """Handles all algorithmic operations with loose coupling."""
    
    def __init__(self):
        self.league_percentiles: Dict[str, Dict[str, float]] = {}
        self.similar_players_cache: Dict[str, List[Dict[str, Any]]] = {}
        
    def calculate_percentiles(self, players_data: List[Dict[str, Any]], 
                             stats_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Pre-calculate league percentiles for key metrics."""
        # Group stats by player
        player_stats = defaultdict(list)
        for stat in stats_data:
            player_stats[stat['player_id']].append(stat)
        
        # Calculate per_90 metrics for each player
        metrics = ['expected_goals_per_90', 'expected_assists_per_90', 
                   'expected_goal_involvements_per_90', 'recoveries']
        
        percentiles = {}
        
        for metric in metrics:
            values = []
            for player_id, stats_list in player_stats.items():
                total = sum(s.get(metric, 0) or 0 for s in stats_list)
                if total > 0:
                    values.append(total)
            
            if values:
                values_sorted = sorted(values)
                percentiles[metric] = {
                    'p50': np.percentile(values_sorted, 50),
                    'p75': np.percentile(values_sorted, 75),
                    'p90': np.percentile(values_sorted, 90),
                    'p95': np.percentile(values_sorted, 95)
                }
        
        self.league_percentiles = percentiles
        return percentiles
    
    def get_player_percentile(self, value: float, metric: str) -> float:
        """Get percentile rank for a player's metric value."""
        if metric not in self.league_percentiles:
            return 50.0
        
        percentiles = self.league_percentiles[metric]
        
        if value <= percentiles['p50']:
            return 50.0
        elif value <= percentiles['p75']:
            return 62.5
        elif value <= percentiles['p90']:
            return 82.5
        elif value <= percentiles['p95']:
            return 92.5
        else:
            return 97.5
    
    def find_similar_players(self, player_id: str, player_info: Dict[str, Any],
                            all_players: List[Dict[str, Any]], 
                            all_stats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find similar players using cosine similarity on Z-scores."""
        # Check cache first
        if player_id in self.similar_players_cache:
            return self.similar_players_cache[player_id]
        
        position = player_info.get('position', '')
        
        # Define metrics by position group
        position_metrics = {
            'Goalkeeper': ['saves_per_90', 'clean_sheets_per_90', 'goals_conceded_per_90'],
            'Defender': ['tackles', 'clearances_blocks_interceptions', 'defensive_contribution_per_90'],
            'Midfielder': ['creativity', 'expected_assists_per_90', 'recoveries', 'ict_index'],
            'Forward': ['expected_goals_per_90', 'threat', 'ict_index']
        }
        
        # Get metrics for this position
        metrics = position_metrics.get(position, ['ict_index'])
        
        # Aggregate stats for target player
        target_stats = [s for s in all_stats if s['player_id'] == player_id]
        if not target_stats:
            return []
        
        target_vector = self._calculate_player_vector(target_stats, metrics)
        
        # Calculate vectors for all players in same position
        similar_players = []
        
        for other_player in all_players:
            other_id = other_player['player_id']
            if other_id == player_id:
                continue
            
            other_position = other_player.get('position', '')
            if other_position != position:
                continue
            
            other_stats = [s for s in all_stats if s['player_id'] == other_id]
            if not other_stats:
                continue
            
            other_vector = self._calculate_player_vector(other_stats, metrics)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(target_vector, other_vector)
            score = ((similarity + 1) / 2) * 100
            
            similar_players.append({
                'player_id': other_id,
                'name': other_player.get('name', ''),
                'club_name': other_player.get('club_name', ''),
                'match_score': round(score, 1)
            })
        
        # Sort by match score and return top 5
        similar_players.sort(key=lambda x: x['match_score'], reverse=True)
        result = similar_players[:5]
        
        # Cache result
        self.similar_players_cache[player_id] = result
        
        return result
    
    def _calculate_player_vector(self, stats_list: List[Dict[str, Any]], 
                                 metrics: List[str]) -> np.ndarray:
        """Calculate aggregated vector for a player."""
        vector = []
        for metric in metrics:
            total = sum(s.get(metric, 0) or 0 for s in stats_list)
            vector.append(total)
        return np.array(vector)
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    def scout_players(self, players_data: List[Dict[str, Any]],
                     all_stats: List[Dict[str, Any]],
                     position_filter: str,
                     targets: Dict[str, float],
                     age_range: tuple = None,
                     market_value_range: tuple = None,
                     contract_year: int = None) -> List[Dict[str, Any]]:
        """Scout players based on role requirements."""
        results = []
        
        # Group stats by player
        player_stats = defaultdict(list)
        for stat in all_stats:
            player_stats[stat['player_id']].append(stat)
        
        for player in players_data:
            player_id = player['player_id']
            position = player.get('position', '')
            
            # Filter by position
            if position_filter and position != position_filter:
                continue
            
            # Apply hard filters
            if age_range:
                # Calculate age from date_of_birth would go here
                pass
            
            if market_value_range:
                mv = player.get('market_value_in_eur', 0) or 0
                if mv < market_value_range[0] or mv > market_value_range[1]:
                    continue
            
            # Calculate match score
            stats_list = player_stats.get(player_id, [])
            if not stats_list:
                continue
            
            scores = []
            
            # xG/90
            xg_per_90 = sum(s.get('expected_goals_per_90', 0) or 0 for s in stats_list)
            xg_percentile = self.get_player_percentile(xg_per_90, 'expected_goals_per_90')
            scores.append(100 - abs(xg_percentile - targets.get('xg_per_90', 50)))
            
            # xA/90
            xa_per_90 = sum(s.get('expected_assists_per_90', 0) or 0 for s in stats_list)
            xa_percentile = self.get_player_percentile(xa_per_90, 'expected_assists_per_90')
            scores.append(100 - abs(xa_percentile - targets.get('xa_per_90', 50)))
            
            # xGI/90
            xgi_per_90 = sum(s.get('expected_goal_involvements_per_90', 0) or 0 for s in stats_list)
            xgi_percentile = self.get_player_percentile(xgi_per_90, 'expected_goal_involvements_per_90')
            scores.append(100 - abs(xgi_percentile - targets.get('xgi_per_90', 50)))
            
            # Recoveries
            recoveries = sum(s.get('recoveries', 0) or 0 for s in stats_list)
            rec_percentile = self.get_player_percentile(recoveries, 'recoveries')
            scores.append(100 - abs(rec_percentile - targets.get('recoveries', 50)))
            
            total_score = sum(scores) / len(scores) if scores else 0
            
            results.append({
                'player_id': player_id,
                'name': player.get('name', ''),
                'club_name': player.get('club_name', ''),
                'position': position,
                'match_score': round(total_score, 1)
            })
        
        # Sort by match score
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return results
    
    def clear_cache(self):
        """Clear all caches."""
        self.similar_players_cache.clear()
