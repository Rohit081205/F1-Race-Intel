import fastf1
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Create directories
Path("data").mkdir(exist_ok=True)
Path("cache").mkdir(exist_ok=True)
fastf1.Cache.enable_cache("cache")

def get_track_status(status_code):
    if str(status_code) == '1':
        return "Green"
    elif str(status_code) == '4':
        return "Safety"
    else:
        return "Yellow"

def extract_race(year, location, output_filename):
    print(f"Loading {year} {location} Race session...")
    try:
        session = fastf1.get_session(year, location, 'R')
        session.load()
    except Exception as e:
        print(f"Error loading session: {e}")
        return

    laps = session.laps.copy()
    laps = laps.dropna(subset=['LapTime'])
    laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()
    
    laps = laps.sort_values(by=['Driver', 'LapNumber'])
    laps['CumulativeTime'] = laps.groupby('Driver')['LapTimeSeconds'].cumsum()
    
    max_lap = int(laps['LapNumber'].max())
    processed_laps = []
    
    print(f"Processing {max_lap} laps for {location}...")
    for lap_num in range(1, max_lap + 1):
        lap_snapshot = laps[laps['LapNumber'] == lap_num].copy()
        if lap_snapshot.empty:
            continue
            
        leader_time = lap_snapshot['CumulativeTime'].min()
        
        for _, row in lap_snapshot.iterrows():
            status = get_track_status(row['TrackStatus'])
            pit_stop = pd.notna(row['PitInTime']) or pd.notna(row['PitOutTime'])
            tire_age = int(row['TyreLife']) if not pd.isna(row['TyreLife']) else 0
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
            
    df = pd.DataFrame(processed_laps)
    df = df.sort_values(by=['lap_number', 'position'])
    
    output_path = Path("data") / output_filename
    df.to_csv(output_path, index=False)
    print(f"Successfully generated {output_path}")

if __name__ == "__main__":
    if len(sys.argv) == 4:
        extract_race(int(sys.argv[1]), sys.argv[2], sys.argv[3])
    else:
        # Default fallback for Silverstone
        extract_race(2023, "Silverstone", "real_race_silverstone_2023.csv")
