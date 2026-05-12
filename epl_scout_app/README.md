# EPL Scout 25/26 - Desktop Application

Ứng dụng desktop scouting cầu thủ Premier League với giao diện Streamlit.

## 🚀 Cài đặt

### Yêu cầu hệ thống
- Python 3.8+
- pip

### Cài đặt dependencies

```bash
cd epl_scout_app
pip install -r requirements.txt
```

### Chạy ứng dụng

```bash
streamlit run app.py
```

Ứng dụng sẽ mở tại: `http://localhost:8501`

## 📁 Cấu trúc dự án

```
epl_scout_app/
├── app.py                      # Main application (UI layer)
├── core/
│   ├── database.py             # Database manager (Data Access layer)
│   └── algorithms.py           # Business logic & algorithms
├── utils/
│   └── charts.py               # Chart generation utilities
├── data/
│   ├── clubs.csv               # Club data
│   ├── playersinfo.csv         # Player info data
│   └── playerstats.csv         # Player statistics
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🏗️ Kiến trúc

### Loose Coupling (Ghép nối lỏng)
- **UI Layer** (`app.py`): Chỉ xử lý hiển thị và bắt sự kiện
- **Business Logic Layer** (`core/algorithms.py`): Thuật toán similar players, scouting
- **Data Access Layer** (`core/database.py`): Truy vấn SQLite
- **Utilities** (`utils/charts.py`): Tạo biểu đồ

### Data Boundary
- Giao tiếp giữa các tầng chỉ sử dụng: `Dict`, `List`, `Tuple`
- Không truyền DB Cursor hay UI objects giữa các tầng

### Database Integrity
- Schema chuẩn hóa với Foreign Keys
- Bảng `clubs`, `playersinfo`, `playerstats`, `watchlist`
- Quan hệ 1-nhiều: club → players, player → stats

## ⚽ Tính năng

### 1. Home Dashboard
- Bento Grid layout với 3 cards chính
- Stats tổng quan

### 2. Players Hub
- Filter theo Position, Club, Market Value
- Search bar real-time
- Pagination 25 players/page
- Click vào player → Player Dashboard

### 3. Scouting (Role Search)
- Select Position Group (GK/DEF/MID/FWD)
- 4 Sliders: xG/90, xA/90, xGI/90, Recoveries/90
- Hard Filters: Age, Market Value, Contract
- Algorithm tính Match Score dựa trên percentile

### 4. Watchlist
- Xem danh sách cầu thủ đã lưu
- Rating 1-5 stars
- Notes inline editing
- Search & filter
- Delete individual/all

### 5. Player Dashboard
#### Tab Overview:
- Player image & info
- Performance Radar Chart (theo position)
- Season Statistics
- Find Similar Players button (Cosine Similarity algorithm)
- Add to Watchlist

#### Tab GW Records:
- Table gameweek records
- Summary stats

#### Tab Performance:
- Bar Chart: Minutes per GW
- Line Chart: Goals vs xG (cumulative)
- Line Chart: Assists vs xA (cumulative)
- Multi-line Chart: ICT Index Components
- GK only: Saves vs Goals Conceded

## 🎨 Theme & Colors

- Background: `#1A1A1A` (Dark)
- Surface: `#2D2D2D` (Card background)
- Primary: `#FFD700` (Yellow accent)
- Text Primary: `#FFFFFF`
- Text Secondary: `#B0B0B0`

## 🔧 Algorithms

### Similar Players
1. Filter cùng position group
2. Z-Score normalization
3. Cosine Similarity calculation
4. Match Score = ((similarity + 1) / 2) * 100
5. Cache results

### Scouting
1. Apply hard filters (age, value, contract)
2. Calculate player percentiles
3. Score = 100 - abs(player_percentile - target_percentile)
4. Sort by average score DESC

## 📊 Database Schema

### clubs
- club_id (PK), club_name

### playersinfo
- player_id (PK), name, club_id (FK), position, market_value, ...

### playerstats
- player_id (FK), gw, minutes, goals, assists, xG, xA, ...
- PK: (player_id, gw)

### watchlist
- watchlist_id (PK), player_id (FK), rating, notes

## 🛠️ Dependencies

- streamlit >= 1.28.0
- pandas >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- scikit-learn >= 1.3.0

## 📝 Lưu ý

- Ứng dụng sử dụng SQLite local file (`epl_scout.db`)
- Charts được cache để tối ưu performance
- Session state quản lý navigation và current player
