import pandas as pd
import sqlite3
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_and_clean_data(csv_file: str) -> pd.DataFrame:
    """
    Load and clean the song dataset from CSV file.
    
    Args:
        csv_file (str): Path to the CSV file containing song data
        
    Returns:
        pd.DataFrame: Cleaned DataFrame with properly formatted columns
    """
    try:
        # Load data from csv file
        logging.info(f"Loading data from {csv_file}")
        dfSongs = pd.read_csv(csv_file)
        
        # Convert duration from milliseconds to seconds and round to nearest integer
        dfSongs['duration'] = (dfSongs['duration_ms'] / 1000).round().astype(int)
        
        # Drop the original duration_ms column
        dfSongs.drop(columns=['duration_ms'], inplace=True)
        
        # Ensure year is properly handled
        dfSongs['year'] = pd.to_numeric(dfSongs['year'], errors='coerce')
        dfSongs = dfSongs.dropna(subset=['year'])
        dfSongs['year'] = dfSongs['year'].astype(int)
        
        # Log year statistics
        year_stats = dfSongs['year'].value_counts().sort_index()
        logging.info("Year distribution in dataset:")
        for year, count in year_stats.items():
            logging.info(f"Year {year}: {count} songs")
        
        # Clean genre data: split comma-separated genres and strip whitespace
        dfSongs['genres'] = dfSongs['genre'].str.split(',').apply(
            lambda x: [g.strip() for g in x] if isinstance(x, list) else []
        )
        
        # Remove any empty genres or 'set()'
        dfSongs['genres'] = dfSongs['genres'].apply(
            lambda x: [g for g in x if g and g != 'set()']
        )
        
        logging.info("Data loading and cleaning completed successfully")
        return dfSongs
    
    except Exception as e:
        logging.error(f"Error in load_and_clean_data: {str(e)}")
        raise

