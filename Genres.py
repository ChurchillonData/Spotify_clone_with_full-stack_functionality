import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def validate_year(year: int) -> bool:
    """
    Validate if the input year is within the valid range.
    
    Args:
        year (int): Year to validate
        
    Returns:
        bool: True if year is valid, False otherwise
    """
    try:
        year_int = int(year)
        is_valid = 1998 <= year_int <= 2020
        if not is_valid:
            logging.warning(f"Year {year} is outside valid range (1998-2020)")
        return is_valid
    except (ValueError, TypeError):
        logging.error(f"Invalid year value: {year}")
        return False

def check_database_years(db_name: str = "CWDatabase.db") -> None:
    """
    Diagnostic function to check year data in the database.
    
    Args:
        db_name (str): Database file name
    """
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Check all distinct years
        cursor.execute("SELECT DISTINCT Year FROM Song ORDER BY Year")
        years = cursor.fetchall()
        print("\nDistinct years in database:")
        print("==========================")
        for year in years:
            print(f"Year: {year[0]}")
            
        # Check song count per year
        cursor.execute("""
            SELECT Year, COUNT(*) as count
            FROM Song
            GROUP BY Year
            ORDER BY Year
        """)
        counts = cursor.fetchall()
        print("\nSong count per year:")
        print("===================")
        for year, count in counts:
            print(f"Year {year}: {count} songs")
            
        conn.close()
        
    except Exception as e:
        logging.error(f"Database diagnostic error: {str(e)}")
        if 'conn' in locals():
            conn.close()

def get_genre_statistics(year: int, db_name: str = "CWDatabase.db", debug: bool = False, min_songs: int = 10) -> Optional[pd.DataFrame]:
    """
    Retrieve genre statistics for a specific year from the database.
    
    Args:
        year (int): Year to analyze
        db_name (str): Database file name
        
    Returns:
        Optional[pd.DataFrame]: DataFrame containing genre statistics or None if no data
    """
    try:
        # Validate year first
        if not validate_year(year):
            logging.error(f"Invalid year provided: {year}")
            return None
            
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Check total song count for the year
        cursor.execute("SELECT COUNT(*) FROM Song WHERE Year = ?", (year,))
        song_count = cursor.fetchone()[0]
        
        if song_count == 0:
            # Find nearest years with data
            cursor.execute("""
                SELECT Year, COUNT(*) as count 
                FROM Song 
                GROUP BY Year 
                HAVING count > ? 
                ORDER BY ABS(Year - ?) 
                LIMIT 2
            """, (min_songs, year))
            alternatives = cursor.fetchall()
            
            msg = f"\nNo songs available for the year {year}."
            if alternatives:
                years_str = ", ".join(str(y) for y, _ in alternatives)
                msg += f" Consider using these years instead: {years_str}"
            print(msg)
            return None
            
        elif song_count < min_songs:
            # Find nearest years with more songs
            cursor.execute("""
                SELECT Year, COUNT(*) as count 
                FROM Song 
                GROUP BY Year 
                HAVING count > ? 
                ORDER BY ABS(Year - ?) 
                LIMIT 2
            """, (min_songs, year))
            better_years = cursor.fetchall()
            
            print(f"\nWarning: Limited data available for {year} (only {song_count} songs).")
            print("The statistics might not be representative of the entire year.")
            if better_years:
                years_str = ", ".join(f"{y} ({c} songs)" for y, c in better_years)
                print(f"Consider these years with more data: {years_str}")
            
        if debug:
            logging.info(f"\nDebug information for year {year}:")
            logging.info(f"Total songs found: {song_count}")
            
            # Get genre distribution
            cursor.execute("""
                SELECT g.Genre, COUNT(*) as count
                FROM Song s
                JOIN SongGenre sg ON s.ID = sg.SongID
                JOIN Genre g ON sg.GenreID = g.ID
                WHERE s.Year = ?
                GROUP BY g.Genre
                ORDER BY count DESC
                LIMIT 3
            """, (year,))
            top_genres = cursor.fetchall()
            if top_genres:
                logging.info("\nTop 3 genres:")
                for genre, count in top_genres:
                    logging.info(f"- {genre}: {count} songs")
            
            # Get sample songs
            cursor.execute("""
                SELECT Title, Artist.Name, s.Popularity 
                FROM Song s
                JOIN Artist ON s.ArtistID = Artist.ID 
                WHERE Year = ? 
                ORDER BY s.Popularity DESC
                LIMIT 5
            """, (year,))
            samples = cursor.fetchall()
            if samples:
                logging.info("\nTop 5 popular songs:")
                for title, artist, popularity in samples:
                    logging.info(f"- {title} by {artist} (Popularity: {popularity})")
        
        query = """
            WITH GenreSongs AS (
                SELECT 
                    g.Genre,
                    s.Danceability,
                    s.Popularity,
                    s.Speechiness,
                    COUNT(*) OVER (PARTITION BY g.Genre) as TotalSongs
                FROM Song s
                JOIN SongGenre sg ON s.ID = sg.SongID
                JOIN Genre g ON sg.GenreID = g.ID
                WHERE s.Year = ?
            )
            SELECT 
                Genre,
                ROUND(AVG(Danceability), 3) as AvgDanceability,
                ROUND(AVG(Popularity), 1) as AvgPopularity,
                ROUND(AVG(Speechiness), 3) as AvgSpeechiness,
                COUNT(*) as SongCount,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as Percentage
            FROM GenreSongs
            GROUP BY Genre
            ORDER BY SongCount DESC;
        """
        
        df = pd.read_sql_query(query, conn, params=(year,))
        conn.close()
        
        return df if not df.empty else None
        
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        return None

