"""
EPL Scout 25/26 - Scouting View Module
Role-based player search
"""

import flet as ft
from typing import Callable, Dict, Any, List


COLORS = {
    'background': '#1A1A1A',
    'surface': '#2D2D2D',
    'primary': '#FFD700',
    'secondary': '#4A4A4A',
    'text_primary': '#FFFFFF',
    'text_secondary': '#B0B0B0',
}


class ScoutingView:
    """Scouting View - Role-based player search"""
    
    def __init__(self, app, on_navigate: Callable):
        self.app = app
        self.on_navigate = on_navigate
        
        # State
        self.position_group = "DEF"
        self.slider_values = {
            'xg_per_90': 50,
            'xa_per_90': 50,
            'xgi_per_90': 50,
            'recoveries': 50,
        }
        self.search_results: List[Dict] = []
        
        # Controls
        self.position_dropdown = None
        self.xg_slider = None
        self.xa_slider = None
        self.xgi_slider = None
        self.recoveries_slider = None
        self.results_table = None
    
    def build(self, **kwargs) -> ft.Container:
        """Build the scouting view"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    self._build_header(),
                    self._build_position_section(),
                    self._build_profile_section(),
                    self._build_hard_filters_section(),
                    self._build_search_button(),
                    self._build_results_section(),
                ],
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=30,
            expand=True,
        )
    
    def _build_header(self) -> ft.Container:
        """Build header"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        icon_color=COLORS['primary'],
                        on_click=lambda e: self.on_navigate("home"),
                    ),
                    ft.Text(
                        "Scouting",
                        size=28,
                        weight="bold",
                        color=COLORS['text_primary'],
                    ),
                ],
            ),
        )
    
    def _build_position_section(self) -> ft.Container:
        """Build position group selection"""
        self.position_dropdown = ft.Dropdown(
            label="Position Group",
            options=[
                ft.dropdown.Option("GK", "Goalkeeper"),
                ft.dropdown.Option("DEF", "Defender"),
                ft.dropdown.Option("MID", "Midfielder"),
                ft.dropdown.Option("FWD", "Forward"),
            ],
            value="DEF",
            width=250,
            text_color=COLORS['text_primary'],
            label_style=ft.TextStyle(color=COLORS['text_secondary']),
            on_change=self._on_position_change,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Select Position Group", size=18, weight="bold", color=COLORS['text_primary']),
                    self.position_dropdown,
                ],
                spacing=10,
            ),
            padding=15,
            bgcolor=COLORS['surface'],
            border_radius=10,
        )
    
    def _build_profile_section(self) -> ft.Container:
        """Build ideal profile sliders"""
        self.xg_slider = ft.Slider(
            min=50,
            max=95,
            divisions=45,
            value=50,
            label="{value}th percentile",
            active_color=COLORS['primary'],
            on_change=self._update_slider_label,
        )
        
        self.xa_slider = ft.Slider(
            min=50,
            max=95,
            divisions=45,
            value=50,
            label="{value}th percentile",
            active_color=COLORS['primary'],
            on_change=self._update_slider_label,
        )
        
        self.xgi_slider = ft.Slider(
            min=50,
            max=95,
            divisions=45,
            value=50,
            label="{value}th percentile",
            active_color=COLORS['primary'],
            on_change=self._update_slider_label,
        )
        
        self.recoveries_slider = ft.Slider(
            min=50,
            max=95,
            divisions=45,
            value=50,
            label="{value}th percentile",
            active_color=COLORS['primary'],
            on_change=self._update_slider_label,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Define Your Ideal Profile", size=18, weight="bold", color=COLORS['text_primary']),
                    ft.Divider(color=COLORS['secondary']),
                    self._build_slider_row("xG/90", self.xg_slider),
                    self._build_slider_row("xA/90", self.xa_slider),
                    self._build_slider_row("xGI/90", self.xgi_slider),
                    self._build_slider_row("Recoveries/90", self.recoveries_slider),
                ],
                spacing=15,
            ),
            padding=15,
            bgcolor=COLORS['surface'],
            border_radius=10,
        )
    
    def _build_slider_row(self, label: str, slider: ft.Slider) -> ft.Row:
        """Build a single slider row"""
        return ft.Row(
            controls=[
                ft.Text(label, width=120, color=COLORS['text_secondary']),
                slider,
                ft.Text("Good → Elite", width=100, color=COLORS['text_secondary'], size=12),
            ],
            alignment=ft.MainAxisAlignment.START,
        )
    
    def _build_hard_filters_section(self) -> ft.Container:
        """Build collapsible hard filters"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Hard Filters (Optional)", size=18, weight="bold", color=COLORS['text_primary']),
                    ft.Text("Market Value and Contract filters can be applied", color=COLORS['text_secondary']),
                ],
                spacing=10,
            ),
            padding=15,
            bgcolor=COLORS['surface'],
            border_radius=10,
        )
    
    def _build_search_button(self) -> ft.Container:
        """Build search button"""
        return ft.Container(
            content=ft.ElevatedButton(
                "SEARCH",
                icon=ft.icons.SEARCH,
                bgcolor=COLORS['primary'],
                color="#1A1A1A",
                height=50,
                width=200,
                on_click=self._perform_search,
            ),
            alignment=ft.alignment.center,
        )
    
    def _build_results_section(self) -> ft.Container:
        """Build results section"""
        self.results_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Rank", color=COLORS['text_primary'])),
                ft.DataColumn(ft.Text("Player", color=COLORS['text_primary'])),
                ft.DataColumn(ft.Text("Club", color=COLORS['text_primary'])),
                ft.DataColumn(ft.Text("Match Score", color=COLORS['text_primary'])),
            ],
            rows=[],
            heading_row_color=COLORS['surface'],
            data_row_color=COLORS['background'],
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Search Results", size=18, weight="bold", color=COLORS['text_primary']),
                    self.results_table,
                ],
                spacing=15,
            ),
            padding=15,
            bgcolor=COLORS['surface'],
            border_radius=10,
        )
    
    def _on_position_change(self, e: ft.ControlEvent):
        """Handle position group change"""
        self.position_group = e.control.value
    
    def _update_slider_label(self, e: ft.ControlEvent):
        """Update slider value labels"""
        pass
    
    def _perform_search(self, e: ft.ControlEvent):
        """Perform player search"""
        if not self.app.data_loader or not self.app.state:
            return
        
        # Get slider values
        targets = {
            'xg_per_90': self.xg_slider.value if self.xg_slider else 50,
            'xa_per_90': self.xa_slider.value if self.xa_slider else 50,
            'xgi_per_90': self.xgi_slider.value if self.xgi_slider else 50,
            'recoveries_per_90': self.recoveries_slider.value if self.recoveries_slider else 50,
        }
        
        # Hard filters (empty for now)
        hard_filters = {}
        
        # Use scouting algorithm
        from core.algorithms import ScoutingAlgorithm
        
        algorithm = ScoutingAlgorithm(
            db=self.app.db,
            data_loader=self.app.data_loader,
            league_percentiles=self.app.state.league_percentiles,
        )
        
        results = algorithm.search_players(
            position_group=self.position_group,
            targets=targets,
            hard_filters=hard_filters,
        )
        
        self.search_results = results
        self._update_results_table()
    
    def _update_results_table(self):
        """Update results table with search results"""
        if not self.results_table:
            return
        
        rows = []
        for idx, result in enumerate(self.search_results[:20], 1):  # Show top 20
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(idx), color=COLORS['text_secondary'])),
                        ft.DataCell(
                            ft.Text(
                                result.get('name', ''),
                                color=COLORS['primary'],
                                weight="bold",
                            ),
                            on_click=lambda e, r=result: self._on_player_click(r),
                        ),
                        ft.DataCell(ft.Text(result.get('club_name', '-'), color=COLORS['text_secondary'])),
                        ft.DataCell(
                            ft.Text(
                                f"{result.get('match_score', 0):.1f}%",
                                color=COLORS['primary'],
                                weight="bold",
                            )
                        ),
                    ],
                )
            )
        
        self.results_table.rows = rows
        self.results_table.update()
    
    def _on_player_click(self, result: Dict[str, Any]):
        """Handle player click"""
        player_id = result.get('player_id')
        if player_id:
            self.on_navigate("player_dashboard", player_id=player_id)
