import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import logging
from typing import Optional, Tuple
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def validate_artist(artist_name: str, cursor: sqlite3.Cursor) -> bool:
    """
    Validate if the artist exists in the database.
    
    Args:
        artist_name (str): Name of the artist to validate
        cursor (sqlite3.Cursor): Database cursor
        
    Returns:
        bool: True if artist exists, False otherwise
    """
    cursor.execute("SELECT COUNT(*) FROM Artist WHERE Name = ?", (artist_name,))
    count = cursor.fetchone()[0]
    if count == 0:
        logging.warning(f"Artist '{artist_name}' not found in database")
        return False
    return True

def get_artist_popularity(artist_name: str, db_name: str = "CWDatabase.db") -> Optional[pd.DataFrame]:
    """
    Get artist's popularity statistics across genres.
    
    Args:
        artist_name (str): Name of the artist to analyze
        db_name (str): Database file name
        
    Returns:
        Optional[pd.DataFrame]: DataFrame with popularity statistics or None if error
    """
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Validate artist first
        if not validate_artist(artist_name, cursor):
            suggestions = get_similar_artists(artist_name, cursor)
            if suggestions:
                print("\nDid you mean one of these artists?")
                for suggestion in suggestions:
                    print(f"- {suggestion}")
            return None

        # Get artist's popularity by genre
        query_artist = """
            SELECT 
                g.Genre,
                ROUND(AVG(s.Popularity), 2) as ArtistPopularity,
                COUNT(*) as SongCount
            FROM Song s
            JOIN Artist a ON s.ArtistID = a.ID
            JOIN SongGenre sg ON s.ID = sg.SongID
            JOIN Genre g ON sg.GenreID = g.ID
            WHERE a.Name = ?
            GROUP BY g.Genre
        """
        
        # Get overall genre popularity
        query_overall = """
            SELECT 
                g.Genre,
                ROUND(AVG(s.Popularity), 2) as OverallPopularity,
                COUNT(*) as TotalSongs
            FROM Song s
            JOIN SongGenre sg ON s.ID = sg.SongID
            JOIN Genre g ON sg.GenreID = g.ID
            GROUP BY g.Genre
        """

        # Execute queries
        df_artist = pd.read_sql_query(query_artist, conn, params=(artist_name,))
        df_overall = pd.read_sql_query(query_overall, conn)

        # Merge results
        df = pd.merge(df_artist, df_overall, on='Genre', how='left')
        
        # Calculate difference and highlight
        df['Difference'] = df['ArtistPopularity'] - df['OverallPopularity']
        df['AboveMean'] = df['Difference'] > 0
        
        # Sort by artist popularity
        df = df.sort_values('ArtistPopularity', ascending=False)
        
        conn.close()
        return df

    except Exception as e:
        logging.error(f"Error getting artist popularity: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return None

def get_similar_artists(name: str, cursor: sqlite3.Cursor, limit: int = 3) -> list:
    """
    Get similar artist names for suggestions.
    
    Args:
        name (str): Input artist name
        cursor (sqlite3.Cursor): Database cursor
        limit (int): Maximum number of suggestions
        
    Returns:
        list: List of similar artist names
    """
    # Try exact match first
    cursor.execute("SELECT Name FROM Artist WHERE Name = ?", (name,))
    exact = cursor.fetchall()
    if exact:
        return [row[0] for row in exact]
    
    # Split name into parts
    name_parts = name.lower().split()
    
    # Try to find artists with similar name parts
    placeholders = ' OR '.join(['Name LIKE ?' for _ in name_parts])
    query = f"""
        SELECT Name, COUNT(*) as matches 
        FROM Artist 
        WHERE {placeholders}
        GROUP BY Name
        ORDER BY matches DESC, length(Name)
        LIMIT ?
    """
    
    # Create parameters with wildcards for each name part
    params = [f"%{part}%" for part in name_parts] + [limit]
    
    cursor.execute(query, params)
    return [row[0] for row in cursor.fetchall()]

def display_popularity_table(df: pd.DataFrame, artist_name: str):
    """
    Display formatted popularity statistics table.
    
    Args:
        df (pd.DataFrame): DataFrame with popularity statistics
        artist_name (str): Name of the artist
    """
    print(f"\nPopularity table for {artist_name}:")
    print("=" * 60)
    
    # Format table for display
    display_df = df[['Genre', 'ArtistPopularity', 'OverallPopularity', 'AboveMean']]
    
    # Format numbers and highlight above average
    for idx, row in display_df.iterrows():
        artist_pop = row['ArtistPopularity']
        overall_pop = row['OverallPopularity']
        is_above = row['AboveMean']
        
        formatted_row = [
            row['Genre'],
            f"\033[1m{artist_pop:.1f}\033[0m" if is_above else f"{artist_pop:.1f}",
            f"{overall_pop:.1f}"
        ]
        
        print(f"{formatted_row[0]:<15} {formatted_row[1]:>10} {formatted_row[2]:>15}")
    
    print("=" * 60)
    print("Note: Bold values indicate above-average popularity")

def create_popularity_chart(df: pd.DataFrame, artist_name: str):
    """
    Create and display popularity comparison chart.
    
    Args:
        df (pd.DataFrame): DataFrame with popularity statistics
        artist_name (str): Name of the artist
    """
    plt.figure(figsize=(12, 6))
    
    x = np.arange(len(df['Genre']))
    width = 0.35
    
    # Create bars
    plt.bar(x - width/2, df['ArtistPopularity'], width, label=f"{artist_name}'s Popularity",
            color=['green' if above else 'lightgreen' for above in df['AboveMean']])
    plt.bar(x + width/2, df['OverallPopularity'], width, label='Overall Genre Average',
            color='lightgray')
    
    plt.xlabel('Genre')
    plt.ylabel('Popularity')
    plt.title(f'Popularity Comparison for {artist_name}')
    plt.xticks(x, df['Genre'], rotation=45, ha='right')
    plt.legend()
    
    # Add value labels on bars
    for i, v in enumerate(df['ArtistPopularity']):
        plt.text(i - width/2, v, f'{v:.1f}', ha='center', va='bottom')
    for i, v in enumerate(df['OverallPopularity']):
        plt.text(i + width/2, v, f'{v:.1f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.show()

def analyze_artist(artist_name: str) -> None:
    """
    Analyze and display artist popularity across genres.
    This function is called by the menu system.
    
    Args:
        artist_name (str): Name of the artist to analyze
        
    Raises:
        ValueError: If the artist is not found
        Exception: If there's an error processing the data
    """
    try:
        # Get popularity statistics
        df = get_artist_popularity(artist_name)
        
        if df is None or df.empty:
            raise ValueError(f"No data available for artist: {artist_name}")
        
        # Display results
        display_popularity_table(df, artist_name)
        create_popularity_chart(df, artist_name)
        
    except ValueError as ve:
        logging.error(f"Value error: {str(ve)}")
        raise
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise

def main():
    """
    Main function for command-line usage.
    """
    try:
        # Get artist name from user
        artist_name = input("\nEnter the artist's name: ").strip()
        analyze_artist(artist_name)
    except ValueError as ve:
        print(f"\nError: {str(ve)}")
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please check the logs for details.")

if __name__ == "__main__":
    main()