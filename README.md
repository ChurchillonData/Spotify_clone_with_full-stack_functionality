# Spotify Song Analysis and Visualization Tool

# 📌 Project Overview

This project develops a Spotify Song Dataset Analyser, leveraging a publicly available dataset of top Spotify tracks (1998–2020). The tool cleans, filters, and stores song data in an SQLite database, then performs various analyses, including:
✅ Genre-based statistics for a given year

✅ Artist popularity comparisons across genres

✅ Top 5 artist ranking within a user-defined timeframe

✅ Visualizations using Matplotlib

The dataset includes details such as song title, artist, duration, popularity, danceability, energy, and genre, enabling insights into musical trends.


📂 Project Structure

📂 Spotify-Song-Analysis/
##### ├── 📂 data/                # Contains songs.csv dataset  
 ├── 📂 scripts/             # Python scripts for different analyses  
 │   ├── CW_Preprocessing.py  # Data cleaning & SQLite storage  
 │   ├── Genres.py           # Genre-based statistics for a given year  
 │   ├── Artist.py           # Artist popularity comparison across genres  
 │   ├── Top5.py             # Top 5 artists ranking based on criteria  
 ├── 📂 results/             # Stores generated plots and analysis reports  
 ├── 📜 CWDatabase.db        # SQLite database storing the cleaned dataset  
 ├── 📜 README.md            # Project documentation  
 ├── 📜 requirements.txt      # Dependencies (Pandas, Matplotlib, SQLite)  
 ├── 📜 .gitignore           # Ignore unnecessary files (e.g., large datasets)  



# 🔍 Dataset Description

The dataset, songs.csv, consists of 2000 top Spotify tracks between 1998 and 2020, including:

🔹 Column Name	Description

🔹 song	Song title

🔹 artist	Artist name

🔹 duration	Song length (seconds)

🔹 year	Release year

🔹 popularity	Popularity score (0-100)

🔹 danceability	Danceability metric (0-1)

🔹 energy	Energy level (0-1)

🔹 speechiness	Spoken word percentage (0-1)

🔹 genre	Genre classification





# 🛠 Features and Functionality

### 1. Data Preprocessing & Storage (CW_Preprocessing.py)

🔹 Loads the dataset into a Pandas DataFrame

🔹 Renames and formats columns (e.g., duration_ms → duration in seconds)

🔹 Filters data:

🔹	Popularity >50 (focus on recognized tracks)

🔹	Speechiness between 0.33 and 0.66 (moderate speech content)

🔹	Danceability >0.20 (tracks with rhythm)

🔹 Stores cleaned data into SQLite database (CWDatabase.db)



### 2. Genre-Based Analysis (Genres.py)

🔹 User inputs a year (1998-2020) 

🔹 Retrieves records for that year from SQLite

🔹 Computes average danceability, total songs, and popularity per genre

🔹 Displays results in a table

🔹 Generates a pie chart visualization using Matplotlib




### 3. Artist Popularity Analysis (Artist.py)

🔹 User inputs an artist’s name

🔹 Fetches the artist’s average song popularity per genre

🔹 Compares it to overall genre popularity

🔹 Highlights genres where the artist is above average

🔹 Generates a bar chart comparing artist vs. overall genre popularity



### 4. Top 5 Artists Ranking (Top5.py)

🔹 User inputs start and end year

🔹 Retrieves songs released in that period

🔹 Calculates ranking value (e.g., Songs Count × Weight + Avg. Popularity × Weight)

🔹 Displays Top 5 artists, highlighting yearly leaders

🔹 Generates a line chart for ranking trends over time



# 📖 How to Run the Project

##### Prerequisites

Ensure you have Python installed along with the required libraries:

pip install -r requirements.txt

 Running the Programs
 
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





# 💡 Future Improvements

🔹 Expand dataset beyond 2020

🔹 Add more features (e.g., tempo, key, loudness)

🔹 Improve ranking formula for Top 5 Artists




 
