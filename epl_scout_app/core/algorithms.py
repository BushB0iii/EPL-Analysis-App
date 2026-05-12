"""
Algorithms for EPL Scout Application
Implements similar players and scouting algorithms with loose coupling.
"""
import numpy as np
from typing import Dict, List, Any, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity


class AlgorithmManager:
    """Manages all algorithmic operations independent of UI and DB."""
    
    def __init__(self):
        self.similar_players_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.league_percentiles: Dict[str, Dict[str, float]] = {}
    
    # ==================== Similar Players Algorithm ====================
    
    def find_similar_players(
        self, 
        target_player_id: str,
        target_player_stats: Dict[str, Any],
        target_player_position: str,
        all_players: List[Dict[str, Any]],
        all_player_stats: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find top 5 similar players using cosine similarity on Z-scores.
        Returns list of dicts with player info and match score.
        """
        # Check cache first
        if target_player_id in self.similar_players_cache:
            return self.similar_players_cache[target_player_id]
        
        # Position group mapping
        position_groups = {
            "Goalkeeper": ["Goalkeeper"],
            "Defender": ["Defender"],
            "Midfielder": ["Midfielder"],
            "Forward": ["Forward"]
        }
        
        target_group = position_groups.get(target_player_position, [])
        
        # Filter players by same position group
        candidates = [
            p for p in all_players 
            if p.get("position") in target_group and p["player_id"] != target_player_id
        ]
        
        if not candidates:
            return []
        
        # Define features based on position
        features = self._get_features_for_position(target_player_position)
        
        # Build feature vectors
        target_vector = self._build_feature_vector(target_player_stats, features)
        
        if target_vector is None or len(target_vector) == 0:
            return []
        
        candidate_vectors = []
        candidate_ids = []
        
        for player in candidates:
            stats = all_player_stats.get(player["player_id"], {})
            vector = self._build_feature_vector(stats, features)
            if vector is not None and len(vector) > 0:
                candidate_vectors.append(vector)
                candidate_ids.append(player["player_id"])
        
        if not candidate_vectors:
            return []
        
        # Normalize using Z-Score
        scaler = StandardScaler()
        all_vectors = [target_vector] + candidate_vectors
        try:
            normalized_vectors = scaler.fit_transform(all_vectors)
        except Exception:
            # Fallback if scaling fails (e.g., zero variance)
            normalized_vectors = np.array(all_vectors)
        
        target_normalized = normalized_vectors[0]
        candidates_normalized = normalized_vectors[1:]
        
        # Calculate cosine similarity
        similarities = cosine_similarity([target_normalized], candidates_normalized)[0]
        
        # Calculate match scores
        results = []
        for idx, sim in enumerate(similarities):
            match_score = ((sim + 1) / 2) * 100  # Scale to 0-100
            player_id = candidate_ids[idx]
            
            # Find original player data
            player_data = next(
                (p for p in candidates if p["player_id"] == player_id), 
                None
            )
            
            if player_data:
                results.append({
                    **player_data,
                    "match_score": round(match_score, 1)
                })
        
        # Sort by match score descending and take top 5
        results.sort(key=lambda x: x["match_score"], reverse=True)
        top_5 = results[:5]
        
        # Cache result
        self.similar_players_cache[target_player_id] = top_5
        
        return top_5
    
    def _get_features_for_position(self, position: str) -> List[str]:
        """Get relevant features for similarity calculation based on position."""
        if position == "Goalkeeper":
            return [
                "saves_per_90", "clean_sheets_per_90", "goals_conceded_per_90",
                "penalties_saved", "influence"
            ]
        elif position == "Defender":
            return [
                "tackles", "clearances_blocks_interceptions", 
                "defensive_contribution_per_90", "expected_goals_conceded_per_90",
                "influence"
            ]
        elif position == "Midfielder":
            return [
                "creativity", "expected_assists_per_90", "recoveries",
                "expected_goal_involvements_per_90", "ict_index"
            ]
        else:  # Forward
            return [
                "expected_goals_per_90", "goals_scored", "threat",
                "expected_goal_involvements_per_90", "ict_index"
            ]
    
    def _build_feature_vector(
        self, 
        stats: Dict[str, Any], 
        features: List[str]
    ) -> Optional[List[float]]:
        """Build feature vector from stats dict."""
        if not stats:
            return None
        
        vector = []
        for feature in features:
            value = stats.get(feature, 0)
            if value is None:
                value = 0
            try:
                vector.append(float(value))
            except (TypeError, ValueError):
                vector.append(0.0)
        
        # Check if all values are zero
        if all(v == 0 for v in vector):
            return None
        
        return vector
    
    def clear_similar_cache(self):
        """Clear the similar players cache."""
        self.similar_players_cache.clear()
    
    # ==================== Scouting Algorithm ====================
    
    def scout_players(
        self,
        candidates: List[Dict[str, Any]],
        all_player_stats: Dict[str, Dict[str, Any]],
        targets: Dict[str, float],
        hard_filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Scout players based on percentile targets and hard filters.
        Returns list of dicts sorted by match score.
        """
        # Apply hard filters first
        filtered_candidates = self._apply_hard_filters(candidates, hard_filters)
        
        if not filtered_candidates:
            return []
        
        # Calculate percentiles for each metric
        metrics = ["expected_goals_per_90", "expected_assists_per_90", 
                   "expected_goal_involvements_per_90", "recoveries"]
        
        # Get all values for percentile calculation
        metric_values = {m: [] for m in metrics}
        for player in filtered_candidates:
            stats = all_player_stats.get(player["player_id"], {})
            for metric in metrics:
                value = stats.get(metric, 0) or 0
                metric_values[metric].append(value)
        
        # Calculate percentiles
        player_scores = []
        for player in filtered_candidates:
            stats = all_player_stats.get(player["player_id"], {})
            
            total_score = 0
            valid_metrics = 0
            
            for metric in metrics:
                player_value = stats.get(metric, 0) or 0
                target_percentile = targets.get(metric, 50)
                
                # Calculate player's percentile
                values = metric_values[metric]
                if values:
                    player_percentile = self._calculate_percentile(player_value, values)
                    
                    # Score = 100 - abs difference
                    metric_score = 100 - abs(player_percentile - target_percentile)
                    total_score += metric_score
                    valid_metrics += 1
            
            if valid_metrics > 0:
                avg_score = total_score / valid_metrics
                player_scores.append({
                    **player,
                    "match_score": round(avg_score, 1)
                })
        
        # Sort by match score descending
        player_scores.sort(key=lambda x: x["match_score"], reverse=True)
        
        return player_scores
    
    def _apply_hard_filters(
        self, 
        candidates: List[Dict[str, Any]], 
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply hard filters to candidate list."""
        result = candidates
        
        # Age filter
        if filters.get("min_age") is not None or filters.get("max_age") is not None:
            filtered = []
            for player in result:
                age = self._calculate_age(player.get("date_of_birth"))
                if age is not None:
                    if filters.get("min_age") and age < filters["min_age"]:
                        continue
                    if filters.get("max_age") and age > filters["max_age"]:
                        continue
                filtered.append(player)
            result = filtered
        
        # Market value filter
        if filters.get("min_market_value") is not None:
            result = [
                p for p in result 
                if (p.get("market_value_in_eur") or 0) >= filters["min_market_value"]
            ]
        
        if filters.get("max_market_value") is not None:
            result = [
                p for p in result 
                if (p.get("market_value_in_eur") or 0) <= filters["max_market_value"]
            ]
        
        # Contract expiration filter
        if filters.get("contract_year"):
            result = [
                p for p in result 
                if self._get_contract_year(p.get("contract_expiration_date")) == filters["contract_year"]
            ]
        
        return result
    
    def _calculate_percentile(self, value: float, values: List[float]) -> float:
        """Calculate percentile of a value in a list."""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        rank = sum(1 for v in sorted_values if v < value)
        percentile = (rank / len(sorted_values)) * 100
        return round(percentile, 1)
    
    def _calculate_age(self, birth_date_str: Optional[str]) -> Optional[int]:
        """Calculate age from birth date string."""
        if not birth_date_str:
            return None
        
        try:
            from datetime import datetime
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - birth_date.year
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1
            return age
        except Exception:
            return None
    
    def _get_contract_year(self, contract_date_str: Optional[str]) -> Optional[int]:
        """Extract year from contract expiration date."""
        if not contract_date_str:
            return None
        
        try:
            from datetime import datetime
            contract_date = datetime.strptime(contract_date_str, "%Y-%m-%d")
            return contract_date.year
        except Exception:
            return None
    
    def calculate_league_percentiles(
        self, 
        all_players: List[Dict[str, Any]],
        all_player_stats: Dict[str, Dict[str, Any]]
    ):
        """Pre-calculate league percentiles for all per_90 metrics."""
        metrics = [
            "expected_goals_per_90", "expected_assists_per_90",
            "expected_goal_involvements_per_90", "expected_goals_conceded_per_90",
            "saves_per_90", "clean_sheets_per_90", "goals_conceded_per_90",
            "starts_per_90", "defensive_contribution_per_90"
        ]
        
        # Collect all values
        metric_values = {m: [] for m in metrics}
        for player in all_players:
            stats = all_player_stats.get(player["player_id"], {})
            for metric in metrics:
                value = stats.get(metric, 0) or 0
                if value > 0:  # Only include positive values
                    metric_values[metric].append(value)
        
        # Calculate percentiles for each metric
        self.league_percentiles = {}
        for metric, values in metric_values.items():
            if values:
                sorted_values = sorted(values)
                self.league_percentiles[metric] = {
                    "p25": self._percentile_value(sorted_values, 25),
                    "p50": self._percentile_value(sorted_values, 50),
                    "p75": self._percentile_value(sorted_values, 75),
                    "p90": self._percentile_value(sorted_values, 90),
                    "p95": self._percentile_value(sorted_values, 95)
                }
    
    def _percentile_value(self, sorted_values: List[float], percentile: float) -> float:
        """Get the value at a specific percentile."""
        if not sorted_values:
            return 0
        
        k = (len(sorted_values) - 1) * (percentile / 100)
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_values) else f
        
        if f == c:
            return sorted_values[f]
        
        return sorted_values[f] * (c - k) + sorted_values[c] * (k - f)
