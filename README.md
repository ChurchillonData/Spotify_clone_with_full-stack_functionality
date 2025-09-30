# 🎵 Spotify Song Dataset Analyser

##  Project Overview

This project builds a full-stack Spotify Song Dataset Analyzer using a public dataset of top Spotify tracks (1998–2020). It involves cleaning and storing data in SQLite, performing analytical queries, and generating insightful visualisations with Matplotlib.

**Key Features:**
- Genre-based statistics for a specific year  
- Artist popularity comparisons across genres  
- Top 5 artist ranking within a custom timeframe  
- Visual analytics for trend discovery  

The dataset includes metadata like song title, artist, duration, popularity, danceability, energy, and genre

---
##  Dataset Description

**Filename:** `songs.csv`  
**Timeframe:** 1998–2020  
**Total Tracks:** 2000  

| Column        | Description                          |
|---------------|--------------------------------------|
| `song`        | Title of the song                    |
| `artist`      | Artist name                          |
| `duration`    | Length in seconds                    |
| `year`        | Year of release                      |
| `popularity`  | Popularity score (0–100)             |
| `danceability`| Danceability metric (0–1)            |
| `energy`      | Energy level (0–1)                   |
| `speechiness` | Spoken word content (0–1)            |
| `genre`       | Genre category                       |

---

##  Features and Functionality

### 1. Data Preprocessing & Storage  
**Script:** `CW_Preprocessing.py`
- Loads and formats dataset
- Filters out:
  - Popularity ≤ 50  
  - Speechiness outside 0.33–0.66  
  - Danceability ≤ 0.20  
- Saves cleaned data to `CWDatabase.db`

---

### 2. Genre-Based Analysis  
**Script:** `Genres.py`
- User inputs a year (1998–2020)
- Calculates genre-wise average danceability, popularity, and song count
- Displays results in table and pie chart

---

### 3. Artist Popularity Analysis  
**Script:** `Artist.py`
- User inputs artist name
- Compares artist’s genre-wise popularity with overall genre averages
- Generates comparative bar chart

---

### 4. Top 5 Artists Ranking  
**Script:** `Top5.py`
- User inputs start and end year
- Calculates a weighted ranking score per artist
- Displays Top 5 artists and generates trend line chart

---

##  How to Run the Project

### Prerequisites  
Install required dependencies:  
pip install -r requirements.txt


1.	Data Preprocessing & Storage

python scripts/CW_Preprocessing.py


	2.	Genre Analysis (User Input: Year)

python scripts/Genres.py


	3.	Artist Popularity (User Input: Artist Name)

python scripts/Artist.py


	4.	Top 5 Artists (User Input: Year Range)

python scripts/Top5.py



##### Running the GUI Menu (Jupyter Notebook)
 
	1.	Open Jupyter Notebook

jupyter notebook


	2.	Navigate to menu.ipynb and run the interactive menu.





