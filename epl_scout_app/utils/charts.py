"""
Chart Generator for EPL Scout Application
Creates matplotlib charts and converts to base64 strings for UI display.
"""
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import io
import base64
from typing import Dict, List, Any, Optional


class ChartGenerator:
    """Generates charts as base64 strings with caching capability."""
    
    def __init__(self):
        self.chart_cache: Dict[str, str] = {}
    
    def create_radar_chart(
        self, 
        player_name: str,
        stats: Dict[str, Any],
        position: str
    ) -> str:
        """Create radar chart for player performance metrics."""
        cache_key = f"radar_{player_name}_{position}"
        if cache_key in self.chart_cache:
            return self.chart_cache[cache_key]
        
        # Define metrics based on position
        if position == "Goalkeeper":
            labels = ["Saves/90", "Clean Sheets/90", "Penalties Saved", 
                     "Goals Conceded/90", "xGC/90"]
            values = [
                stats.get("saves_per_90", 0) or 0,
                stats.get("clean_sheets_per_90", 0) or 0,
                stats.get("penalties_saved", 0) or 0,
                stats.get("goals_conceded_per_90", 0) or 0,
                stats.get("expected_goals_conceded_per_90", 0) or 0
            ]
        elif position == "Defender":
            labels = ["Tackles", "Clearances/Blocks/Interceptions", 
                     "Defensive Contribution/90", "xGC/90", "Influence"]
            values = [
                stats.get("tackles", 0) or 0,
                stats.get("clearances_blocks_interceptions", 0) or 0,
                stats.get("defensive_contribution_per_90", 0) or 0,
                stats.get("expected_goals_conceded_per_90", 0) or 0,
                stats.get("influence", 0) or 0
            ]
        elif position == "Midfielder":
            labels = ["Creativity", "xA/90", "Recoveries", "xGI/90", "ICT Index"]
            values = [
                stats.get("creativity", 0) or 0,
                stats.get("expected_assists_per_90", 0) or 0,
                stats.get("recoveries", 0) or 0,
                stats.get("expected_goal_involvements_per_90", 0) or 0,
                stats.get("ict_index", 0) or 0
            ]
        else:  # Forward
            labels = ["xG/90", "Goals", "Threat", "xGI/90", "ICT Index"]
            values = [
                stats.get("expected_goals_per_90", 0) or 0,
                stats.get("goals_scored", 0) or 0,
                stats.get("threat", 0) or 0,
                stats.get("expected_goal_involvements_per_90", 0) or 0,
                stats.get("ict_index", 0) or 0
            ]
        
        # Normalize values for better visualization
        max_val = max(values) if values else 1
        if max_val > 0:
            normalized_values = [(v / max_val) * 100 for v in values]
        else:
            normalized_values = values
        
        # Create radar chart
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        
        angles = [n / len(labels) * 2 * 3.14159 for n in range(len(labels))]
        angles += angles[:1]
        normalized_values += normalized_values[:1]
        
        ax.plot(angles, normalized_values, linewidth=2, color='#FFD700')
        ax.fill(angles, normalized_values, alpha=0.25, color='#FFD700')
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, color='white', size=10)
        ax.set_yticklabels([])
        
        ax.set_title(player_name, color='white', size=14, pad=20)
        
        fig.patch.set_facecolor('#1A1A1A')
        ax.set_facecolor('#2D2D2D')
        
        # Convert to base64
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
        img_bytes.seek(0)
        img_base64 = base64.b64encode(img_bytes.read()).decode()
        
        plt.close(fig)
        
        result = f"data:image/png;base64,{img_base64}"
        self.chart_cache[cache_key] = result
        return result
    
    def create_gw_minutes_chart(
        self,
        player_name: str,
        gw_stats: List[Dict[str, Any]]
    ) -> str:
        """Create bar chart for minutes per gameweek."""
        cache_key = f"gw_minutes_{player_name}"
        if cache_key in self.chart_cache:
            return self.chart_cache[cache_key]
        
        if not gw_stats:
            return self._create_placeholder("No data available")
        
        gws = [str(s.get("gw", i+1)) for i, s in enumerate(gw_stats)]
        minutes = [s.get("minutes", 0) or 0 for s in gw_stats]
        goals = [s.get("goals_scored", 0) or 0 for s in gw_stats]
        assists = [s.get("assists", 0) or 0 for s in gw_stats]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        
        bars = ax.bar(gws, minutes, color='#2D2D2D', edgecolor='#FFD700', linewidth=1.5)
        
        # Add goal/assist labels on top
        for i, (bar, g, a) in enumerate(zip(bars, goals, assists)):
            height = bar.get_height()
            label = ""
            if g > 0 and a > 0:
                label = f"{int(g)}G {int(a)}A"
            elif g > 0:
                label = f"{int(g)}G"
            elif a > 0:
                label = f"{int(a)}A"
            
            if label:
                ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                       label, ha='center', va='bottom', color='#FFD700', fontsize=9)
        
        ax.set_xlabel("Gameweek", color='white')
        ax.set_ylabel("Minutes", color='white')
        ax.set_title(f"{player_name} - Minutes per GW", color='white', pad=10)
        
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.set_facecolor('#2D2D2D')
        fig.patch.set_facecolor('#1A1A1A')
        
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
        img_bytes.seek(0)
        img_base64 = base64.b64encode(img_bytes.read()).decode()
        
        plt.close(fig)
        
        result = f"data:image/png;base64,{img_base64}"
        self.chart_cache[cache_key] = result
        return result
    
    def create_cumulative_line_chart(
        self,
        player_name: str,
        gw_stats: List[Dict[str, Any]],
        metric: str,
        expected_metric: str,
        title: str
    ) -> str:
        """Create line chart for cumulative actual vs expected metrics."""
        cache_key = f"cumulative_{metric}_{player_name}"
        if cache_key in self.chart_cache:
            return self.chart_cache[cache_key]
        
        if not gw_stats:
            return self._create_placeholder("No data available")
        
        gws = [s.get("gw", i+1) for i, s in enumerate(gw_stats)]
        
        # Calculate cumulative values
        actual_cumulative = []
        expected_cumulative = []
        actual_sum = 0
        expected_sum = 0
        
        for s in gw_stats:
            actual_sum += s.get(metric, 0) or 0
            expected_sum += s.get(expected_metric, 0) or 0
            actual_cumulative.append(actual_sum)
            expected_cumulative.append(expected_sum)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        
        ax.plot(gws, actual_cumulative, marker='o', linewidth=2, color='#FFD700', label='Actual')
        ax.plot(gws, expected_cumulative, marker='s', linewidth=2, color='#4A4A4A', label='Expected')
        
        ax.set_xlabel("Gameweek", color='white')
        ax.set_ylabel("Cumulative Total", color='white')
        ax.set_title(f"{player_name} - {title}", color='white', pad=10)
        ax.legend(facecolor='#2D2D2D', labelcolor='white')
        
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.set_facecolor('#2D2D2D')
        fig.patch.set_facecolor('#1A1A1A')
        
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
        img_bytes.seek(0)
        img_base64 = base64.b64encode(img_bytes.read()).decode()
        
        plt.close(fig)
        
        result = f"data:image/png;base64,{img_base64}"
        self.chart_cache[cache_key] = result
        return result
    
    def create_ict_chart(
        self,
        player_name: str,
        gw_stats: List[Dict[str, Any]]
    ) -> str:
        """Create multi-line chart for ICT Index components."""
        cache_key = f"ict_{player_name}"
        if cache_key in self.chart_cache:
            return self.chart_cache[cache_key]
        
        if not gw_stats:
            return self._create_placeholder("No data available")
        
        gws = [s.get("gw", i+1) for i, s in enumerate(gw_stats)]
        influence = [s.get("influence", 0) or 0 for s in gw_stats]
        creativity = [s.get("creativity", 0) or 0 for s in gw_stats]
        threat = [s.get("threat", 0) or 0 for s in gw_stats]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        
        ax.plot(gws, influence, marker='o', linewidth=2, color='#FFD700', label='Influence')
        ax.plot(gws, creativity, marker='s', linewidth=2, color='#4CAF50', label='Creativity')
        ax.plot(gws, threat, marker='^', linewidth=2, color='#F44336', label='Threat')
        
        ax.set_xlabel("Gameweek", color='white')
        ax.set_ylabel("Score", color='white')
        ax.set_title(f"{player_name} - ICT Index Components", color='white', pad=10)
        ax.legend(facecolor='#2D2D2D', labelcolor='white')
        
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.set_facecolor('#2D2D2D')
        fig.patch.set_facecolor('#1A1A1A')
        
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
        img_bytes.seek(0)
        img_base64 = base64.b64encode(img_bytes.read()).decode()
        
        plt.close(fig)
        
        result = f"data:image/png;base64,{img_base64}"
        self.chart_cache[cache_key] = result
        return result
    
    def create_gk_saves_chart(
        self,
        player_name: str,
        gw_stats: List[Dict[str, Any]]
    ) -> str:
        """Create grouped bar chart for goalkeeper saves vs goals conceded."""
        cache_key = f"gk_saves_{player_name}"
        if cache_key in self.chart_cache:
            return self.chart_cache[cache_key]
        
        if not gw_stats:
            return self._create_placeholder("No data available")
        
        gws = [str(s.get("gw", i+1)) for i, s in enumerate(gw_stats)]
        saves = [s.get("saves", 0) or 0 for s in gw_stats]
        goals_conceded = [s.get("goals_conceded", 0) or 0 for s in gw_stats]
        
        x = range(len(gws))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(10, 5))
        
        bars1 = ax.bar([i - width/2 for i in x], saves, width, label='Saves', color='#4CAF50')
        bars2 = ax.bar([i + width/2 for i in x], goals_conceded, width, label='Goals Conceded', color='#F44336')
        
        ax.set_xlabel("Gameweek", color='white')
        ax.set_ylabel("Count", color='white')
        ax.set_title(f"{player_name} - Saves vs Goals Conceded", color='white', pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(gws)
        ax.legend(facecolor='#2D2D2D', labelcolor='white')
        
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.set_facecolor('#2D2D2D')
        fig.patch.set_facecolor('#1A1A1A')
        
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
        img_bytes.seek(0)
        img_base64 = base64.b64encode(img_bytes.read()).decode()
        
        plt.close(fig)
        
        result = f"data:image/png;base64,{img_base64}"
        self.chart_cache[cache_key] = result
        return result
    
    def _create_placeholder(self, message: str) -> str:
        """Create a placeholder image with message."""
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, message, ha='center', va='center', color='white', fontsize=14)
        ax.set_facecolor('#2D2D2D')
        fig.patch.set_facecolor('#1A1A1A')
        ax.axis('off')
        
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
        img_bytes.seek(0)
        img_base64 = base64.b64encode(img_bytes.read()).decode()
        
        plt.close(fig)
        
        return f"data:image/png;base64,{img_base64}"
    
    def clear_cache(self):
        """Clear chart cache."""
        self.chart_cache.clear()