def display_statistics(df: pd.DataFrame, year: int):
    """
    Display formatted genre statistics.
    
    Args:
        df (pd.DataFrame): DataFrame containing genre statistics
        year (int): Year being analyzed
    """
    print(f"\nSongs in Year {year}:")
    print("=" * 80)
    
    # Format the DataFrame for display
    formatted_df = df.copy()
    formatted_df['AvgPopularity'] = formatted_df['AvgPopularity'].map('{:.1f}'.format)
    formatted_df['AvgDanceability'] = formatted_df['AvgDanceability'].map('{:.3f}'.format)
    formatted_df['AvgSpeechiness'] = formatted_df['AvgSpeechiness'].map('{:.3f}'.format)
    formatted_df['Percentage'] = formatted_df['Percentage'].map('{:.1f}%'.format)
    
    # Rename columns for better display
    formatted_df.columns = ['Genre', 'Avg Danceability', 'Avg Popularity', 
                          'Avg Speechiness', 'Total Songs', 'Percentage']
    
    print(formatted_df.to_string(index=False))
    print("=" * 80)

def create_visualizations(df: pd.DataFrame, year: int):
    """
    Create and display visualizations for genre statistics.
    
    Args:
        df (pd.DataFrame): DataFrame containing genre statistics
        year (int): Year being analyzed
    """
    
    # Pie chart for song distribution by genres
    plt.pie(df['SongCount'], labels=df['Genre'], autopct='%1.1f%%', 
            startangle=90)
    plt.title(f'Song Distribution by Genre ({year})')
    plt.legend()
    plt.tight_layout()
    plt.show()

def analyze_year(year: int) -> None:
    """
    Analyze and display genre statistics for a specific year.
    
    Args:
        year (int): The year to analyze (must be between 1998-2020)
    
    Raises:
        ValueError: If the year is invalid
        Exception: If there's an error processing the data
    """
    try:
        if not validate_year(year):
            raise ValueError(f"Invalid year: {year}. Year must be between 1998 and 2020.")
        
        # Get statistics
        df = get_genre_statistics(year, debug=False)
        
        if df is None:
            raise ValueError(f"No data available for the year {year}.")
        
        # Display statistics and visualizations
        display_statistics(df, year)
        create_visualizations(df, year)
        
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
        # Get year input from user
        while True:
            try:
                year = int(input("\nEnter year (1998-2020): "))
                analyze_year(year)
                break
            except ValueError as ve:
                print(f"Error: {str(ve)}")
            except Exception as e:
                print(f"Error: {str(e)}")
                break
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")

if __name__ == "__main__":
    main()