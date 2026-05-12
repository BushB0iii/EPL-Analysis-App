"""
EPL Scout 25/26 - Chart Utilities
Matplotlib chart generation with base64 encoding
"""
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from io import BytesIO
import base64
from typing import Dict, List, Any, Optional


class ChartGenerator:
    """Generates charts as base64-encoded images."""
    
    def __init__(self):
        self.chart_cache: Dict[str, str] = {}
        
    def _encode_chart(self, fig: plt.Figure) -> str:
        """Convert matplotlib figure to base64 string."""
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        img_bytes = buf.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        plt.close(fig)
        return f"data:image/png;base64,{img_base64}"
    
    def create_radar_chart(self, player_info: Dict[str, Any], 
                          stats: List[Dict[str, Any]]) -> str:
        """Create performance radar chart based on position."""
        position = player_info.get('position', '')
        
        # Define metrics by position
        metrics_config = {
            'Goalkeeper': {
                'labels': ['Saves/90', 'Clean Sheets/90', 'Penalties Saved', 
                          'Goals Conceded/90', 'xGC/90'],
                'keys': ['saves_per_90', 'clean_sheets_per_90', 'penalties_saved',
                        'goals_conceded_per_90', 'expected_goals_conceded_per_90']
            },
            'Defender': {
                'labels': ['Tackles', 'Clearances/Blocks/Interceptions', 
                          'Defensive Contrib/90', 'xGC/90', 'Influence'],
                'keys': ['tackles', 'clearances_blocks_interceptions', 
                        'defensive_contribution_per_90', 'expected_goals_conceded_per_90', 
                        'influence']
            },
            'Midfielder': {
                'labels': ['Creativity', 'xA/90', 'Recoveries', 'xGI/90', 'ICT Index'],
                'keys': ['creativity', 'expected_assists_per_90', 'recoveries',
                        'expected_goal_involvements_per_90', 'ict_index']
            },
            'Forward': {
                'labels': ['xG/90', 'Goals', 'Threat', 'xGI/90', 'ICT Index'],
                'keys': ['expected_goals_per_90', 'goals_scored', 'threat',
                        'expected_goal_involvements_per_90', 'ict_index']
            }
        }
        
        config = metrics_config.get(position, metrics_config['Midfielder'])
        labels = config['labels']
        keys = config['keys']
        
        # Aggregate stats
        values = []
        for key in keys:
            total = sum(s.get(key, 0) or 0 for s in stats)
            values.append(total)
        
        # Normalize values for radar chart (0-1 scale)
        max_values = [max(v, 1) for v in values]
        normalized = [v / mv for v, mv in zip(values, max_values)]
        
        # Create radar chart
        angles = [n / len(labels) * 2 * 3.14159 for n in range(len(labels))]
        angles += angles[:1]
        normalized += normalized[:1]
        
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.plot(angles, normalized, linewidth=2, color='#FFD700')
        ax.fill(angles, normalized, color='#FFD700', alpha=0.25)
        ax.set_yticklabels([])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=10, color='white')
        ax.tick_params(colors='white')
        fig.patch.set_facecolor('#1A1A1A')
        ax.set_facecolor('#2D2D2D')
        
        return self._encode_chart(fig)
    
    def create_bar_chart_gw(self, stats: List[Dict[str, Any]]) -> str:
        """Create bar chart for minutes per GW."""
        if not stats:
            return ""
        
        gws = [s.get('gw', 0) for s in stats]
        minutes = [s.get('minutes', 0) or 0 for s in stats]
        goals = [s.get('goals_scored', 0) or 0 for s in stats]
        assists = [s.get('assists', 0) or 0 for s in stats]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(gws, minutes, color='#FFD700', alpha=0.8)
        
        # Add goals and assists labels
        for i, (g, a, m) in enumerate(zip(goals, assists, minutes)):
            if m > 0:
                label = ""
                if g > 0:
                    label += f"G:{g} "
                if a > 0:
                    label += f"A:{a}"
                if label:
                    ax.text(i + 1, m + 5, label.strip(), ha='center', 
                           fontsize=8, color='white')
        
        ax.set_xlabel('Gameweek', color='white')
        ax.set_ylabel('Minutes', color='white')
        ax.set_title('Minutes per Gameweek', color='white', fontsize=12)
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        fig.patch.set_facecolor('#1A1A1A')
        ax.set_facecolor('#2D2D2D')
        
        return self._encode_chart(fig)
    
    def create_line_chart_cumulative(self, stats: List[Dict[str, Any]], 
                                    metric: str, expected_metric: str,
                                    title: str) -> str:
        """Create line chart for cumulative actual vs expected."""
        if not stats:
            return ""
        
        stats_sorted = sorted(stats, key=lambda x: x.get('gw', 0))
        
        gws = [s.get('gw', 0) for s in stats_sorted]
        actual_vals = [s.get(metric, 0) or 0 for s in stats_sorted]
        expected_vals = [s.get(expected_metric, 0) or 0 for s in stats_sorted]
        
        # Calculate cumulative
        actual_cum = []
        expected_cum = []
        acc_actual = 0
        acc_expected = 0
        
        for a, e in zip(actual_vals, expected_vals):
            acc_actual += a
            acc_expected += e
            actual_cum.append(acc_actual)
            expected_cum.append(acc_expected)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(gws, actual_cum, marker='o', linewidth=2, color='#FFD700', 
               label='Actual')
        ax.plot(gws, expected_cum, marker='s', linewidth=2, color='#4A4A4A',
               label='Expected')
        
        ax.set_xlabel('Gameweek', color='white')
        ax.set_ylabel(title, color='white')
        ax.set_title(f'{title} - Actual vs Expected', color='white', fontsize=12)
        ax.legend(facecolor='#2D2D2D', edgecolor='#FFD700', labelcolor='white')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        fig.patch.set_facecolor('#1A1A1A')
        ax.set_facecolor('#2D2D2D')
        
        return self._encode_chart(fig)
    
    def create_ict_chart(self, stats: List[Dict[str, Any]]) -> str:
        """Create multi-line chart for ICT components."""
        if not stats:
            return ""
        
        stats_sorted = sorted(stats, key=lambda x: x.get('gw', 0))
        
        gws = [s.get('gw', 0) for s in stats_sorted]
        influence = [s.get('influence', 0) or 0 for s in stats_sorted]
        creativity = [s.get('creativity', 0) or 0 for s in stats_sorted]
        threat = [s.get('threat', 0) or 0 for s in stats_sorted]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(gws, influence, marker='o', linewidth=2, color='#FFD700', 
               label='Influence')
        ax.plot(gws, creativity, marker='s', linewidth=2, color='#4CAF50',
               label='Creativity')
        ax.plot(gws, threat, marker='^', linewidth=2, color='#F44336',
               label='Threat')
        
        ax.set_xlabel('Gameweek', color='white')
        ax.set_ylabel('ICT Score', color='white')
        ax.set_title('ICT Index Components', color='white', fontsize=12)
        ax.legend(facecolor='#2D2D2D', edgecolor='#FFD700', labelcolor='white')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        fig.patch.set_facecolor('#1A1A1A')
        ax.set_facecolor('#2D2D2D')
        
        return self._encode_chart(fig)
    
    def clear_cache(self):
        """Clear chart cache."""
        self.chart_cache.clear()
