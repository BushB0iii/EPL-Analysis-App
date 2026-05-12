"""
EPL Scout 25/26 - Home View
Main dashboard with Bento Grid layout
"""
import flet as ft
from typing import Callable


class HomeView:
    """Home view with navigation cards."""
    
    def __init__(self, on_navigate: Callable[[str], None]):
        self.on_navigate = on_navigate
        
    def build(self) -> ft.Control:
        """Build the home view."""
        # Color scheme
        bg_color = "#1A1A1A"
        surface_color = "#2D2D2D"
        primary_color = "#FFD700"
        text_primary = "#FFFFFF"
        text_secondary = "#B0B0B0"
        
        def create_nav_card(title: str, subtitle: str, icon: str, 
                           navigate_to: str) -> ft.Container:
            """Create a navigation card."""
            return ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=40, color=primary_color),
                    ft.Text(title, size=18, weight="bold", color=text_primary),
                    ft.Text(subtitle, size=12, color=text_secondary),
                ], alignment="center", horizontal_alignment="center"),
                bgcolor=surface_color,
                border_radius=10,
                padding=30,
                on_click=lambda e: self.on_navigate(navigate_to),
                ink=True,
                width=300,
                height=200,
            )
        
        content = ft.Column([
            ft.Container(
                content=ft.Text("EPL SCOUT 25/26", size=32, weight="bold", 
                               color=primary_color),
                padding=ft.padding.only(top=20, bottom=20),
            ),
            ft.Container(
                content=ft.Row([
                    create_nav_card("PLAYERS HUB", "Browse all players", 
                                   ft.icons.PERSON, "players_hub"),
                    create_nav_card("SCOUTING", "Find ideal profiles", 
                                   ft.icons.SEARCH, "scouting"),
                    create_nav_card("MY WATCHLIST", "Track your players", 
                                   ft.icons.STAR, "watchlist"),
                ], alignment="center", spacing=30),
                padding=20,
            ),
            ft.Container(
                content=ft.Row([
                    ft.Text("60+ Players", size=14, color=text_secondary),
                    ft.Text(" | ", size=14, color=text_secondary),
                    ft.Text("20 Clubs", size=14, color=text_secondary),
                ], alignment="center"),
                padding=ft.padding.only(top=20),
            ),
        ], alignment="start", horizontal_alignment="center")
        
        return ft.Container(
            content=content,
            bgcolor=bg_color,
            expand=True,
        )
