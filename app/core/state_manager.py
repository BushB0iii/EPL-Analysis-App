"""
EPL Scout 25/26 - State Manager Module
Manages global application state
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AppState:
    """Global Application State"""
    
    # Pre-calculated data
    league_percentiles: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Caches
    watchlist_cache: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    similar_players_cache: Dict[str, list] = field(default_factory=dict)
    
    # Current view state
    current_player_id: Optional[str] = None
    previous_view: str = "home"
    
    # Player Hub state
    player_hub_filters: Dict[str, Any] = field(default_factory=dict)
    player_hub_current_page: int = 1
    
    # Scouting state
    scouting_slider_values: Dict[str, float] = field(default_factory=dict)
    scouting_results: list = field(default_factory=list)
    
    # Watchlist state
    watchlist_sort_by: str = "name"
    watchlist_filter_by: Dict[str, str] = field(default_factory=dict)
    
    def get_percentile(self, stat_name: str, value: float, position: str) -> float:
        """Get percentile for a specific stat and position"""
        key = f"{position}_{stat_name}"
        if key in self.league_percentiles:
            percentiles = self.league_percentiles[key]
            for percentile, threshold in sorted(percentiles.items(), key=lambda x: float(x[0])):
                if value <= threshold:
                    return float(percentile)
            return 95.0
        return 50.0
    
    def clear_cache(self, cache_type: str):
        """Clear specific cache"""
        if cache_type == "similar_players":
            self.similar_players_cache.clear()
        elif cache_type == "watchlist":
            self.watchlist_cache.clear()
