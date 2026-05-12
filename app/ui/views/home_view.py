"""
EPL Scout 25/26 - Home View Module
Main dashboard with Bento Grid layout
"""

import flet as ft
from typing import Callable


# Color constants
COLORS = {
    'background': '#1A1A1A',
    'surface': '#2D2D2D',
    'primary': '#FFD700',
    'secondary': '#4A4A4A',
    'text_primary': '#FFFFFF',
    'text_secondary': '#B0B0B0',
    'success': '#4CAF50',
    'error': '#F44336',
}


class HomeView:
    """Home View - Main Dashboard with Bento Grid"""
    
    def __init__(self, app, on_navigate: Callable):
        self.app = app
        self.on_navigate = on_navigate
    
    def build(self) -> ft.Container:
        """Build the home view"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    self._build_header(),
                    self._build_bento_grid(),
                ],
                spacing=20,
            ),
            padding=30,
            expand=True,
        )
    
    def _build_header(self) -> ft.Container:
        """Build header section"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "EPL Scout 25/26",
                        size=36,
                        weight="bold",
                        color=COLORS['primary'],
                    ),
                    ft.Text(
                        "Professional Football Analytics Platform",
                        size=16,
                        color=COLORS['text_secondary'],
                    ),
                ],
                spacing=5,
            ),
        )
    
    def _build_bento_grid(self) -> ft.Row:
        """Build Bento Grid with 3 main cards"""
        return ft.Row(
            controls=[
                self._build_card(
                    title="PLAYERS HUB",
                    subtitle="Browse all players",
                    stats="60+ Players",
                    icon=ft.icons.PERSON_SEARCH,
                    on_click=lambda e: self.on_navigate("player_hub"),
                ),
                self._build_card(
                    title="SCOUTING",
                    subtitle="Find ideal profiles",
                    stats="Advanced Search",
                    icon=ft.icons.TUNE,
                    on_click=lambda e: self.on_navigate("scouting"),
                ),
                self._build_card(
                    title="MY WATCHLIST",
                    subtitle="Track your players",
                    stats="Personal List",
                    icon=ft.icons.STAR_BORDER,
                    on_click=lambda e: self.on_navigate("watchlist"),
                ),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
        )
    
    def _build_card(
        self,
        title: str,
        subtitle: str,
        stats: str,
        icon: str,
        on_click: Callable
    ) -> ft.GestureDetector:
        """Build a single Bento card"""
        return ft.GestureDetector(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            icon,
                            size=48,
                            color=COLORS['primary'],
                        ),
                        ft.Text(
                            title,
                            size=20,
                            weight="bold",
                            color=COLORS['text_primary'],
                        ),
                        ft.Text(
                            subtitle,
                            size=14,
                            color=COLORS['text_secondary'],
                        ),
                        ft.Container(
                            content=ft.Text(
                                stats,
                                size=12,
                                color=COLORS['primary'],
                                weight="bold",
                            ),
                            padding=ft.padding.all(8),
                            border_radius=5,
                            bgcolor=COLORS['secondary'],
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                width=300,
                height=280,
                bgcolor=COLORS['surface'],
                border_radius=15,
                padding=25,
                border=ft.border.all(1, COLORS['secondary']),
            ),
            on_hover=self._on_card_hover,
            on_click=on_click,
        )
    
    def _on_card_hover(self, e: ft.HoverEvent):
        """Handle card hover effect"""
        if e.data == "true":
            e.control.content.border = ft.border.all(2, COLORS['primary'])
        else:
            e.control.content.border = ft.border.all(1, COLORS['secondary'])
        e.control.update()
