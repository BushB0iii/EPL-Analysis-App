# EPL Scout 25/26

Desktop application for scouting Premier League players.

## Project Structure

```
/epl_scout
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── data/                  # CSV data files
│   ├── clubs.csv
│   ├── playersinfo.csv
│   └── playerstats.csv
├── core/                  # Business logic layer
│   ├── __init__.py
│   ├── database.py        # Database management
│   └── algorithms.py      # Algorithms (similar players, scouting)
├── utils/                 # Utilities
│   ├── __init__.py
│   └── charts.py          # Chart generation
└── ui/                    # UI components
    └── views/
        ├── __init__.py
        └── home_view.py
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
cd epl_scout
streamlit run app.py
```

## Features

- **Players Hub**: Browse and filter all players
- **Scouting**: Find players matching your ideal profile
- **Watchlist**: Track and rate players
- **Player Dashboard**: Detailed stats, charts, and performance analysis

## Architecture

- **Loose Coupling**: UI separated from business logic
- **Data Boundary**: Only standard Python types (Dict, List) passed between layers
- **Database Integrity**: Normalized SQLite schema with foreign keys

## Color Scheme

- Background: #1A1A1A (Dark)
- Surface: #2D2D2D (Card background)
- Primary: #FFD700 (Yellow accent)
- Text Primary: #FFFFFF
- Text Secondary: #B0B0B0
