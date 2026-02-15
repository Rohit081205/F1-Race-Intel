import fastf1
import pandas as pd
import numpy as np
from pathlib import Path
import os

# Create data directory if it doesn't exist
Path("data").mkdir(exist_ok=True)
# Enable cache
Path("cache").mkdir(exist_ok=True)
fastf1.Cache.enable_cache("cache")

def get_track_status(status_code):
    """
    Map FastF1 TrackStatus codes to engine strings.
    1 -> Green, 4 -> Safety, else -> Yellow
    """
    if str(status_code) == '1':
        return "Green"
    elif str(status_code) == '4':
        return "Safety"
    else:
        return "Yellow"

def load_real_race_data():
    print("Loading 2023 Silverstone Race session...")
    session = fastf1.get_session(2023, "Silverstone", "R")
    session.load()
    
    laps = session.laps.copy()
    
    # Clean data
    laps = laps.dropna(subset=['LapTime'])
    
    # Compute cumulative race time per driver
    print("Computing cumulative race times...")
    laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()
    
    # Sort by Driver and LapNumber to ensure cumulative sum is correct
    laps = laps.sort_values(by=['Driver', 'LapNumber'])
    laps['CumulativeTime'] = laps.groupby('Driver')['LapTimeSeconds'].cumsum()
    
    # Find leader cumulative time per lap
    # First, get the maximum lap number reached by the leader (or anyone)
    max_lap = int(laps['LapNumber'].max())
    
    processed_laps = []
    
    print(f"Processing {max_lap} laps...")
    for lap_num in range(1, max_lap + 1):
        lap_snapshot = laps[laps['LapNumber'] == lap_num].copy()
        if lap_snapshot.empty:
            continue
            
        # Determine the leader of this specific lap
        # The leader is the one with the smallest CumulativeTime who is on this lap
        # Note: In real F1, some might be lapped. We only care about those on lap_num.
        leader_time = lap_snapshot['CumulativeTime'].min()
        
        for _, row in lap_snapshot.iterrows():
            # Mapping status
            status = get_track_status(row['TrackStatus'])
            
            # Pit stop detection
            # pit_stop = not pd.isna(row['PitOutTime'])
            pit_stop = pd.notna(row['PitInTime']) or pd.notna(row['PitOutTime'])
            
            # Tyre life
            tire_age = int(row['TyreLife']) if not pd.isna(row['TyreLife']) else 0
            
            # Gap ahead calculation
            gap_ahead = round(row['CumulativeTime'] - leader_time, 3)
            
            processed_laps.append({
                'lap_number': int(row['LapNumber']),
                'driver': row['Driver'],
                'position': int(row['Position']) if not pd.isna(row['Position']) else None,
                'lap_time': round(row['LapTimeSeconds'], 3),
                'gap_ahead': gap_ahead,
                'tire_compound': row['Compound'] if not pd.isna(row['Compound']) else "Unknown",
                'tire_age': tire_age,
                'pit_stop': pit_stop,
                'track_status': status
            })
            
    # Create DataFrame and export
    df = pd.DataFrame(processed_laps)
    
    # Sort by lap and position for consistency
    df = df.sort_values(by=['lap_number', 'position'])
    
    output_path = "data/real_race_silverstone_2023.csv"
    df.to_csv(output_path, index=False)
    print(f"Successfully generated {output_path}")
    return output_path

if __name__ == "__main__":
    load_real_race_data()