def filter_data(dfSongs: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the songs dataset based on specified criteria.
    
    Args:
        dfSongs (pd.DataFrame): Input DataFrame containing song data
        
    Returns:
        pd.DataFrame: Filtered DataFrame meeting all criteria
    """
    try:
        # Verify data types before filtering
        logging.info("\nVerifying data types:")
        logging.info(f"Year dtype: {dfSongs['year'].dtype}")
        logging.info(f"Popularity dtype: {dfSongs['popularity'].dtype}")
        logging.info(f"Danceability dtype: {dfSongs['danceability'].dtype}")
        
        # Log year distribution before filtering
        year_stats_before = dfSongs['year'].value_counts().sort_index()
        logging.info("\nYear distribution before filtering:")
        for year, count in year_stats_before.items():
            logging.info(f"Year {year}: {count} songs")
        
        # Convert popularity to numeric if needed
        dfSongs['popularity'] = pd.to_numeric(dfSongs['popularity'], errors='coerce')
        dfSongs['danceability'] = pd.to_numeric(dfSongs['danceability'], errors='coerce')
        
        # Apply filters with proper null handling
        dfFiltered = dfSongs[
            (dfSongs['popularity'].notna()) & 
            (dfSongs['popularity'] > 50) &
            (dfSongs['danceability'].notna()) &
            (dfSongs['danceability'] > 0.20) &
            (dfSongs['speechiness'].notna()) &
            (dfSongs['speechiness'].between(0.33, 0.66))
        ]
        
        # Log year distribution after filtering
        year_stats_after = dfFiltered['year'].value_counts().sort_index()
        logging.info("\nYear distribution after filtering:")
        for year, count in year_stats_after.items():
            logging.info(f"Year {year}: {count} songs")
            
        # Log filtering impact per year
        logging.info("\nFiltering impact per year:")
        for year in sorted(set(year_stats_before.index)):
            before = year_stats_before.get(year, 0)
            after = year_stats_after.get(year, 0)
            if before > 0:
                retained = (after / before) * 100
                logging.info(f"Year {year}: {before} -> {after} songs ({retained:.1f}% retained)")
        
        # Print artists that match the criteria
        print("\nArtists with songs matching the criteria:")
        print("----------------------------------------")
        matching_artists = dfFiltered['artist'].unique()
        for artist in sorted(matching_artists):
            artist_songs = dfFiltered[dfFiltered['artist'] == artist]
            print(f"{artist}: {len(artist_songs)} matching songs")
            
        logging.info(f"\nFiltered data from {len(dfSongs)} to {len(dfFiltered)} records")
        return dfFiltered
    
    except Exception as e:
        logging.error(f"Error in filter_data: {str(e)}")
        raise

def create_database_schema(cursor: sqlite3.Cursor):
    """
    Create the database schema with proper tables and relationships.
    
    Args:
        cursor (sqlite3.Cursor): Database cursor for executing SQL commands
    """
    # Drop existing tables to start fresh
    tables = ['Song', 'Artist', 'Genre', 'SongGenre']
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    
    # Create Artist table
    cursor.execute('''
        CREATE TABLE Artist (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create Genre table
    cursor.execute('''
        CREATE TABLE Genre (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Genre TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create Song table
    cursor.execute('''
        CREATE TABLE Song (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Title TEXT NOT NULL,
            Duration INTEGER NOT NULL,
            Explicit BOOLEAN NOT NULL,
            Year INTEGER NOT NULL,
            Popularity INTEGER NOT NULL,
            Danceability FLOAT NOT NULL,
            Speechiness FLOAT NOT NULL,
            ArtistID INTEGER NOT NULL,
            FOREIGN KEY (ArtistID) REFERENCES Artist(ID)
        )
    ''')
    
    # Create SongGenre junction table for many-to-many relationship
    cursor.execute('''
        CREATE TABLE SongGenre (
            SongID INTEGER,
            GenreID INTEGER,
            PRIMARY KEY (SongID, GenreID),
            FOREIGN KEY (SongID) REFERENCES Song(ID),
            FOREIGN KEY (GenreID) REFERENCES Genre(ID)
        )
    ''')

def create_and_populate_database(df: pd.DataFrame, db_name: str = "CWDatabase.db"):
    """
    Create and populate the SQLite database with the processed song data.
    
    Args:
        df (pd.DataFrame): Processed DataFrame containing song data
        db_name (str): Name of the SQLite database file
    """
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Create database schema
        create_database_schema(cursor)
        
        # Insert unique artists and create mapping
        unique_artists = df['artist'].unique()
        artist_id_map = {}
        for artist in unique_artists:
            cursor.execute("INSERT INTO Artist (Name) VALUES (?)", (artist,))
            artist_id_map[artist] = cursor.lastrowid
        
        # Insert unique genres and create mapping
        unique_genres = set()
        for genres in df['genres']:
            unique_genres.update(genres)
        
        genre_id_map = {}
        for genre in unique_genres:
            cursor.execute("INSERT INTO Genre (Genre) VALUES (?)", (genre,))
            genre_id_map[genre] = cursor.lastrowid
        
        # Prepare and insert song data
        for _, row in df.iterrows():
            # Insert song
            cursor.execute('''
                INSERT INTO Song (Title, Duration, Explicit, Year, Popularity, 
                                Danceability, Speechiness, ArtistID)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['song'],
                row['duration'],
                row['explicit'],
                row['year'],
                row['popularity'],
                row['danceability'],
                row['speechiness'],
                artist_id_map[row['artist']]
            ))
            song_id = cursor.lastrowid
            
            # Insert song-genre relationships
            for genre in row['genres']:
                cursor.execute('''
                    INSERT INTO SongGenre (SongID, GenreID)
                    VALUES (?, ?)
                ''', (song_id, genre_id_map[genre]))
        
        conn.commit()
        conn.close()
        logging.info(f"Database {db_name} created and populated successfully")
        
    except Exception as e:
        logging.error(f"Error in create_and_populate_database: {str(e)}")
        if 'conn' in locals():
            conn.close()
        raise

def main():
    """
    Main function to perform data preprocessing.
    This function is called by the menu system.
    
    Returns:
        bool: True if preprocessing was successful, False otherwise
    """
    try:
        csv_file = "songs.csv"
        logging.info("Starting data preprocessing...")
        
        # Load and clean data
        dfSongs = load_and_clean_data(csv_file)
        
        # Apply filters
        dfFiltered = filter_data(dfSongs)
        
        # Create and populate database
        create_and_populate_database(dfFiltered)
        
        logging.info("Data preprocessing completed successfully")
        return True
        
    except Exception as e:
        logging.error(f"Preprocessing failed: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Preprocessing failed: {str(e)}")