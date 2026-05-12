"""
EPL Scout 25/26 - Core Application Module
Main entry point and application orchestration
"""

import flet as ft
from typing import Dict, Optional
from app.data.database import DatabaseManager
from app.data.data_loader import DataLoader
from app.core.state_manager import AppState
from app.ui.views.home_view import HomeView
from app.ui.views.player_hub_view import PlayerHubView
from app.ui.views.scouting_view import ScoutingView
from app.ui.views.watchlist_view import WatchlistView
from app.ui.views.player_dashboard_view import PlayerDashboardView


class EPLScoutApp:
    """Main Application Class - Orchestrates all components"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.db: Optional[DatabaseManager] = None
        self.data_loader: Optional[DataLoader] = None
        self.state: Optional[AppState] = None
        
        # View instances
        self.home_view: Optional[HomeView] = None
        self.player_hub_view: Optional[PlayerHubView] = None
        self.scouting_view: Optional[ScoutingView] = None
        self.watchlist_view: Optional[WatchlistView] = None
        self.player_dashboard_view: Optional[PlayerDashboardView] = None
        
        # Navigation stack
        self.navigation_stack: list = []
        
    def initialize(self, e: ft.ControlEvent):
        """Initialize application components"""
        try:
            # Setup page
            self.page.title = "EPL Scout 25/26"
            self.page.window.width = 1280
            self.page.window.height = 800
            self.page.theme_mode = ft.ThemeMode.DARK
            self.page.bgcolor = "#1A1A1A"
            
            # Initialize database
            self.db = DatabaseManager("epl_scout.db")
            self.db.initialize_schema()
            
            # Initialize data loader
            self.data_loader = DataLoader(
                db=self.db,
                clubs_path="clubs.csv",
                playersinfo_path="playersinfo.csv",
                playerstats_path="playerstats.csv"
            )
            self.data_loader.load_all_data()
            
            # Initialize state manager
            self.state = AppState(
                league_percentiles=self.data_loader.calculate_league_percentiles(),
                watchlist_cache={},
                similar_players_cache={}
            )
            
            # Initialize views
            self._initialize_views()
            
            # Navigate to home
            self._navigate_to("home")
            
            # Show success snackbar
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Application initialized successfully!"),
                bgcolor="#4CAF50",
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Initialization error: {str(ex)}"),
                bgcolor="#F44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
            raise
    
    def _initialize_views(self):
        """Initialize all view instances"""
        self.home_view = HomeView(
            app=self,
            on_navigate=self._navigate_to
        )
        self.player_hub_view = PlayerHubView(
            app=self,
            on_navigate=self._navigate_to
        )
        self.scouting_view = ScoutingView(
            app=self,
            on_navigate=self._navigate_to
        )
        self.watchlist_view = WatchlistView(
            app=self,
            on_navigate=self._navigate_to
        )
        self.player_dashboard_view = PlayerDashboardView(
            app=self,
            on_navigate=self._navigate_to
        )
    
    def _navigate_to(self, view_name: str, **kwargs):
        """Navigate to a specific view"""
        # Clear current content
        self.page.content = None
        
        # Get the appropriate view
        if view_name == "home":
            view = self.home_view.build()
        elif view_name == "player_hub":
            view = self.player_hub_view.build(**kwargs)
        elif view_name == "scouting":
            view = self.scouting_view.build(**kwargs)
        elif view_name == "watchlist":
            view = self.watchlist_view.build(**kwargs)
        elif view_name == "player_dashboard":
            player_id = kwargs.get("player_id")
            view = self.player_dashboard_view.build(player_id=player_id)
        else:
            view = self.home_view.build()
        
        # Set new content
        self.page.content = view
        self.page.update()
    
    def go_back(self):
        """Navigate back to previous view"""
        if len(self.navigation_stack) > 1:
            self.navigation_stack.pop()
            previous_view = self.navigation_stack[-1]
            self._navigate_to(previous_view)


def main(page: ft.Page):
    """Main entry point for Flet application"""
    app = EPLScoutApp(page)
    
    # Add initialization button
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("EPL Scout 25/26", size=32, weight="bold", color="#FFD700"),
                    ft.Text("Click below to initialize the application", color="#B0B0B0"),
                    ft.ElevatedButton(
                        "Initialize Application",
                        icon=ft.icons.PLAY_ARROW,
                        bgcolor="#FFD700",
                        color="#1A1A1A",
                        on_click=app.initialize,
                        height=50,
                        width=300,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )
    )
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
