import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import logging
from typing import Optional, Tuple, Dict
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RankingWeights:
    """Class to hold and validate ranking weights"""
    def __init__(self, song_weight: float = 0.4, popularity_weight: float = 0.6):
        """
        Initialize ranking weights.
        
        Args:
            song_weight (float): Weight for number of songs (default: 0.4)
            popularity_weight (float): Weight for popularity (default: 0.6)
        """
        if not np.isclose(song_weight + popularity_weight, 1.0):
            raise ValueError("Weights must sum to 1.0")
        self.song_weight = song_weight
        self.popularity_weight = popularity_weight

def validate_year_range(start_year: int, end_year: int) -> bool:
    """
    Validate if the input year range is valid.
    
    Args:
        start_year (int): Start year
        end_year (int): End year
        
    Returns:
        bool: True if range is valid, False otherwise
    """
    try:
        if not (isinstance(start_year, int) and isinstance(end_year, int)):
            logging.error("Years must be integers")
            return False
            
        if start_year < 1998 or end_year > 2020:
            logging.error("Years must be between 1998 and 2020")
            return False
            
        if start_year > end_year:
            logging.error("Start year must be before or equal to end year")
            return False
            
        return True
        
    except Exception as e:
        logging.error(f"Year validation error: {str(e)}")
        return False

def calculate_ranking_value(num_songs: int, avg_popularity: float, weights: RankingWeights) -> float:
    """
    Calculate ranking value using weighted formula.
    
    The formula is:
    Rank Value = (Number of Songs × Weight₁) + (Average Popularity × Weight₂)
    where Weight₁ and Weight₂ sum to 1.0
    
    Args:
        num_songs (int): Number of songs by artist
        avg_popularity (float): Average popularity of artist's songs
        weights (RankingWeights): Weights for the formula components
        
    Returns:
        float: Calculated ranking value
    """
    # Normalize number of songs (0-100 scale like popularity)
    max_songs = 100  # Reasonable maximum for normalization
    normalized_songs = min((num_songs / max_songs) * 100, 100)
    
    return (weights.song_weight * normalized_songs) + \
           (weights.popularity_weight * avg_popularity)

def get_top_artists(start_year: int, end_year: int, weights: RankingWeights, 
                   db_name: str = "CWDatabase.db") -> Optional[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Get top 5 artists and their statistics for the specified year range.
    
    Args:
        start_year (int): Start year
        end_year (int): End year
        weights (RankingWeights): Ranking weights
        db_name (str): Database file name
        
    Returns:
        Optional[Tuple[pd.DataFrame, pd.DataFrame]]: Tuple of (yearly_data, summary_data) or None if error
    """
    try:
        conn = sqlite3.connect(db_name)
        
        # Get artist statistics by year
        query = """
            SELECT 
                a.Name as Artist,
                s.Year,
                COUNT(*) as NumSongs,
                ROUND(AVG(s.Popularity), 2) as AvgPopularity
            FROM Song s
            JOIN Artist a ON s.ArtistID = a.ID
            WHERE s.Year BETWEEN ? AND ?
            GROUP BY a.Name, s.Year
            HAVING NumSongs > 0
            ORDER BY s.Year, NumSongs DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(start_year, end_year))
        
        if df.empty:
            logging.warning(f"No data found for years {start_year}-{end_year}")
            conn.close()
            return None
            
        # Calculate ranking values
        df['RankValue'] = df.apply(
            lambda row: calculate_ranking_value(
                row['NumSongs'], 
                row['AvgPopularity'],
                weights
            ),
            axis=1
        )
        
        # Get top 5 artists based on total ranking value
        top_artists = df.groupby('Artist').agg({
            'RankValue': 'sum',
            'NumSongs': 'sum',
            'AvgPopularity': 'mean'
        }).sort_values('RankValue', ascending=False).head(5)
        
        # Create yearly breakdown for top artists
        yearly_data = pd.pivot_table(
            df[df['Artist'].isin(top_artists.index)],
            values='RankValue',
            index='Artist',
            columns='Year',
            fill_value=None
        )
        
        # Add average row
        yearly_data.loc['Average'] = yearly_data.mean()
        
        conn.close()
        return yearly_data, top_artists
        
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return None

