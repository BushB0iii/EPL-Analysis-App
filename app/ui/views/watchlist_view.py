"""
EPL Scout 25/26 - Watchlist View Module
Manage personal player watchlist
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


class WatchlistView:
    """Watchlist View - Manage watched players"""
    
    def __init__(self, app, on_navigate: Callable):
        self.app = app
        self.on_navigate = on_navigate
        
        # State
        self.watchlist_players: List[Dict] = []
        self.sort_by = "name"
        
        # Controls
        self.search_field = None
        self.position_filter = None
        self.club_filter = None
        self.watchlist_table = None
    
    def build(self, **kwargs) -> ft.Container:
        """Build the watchlist view"""
        self._load_watchlist()
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    self._build_header(),
                    self._build_toolbar(),
                    self._build_watchlist_table(),
                ],
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=30,
            expand=True,
        )
    
    def _load_watchlist(self):
        """Load watchlist from database"""
        if self.app.db:
            self.watchlist_players = self.app.db.get_watchlist()
    
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
                        "My Watchlist",
                        size=28,
                        weight="bold",
                        color=COLORS['text_primary'],
                    ),
                    ft.Spacer(),
                    ft.ElevatedButton(
                        "Delete All",
                        icon=ft.icons.DELETE_FOREVER,
                        bgcolor="#F44336",
                        color=COLORS['text_primary'],
                        on_click=self._delete_all,
                    ),
                ],
            ),
        )
    
    def _build_toolbar(self) -> ft.Container:
        """Build toolbar with filters"""
        self.search_field = ft.TextField(
            label="Search",
            hint_text="Player name...",
            width=200,
            on_change=self._apply_filters,
            text_color=COLORS['text_primary'],
            prefix_icon=ft.icons.SEARCH,
        )
        
        self.position_filter = ft.Dropdown(
            label="Position",
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("Goalkeeper"),
                ft.dropdown.Option("Defender"),
                ft.dropdown.Option("Midfielder"),
                ft.dropdown.Option("Forward"),
            ],
            width=150,
            on_change=self._apply_filters,
            text_color=COLORS['text_primary'],
        )
        
        self.club_filter = ft.Dropdown(
            label="Club",
            options=[ft.dropdown.Option("All")],
            width=150,
            on_change=self._apply_filters,
            text_color=COLORS['text_primary'],
        )
        
        # Load clubs for filter
        if self.app.db:
            clubs = self.app.db.get_all_clubs()
            self.club_filter.options.extend([
                ft.dropdown.Option(c['club_name']) for c in clubs
            ])
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    self.search_field,
                    self.position_filter,
                    self.club_filter,
                ],
                wrap=True,
            ),
            padding=15,
            bgcolor=COLORS['surface'],
            border_radius=10,
        )
    
    def _build_watchlist_table(self) -> ft.Container:
        """Build watchlist table"""
        self.watchlist_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name", color=COLORS['text_primary'])),
                ft.DataColumn(ft.Text("Club", color=COLORS['text_primary'])),
                ft.DataColumn(ft.Text("Position", color=COLORS['text_primary'])),
                ft.DataColumn(ft.Text("Notes", color=COLORS['text_primary'])),
                ft.DataColumn(ft.Text("Rating", color=COLORS['text_primary'])),
                ft.DataColumn(ft.Text("Actions", color=COLORS['text_primary'])),
            ],
            rows=self._build_table_rows(),
            heading_row_color=COLORS['surface'],
            data_row_color=COLORS['background'],
        )
        
        # Check for empty state
        if not self.watchlist_players:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.icons.STAR_BORDER,
                            size=64,
                            color=COLORS['secondary'],
                        ),
                        ft.Text(
                            "Your watchlist is empty. Add players from the Hub.",
                            color=COLORS['text_secondary'],
                        ),
                        ft.ElevatedButton(
                            "Go to Players Hub",
                            icon=ft.icons.PERSON_SEARCH,
                            bgcolor=COLORS['primary'],
                            color="#1A1A1A",
                            on_click=lambda e: self.on_navigate("player_hub"),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                alignment=ft.alignment.center,
                padding=50,
            )
        
        return ft.Container(
            content=self.watchlist_table,
        )
    
    def _build_table_rows(self) -> list:
        """Build table rows"""
        rows = []
        
        for player in self.watchlist_players:
            rating = player.get('rating', 0) or 0
            
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
                        ft.DataCell(ft.Text(player.get('club_name', '-'), color=COLORS['text_secondary'])),
                        ft.DataCell(ft.Text(player.get('position', '-'), color=COLORS['text_secondary'])),
                        ft.DataCell(
                            ft.TextField(
                                value=player.get('notes', ''),
                                hint_text="Add notes...",
                                width=200,
                                text_size=12,
                                content_padding=ft.padding.all(8),
                                on_change=lambda e, p=player: self._update_notes(p, e.control.value),
                                text_color=COLORS['text_primary'],
                            )
                        ),
                        ft.DataCell(
                            self._build_rating_stars(rating, player.get('player_id', ''))
                        ),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                icon_color="#F44336",
                                on_click=lambda e, p=player: self._delete_player(p),
                            )
                        ),
                    ],
                )
            )
        
        return rows
    
    def _build_rating_stars(self, rating: int, player_id: str) -> ft.Row:
        """Build clickable star rating"""
        stars = []
        for i in range(1, 6):
            star = ft.IconButton(
                icon=ft.icons.STAR if i <= rating else ft.icons.STAR_BORDER,
                icon_color=COLORS['primary'] if i <= rating else COLORS['secondary'],
                icon_size=20,
                on_click=lambda e, r=i, pid=player_id: self._update_rating(pid, r),
                tooltip=f"Rate {i} stars",
            )
            stars.append(star)
        
        return ft.Row(controls=stars, spacing=0)
    
    def _apply_filters(self, e: ft.ControlEvent):
        """Apply filters to watchlist"""
        filtered = self.watchlist_players.copy()
        
        # Search filter
        if self.search_field and self.search_field.value:
            search_term = self.search_field.value.lower()
            filtered = [
                p for p in filtered
                if search_term in (p.get('name', '') or '').lower()
            ]
        
        # Position filter
        if self.position_filter and self.position_filter.value and self.position_filter.value != "All":
            filtered = [
                p for p in filtered
                if p.get('position') == self.position_filter.value
            ]
        
        # Club filter
        if self.club_filter and self.club_filter.value and self.club_filter.value != "All":
            filtered = [
                p for p in filtered
                if p.get('club_name') == self.club_filter.value
            ]
        
        self.watchlist_players = filtered
        self._update_table()
    
    def _update_table(self):
        """Update the watchlist table"""
        if self.watchlist_table:
            self.watchlist_table.rows = self._build_table_rows()
            self.watchlist_table.update()
    
    def _update_rating(self, player_id: str, rating: int):
        """Update player rating"""
        if self.app.db:
            self.app.db.update_watchlist_rating(player_id, rating)
            self._load_watchlist()
            self._update_table()
    
    def _update_notes(self, player: Dict, notes: str):
        """Update player notes"""
        player_id = player.get('player_id')
        if player_id and self.app.db:
            self.app.db.update_watchlist_notes(player_id, notes)
    
    def _delete_player(self, player: Dict):
        """Delete player from watchlist"""
        player_id = player.get('player_id')
        if player_id and self.app.db:
            self.app.db.remove_from_watchlist(player_id)
            self._load_watchlist()
            self._update_table()
    
    def _delete_all(self, e: ft.ControlEvent):
        """Delete all players from watchlist"""
        if self.app.db:
            self.app.db.clear_watchlist()
            self._load_watchlist()
            self._update_table()
    
    def _on_player_click(self, player: Dict):
        """Handle player click"""
        player_id = player.get('player_id')
        if player_id:
            self.on_navigate("player_dashboard", player_id=player_id)
