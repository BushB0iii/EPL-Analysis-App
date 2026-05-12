"""
EPL Scout 25/26 - Player Hub View Module
Browse and filter all players
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


class PlayerHubView:
    """Player Hub View - Browse and filter players"""
    
    def __init__(self, app, on_navigate: Callable):
        self.app = app
        self.on_navigate = on_navigate
        
        # State
        self.current_filters: Dict[str, Any] = {}
        self.current_page = 1
        self.items_per_page = 25
        self.all_players: List[Dict] = []
        self.filtered_players: List[Dict] = []
        
        # Controls references
        self.position_dropdown = None
        self.club_dropdown = None
        self.search_field = None
        self.players_table = None
        self.page_info = None
    
    def build(self, **kwargs) -> ft.Container:
        """Build the player hub view"""
        # Load data
        self._load_data()
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    self._build_header(),
                    self._build_filters(),
                    self._build_results_table(),
                ],
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=30,
            expand=True,
        )
    
    def _load_data(self):
        """Load players and clubs data"""
        if self.app.db:
            self.all_players = self.app.db.get_all_players()
            self.filtered_players = self.all_players.copy()
    
    def _build_header(self) -> ft.Container:
        """Build header section"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        icon_color=COLORS['primary'],
                        on_click=lambda e: self.on_navigate("home"),
                    ),
                    ft.Text(
                        "Players Hub",
                        size=28,
                        weight="bold",
                        color=COLORS['text_primary'],
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
        )
    
    def _build_filters(self) -> ft.Container:
        """Build filters row"""
        # Get clubs for dropdown
        clubs = []
        if self.app.db:
            clubs = self.app.db.get_all_clubs()
        
        self.position_dropdown = ft.Dropdown(
            label="Position",
            options=[
                ft.dropdown.Option("Goalkeeper"),
                ft.dropdown.Option("Defender"),
                ft.dropdown.Option("Midfielder"),
                ft.dropdown.Option("Forward"),
            ],
            width=180,
            on_change=self._apply_filters,
            text_color=COLORS['text_primary'],
            label_style=ft.TextStyle(color=COLORS['text_secondary']),
        )
        
        self.club_dropdown = ft.Dropdown(
            label="Club",
            options=[ft.dropdown.Option(c['club_name']) for c in clubs],
            width=200,
            on_change=self._apply_filters,
            text_color=COLORS['text_primary'],
            label_style=ft.TextStyle(color=COLORS['text_secondary']),
        )
        
        self.search_field = ft.TextField(
            label="Search Player",
            hint_text="Name...",
            width=250,
            on_change=self._on_search_change,
            text_color=COLORS['text_primary'],
            label_style=ft.TextStyle(color=COLORS['text_secondary']),
            prefix_icon=ft.icons.SEARCH,
        )
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    self.position_dropdown,
                    self.club_dropdown,
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Market Value (€)", color=COLORS['text_secondary'], size=12),
                                ft.RangeSlider(
                                    min=0,
                                    max=100000000,
                                    divisions=100,
                                    active_color=COLORS['primary'],
                                    on_change_end=self._on_market_value_change,
                                ),
                            ],
                            spacing=5,
                        ),
                        width=250,
                    ),
                    self.search_field,
                    ft.ElevatedButton(
                        "Reset Filters",
                        icon=ft.icons.REFRESH,
                        bgcolor=COLORS['secondary'],
                        color=COLORS['text_primary'],
                        on_click=self._reset_filters,
                    ),
                ],
                wrap=True,
            ),
            padding=ft.padding.all(15),
            bgcolor=COLORS['surface'],
            border_radius=10,
        )
    
    def _build_results_table(self) -> ft.Container:
        """Build players results table"""
        self.players_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name", color=COLORS['text_primary'])),
                ft.DataColumn(ft.Text("Position", color=COLORS['text_primary'])),
                ft.DataColumn(ft.Text("Club", color=COLORS['text_primary'])),
                ft.DataColumn(ft.Text("Market Value", color=COLORS['text_primary'])),
            ],
            rows=self._build_table_rows(),
            heading_row_color=COLORS['surface'],
            data_row_color=COLORS['background'],
        )
        
        self.page_info = ft.Text(
            f"Showing {len(self.filtered_players)} players",
            color=COLORS['text_secondary'],
            size=12,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.page_info,
                            ft.Spacer(),
                            ft.IconButton(
                                icon=ft.icons.CHEVRON_LEFT,
                                on_click=self._previous_page,
                                icon_color=COLORS['text_primary'],
                            ),
                            ft.Text(f"Page {self.current_page}", color=COLORS['text_primary']),
                            ft.IconButton(
                                icon=ft.icons.CHEVRON_RIGHT,
                                on_click=self._next_page,
                                icon_color=COLORS['text_primary'],
                            ),
                        ],
                    ),
                    self.players_table,
                ],
            ),
        )
    
    def _build_table_rows(self) -> list:
        """Build table rows from filtered players"""
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_players = self.filtered_players[start_idx:end_idx]
        
        rows = []
        for player in page_players:
            market_value = player.get('market_value_in_eur', 0) or 0
            mv_formatted = f"€{market_value:,}" if market_value > 0 else "-"
            
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(
                                player.get('name', ''),
                                color=COLORS['primary'],
                                weight="bold",
                            ),
                            on_click=lambda e, p=player: self._on_player_click(p),
                        ),
                        ft.DataCell(ft.Text(player.get('position', '-'), color=COLORS['text_secondary'])),
                        ft.DataCell(ft.Text(player.get('club_name', '-'), color=COLORS['text_secondary'])),
                        ft.DataCell(ft.Text(mv_formatted, color=COLORS['text_secondary'])),
                    ],
                )
            )
        
        return rows
    
    def _on_search_change(self, e: ft.ControlEvent):
        """Handle search input with debounce"""
        # Simple implementation - in production use proper debounce
        self._apply_filters(e)
    
    def _on_market_value_change(self, e: ft.ControlEvent):
        """Handle market value range change"""
        self._apply_filters(e)
    
    def _apply_filters(self, e: ft.ControlEvent = None):
        """Apply all filters to players list"""
        self.filtered_players = self.all_players.copy()
        
        # Position filter
        if self.position_dropdown and self.position_dropdown.value:
            self.filtered_players = [
                p for p in self.filtered_players
                if p.get('position') == self.position_dropdown.value
            ]
        
        # Club filter
        if self.club_dropdown and self.club_dropdown.value:
            self.filtered_players = [
                p for p in self.filtered_players
                if p.get('club_name') == self.club_dropdown.value
            ]
        
        # Search filter
        if self.search_field and self.search_field.value:
            search_term = self.search_field.value.lower()
            self.filtered_players = [
                p for p in self.filtered_players
                if search_term in (p.get('name', '') or '').lower()
                or search_term in (p.get('first_name', '') or '').lower()
                or search_term in (p.get('last_name', '') or '').lower()
            ]
        
        # Reset to first page
        self.current_page = 1
        
        # Update table
        self._update_table()
    
    def _reset_filters(self, e: ft.ControlEvent):
        """Reset all filters"""
        if self.position_dropdown:
            self.position_dropdown.value = None
        if self.club_dropdown:
            self.club_dropdown.value = None
        if self.search_field:
            self.search_field.value = ""
        
        self.filtered_players = self.all_players.copy()
        self.current_page = 1
        self._update_table()
    
    def _update_table(self):
        """Update the players table"""
        if self.players_table:
            self.players_table.rows = self._build_table_rows()
            self.players_table.update()
        
        if self.page_info:
            self.page_info.value = f"Showing {len(self.filtered_players)} players"
            self.page_info.update()
    
    def _previous_page(self, e: ft.ControlEvent):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self._update_table()
    
    def _next_page(self, e: ft.ControlEvent):
        """Go to next page"""
        max_pages = (len(self.filtered_players) + self.items_per_page - 1) // self.items_per_page
        if self.current_page < max_pages:
            self.current_page += 1
            self._update_table()
    
    def _on_player_click(self, player: Dict[str, Any]):
        """Handle player click - navigate to dashboard"""
        player_id = player.get('player_id')
        if player_id:
            self.on_navigate("player_dashboard", player_id=player_id)