def display_rankings_table(yearly_data: pd.DataFrame, top_artists: pd.DataFrame):
    """
    Display formatted rankings table with highlighting.
    
    Args:
        yearly_data (pd.DataFrame): Yearly breakdown of artist rankings
        top_artists (pd.DataFrame): Summary statistics for top artists
    """
    print("\nTop Artists Table:")
    print("=" * 80)
    
    # Format table with highlighting
    display_df = yearly_data.copy()
    
    # Highlight maximum values in each year
    for col in display_df.columns:
        max_val = display_df[col].max()
        display_df[col] = display_df[col].apply(
            lambda x: f"\033[1m{x:.1f}\033[0m" if x == max_val else f"{x:.1f}" if pd.notnull(x) else "Null"
        )
    
    # Add overall statistics
    display_df['Total Songs'] = top_artists['NumSongs']
    display_df['Avg Popularity'] = top_artists['AvgPopularity'].round(1)
    
    print(display_df.to_string())
    print("\nNote: Bold values indicate highest rank value for each year")
    print("=" * 80)

def create_visualization(yearly_data: pd.DataFrame, start_year: int, end_year: int):
    """
    Create visualization of artist rankings over time and save to file.
    
    Args:
        yearly_data (pd.DataFrame): Yearly breakdown of artist rankings
        start_year (int): Start year
        end_year (int): End year
    """
    plt.figure(figsize=(12, 6))
    
    # Plot individual artist lines
    for artist in yearly_data.index[:-1]:  # Exclude Average row
        data = yearly_data.loc[artist]
        years = [year for year in range(start_year, end_year + 1) 
                if year in yearly_data.columns and pd.notnull(data[year])]
        values = [data[year] for year in years]
        plt.plot(years, values, marker='o', label=artist, linewidth=2)
    
    # Plot average line
    avg_data = yearly_data.loc['Average']
    years = [year for year in range(start_year, end_year + 1) 
            if year in yearly_data.columns and pd.notnull(avg_data[year])]
    values = [avg_data[year] for year in years]
    plt.plot(years, values, 'k--', label='Average', linewidth=2)
    
    plt.title(f"Artist Rankings Over Time ({start_year}-{end_year})")
    plt.xlabel("Year")
    plt.ylabel("Rank Value")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def analyze_top_artists(start_year: int, end_year: int) -> bool:
    """
    Analyze top artists for the specified year range.
    This function is called from the menu system.
    
    Args:
        start_year (int): Start year for analysis
        end_year (int): End year for analysis
        
    Returns:
        bool: True if analysis was successful, False otherwise
    """
    try:
        if not validate_year_range(start_year, end_year):
            return False
            
        # Initialize ranking weights
        weights = RankingWeights()
        
        # Get and display results
        result = get_top_artists(start_year, end_year, weights)
        
        if result is not None:
            yearly_data, top_artists = result
            display_rankings_table(yearly_data, top_artists)
            create_visualization(yearly_data, start_year, end_year)
            return True
        else:
            print("\nUnable to generate rankings. Please check the logs for details.")
            return False
            
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        print(f"\nError analyzing top artists: {str(e)}")
        return False

def main():
    """
    Main function to run the top artists analysis.
    """
    try:
        print("\nTop 5 Artists Analysis")
        print("=====================")
        
        # Get year range from user
        while True:
            try:
                start_year = int(input("\nEnter start year (1998-2020): "))
                end_year = int(input("Enter end year (1998-2020): "))
                
                if validate_year_range(start_year, end_year):
                    break
                    
                print("\nPlease enter a valid year range.")
                
            except ValueError:
                print("\nPlease enter valid numbers for years.")
        
        analyze_top_artists(start_year, end_year)
            
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        print("\nAn error occurred while processing the request. Please check the logs for details.")

if __name__ == "__main__":
    main()