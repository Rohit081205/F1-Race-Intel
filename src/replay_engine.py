"""
Race Replay Engine Module

Loads lap-by-lap telemetry data from CSV and simulates race progression.
Maintains race memory and computes delta metrics between consecutive laps.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd


@dataclass
class LapData:
    """Represents telemetry data for a single driver on a single lap."""
    lap_number: int
    driver: str
    position: int
    lap_time: float
    gap_ahead: float
    tire_compound: str
    tire_age: int
    pit_stop: bool
    track_status: str


class RaceReplay:
    """
    Simulates lap-by-lap race progression from historical telemetry data.
    
    Maintains race state memory and computes delta metrics between laps.
    """
    
    def __init__(self, csv_path: str):
        """
        Initialize race replay from CSV file.
        
        Args:
            csv_path: Path to CSV file containing lap-by-lap telemetry data
        """
        # Load CSV data
        self.df = pd.read_csv(csv_path)
        
        # Convert pit_stop to boolean if needed
        if self.df['pit_stop'].dtype == 'object':
            self.df['pit_stop'] = self.df['pit_stop'].map({'True': True, 'False': False, True: True, False: False})
        
        # Group data by lap number for efficient access
        self.laps_data = {}
        for lap_num, lap_df in self.df.groupby("lap_number"):
            lap_df = lap_df.sort_values('position')
            self.laps_data[lap_num] = self._convert_to_lap_data(lap_df)
        
        # Store total laps
        self.total_laps = int(self.df['lap_number'].max())
        
        # Initialize state
        self.current_lap = 0
        self.previous_lap_data = None
    
    def _convert_to_lap_data(self, lap_df: pd.DataFrame) -> List[LapData]:
        """
        Convert DataFrame rows to LapData objects.
        
        Args:
            lap_df: DataFrame containing data for a single lap
            
        Returns:
            List of LapData objects
        """
        lap_data_list = []
        for _, row in lap_df.iterrows():
            lap_data = LapData(
                lap_number=int(row['lap_number']),
                driver=str(row['driver']),
                position=int(row['position']),
                lap_time=float(row['lap_time']),
                gap_ahead=float(row['gap_ahead']),
                tire_compound=str(row['tire_compound']),
                tire_age=int(row['tire_age']),
                pit_stop=bool(row['pit_stop']),
                track_status=str(row['track_status'])
            )
            lap_data_list.append(lap_data)
        return lap_data_list
    
    def start_race(self) -> Dict:
        """
        Start the race from lap 1.
        
        Returns:
            Dictionary containing lap 1 data and empty deltas
        """
        self.current_lap = 1
        self.previous_lap_data = None
        
        drivers = self.laps_data.get(1, [])
        
        return {
            "lap_number": 1,
            "drivers": drivers,
            "deltas": {
                "position_changes": [],
                "gap_deltas": {},
                "lap_time_deltas": {}
            }
        }
    
    def next_lap(self) -> Optional[Dict]:
        """
        Progress to the next lap and compute deltas from previous lap.
        
        Returns:
            Dictionary containing lap data and deltas, or None if race is finished
        """
        # Auto-start race if not started yet
        if self.current_lap == 0:
            return self.start_race()
        
        # Check if race is finished
        if self.current_lap >= self.total_laps:
            return None
        
        # Store current lap as previous
        if self.current_lap > 0:
            self.previous_lap_data = self.laps_data.get(self.current_lap, [])
        
        # Increment to next lap
        self.current_lap += 1
        
        # Get current lap data
        current_drivers = self.laps_data.get(self.current_lap, [])
        
        # Compute deltas if we have previous lap data
        deltas = self._compute_deltas(current_drivers, self.previous_lap_data)
        
        return {
            "lap_number": self.current_lap,
            "drivers": current_drivers,
            "deltas": deltas
        }
    
    def _compute_deltas(self, current_drivers: List[LapData], 
                       previous_drivers: Optional[List[LapData]]) -> Dict:
        """
        Compute delta metrics between current and previous lap.
        
        Handles real-world variability like DNFs, None positions, and variable grid sizes.
        """
        if previous_drivers is None:
            return {
                "position_changes": [],
                "gap_deltas": {},
                "lap_time_deltas": {}
            }
        
        # Create lookup dictionaries for previous lap
        prev_positions = {driver.driver: driver.position for driver in previous_drivers}
        prev_gaps = {driver.driver: driver.gap_ahead for driver in previous_drivers}
        prev_lap_times = {driver.driver: driver.lap_time for driver in previous_drivers}
        
        # Track position changes
        position_changes = []
        gap_deltas = {}
        lap_time_deltas = {}
        
        # Sort current drivers by position (handling None) to ensure deterministic processing
        sorted_current = sorted(current_drivers, key=lambda x: x.position if x.position is not None else 999)
        
        for driver in sorted_current:
            driver_name = driver.driver
            
            # Position changes - only if both are present
            if driver_name in prev_positions:
                prev_pos = prev_positions[driver_name]
                curr_pos = driver.position
                
                if prev_pos is not None and curr_pos is not None:
                    if prev_pos > curr_pos:
                        positions_gained = prev_pos - curr_pos
                        position_changes.append(f"{driver_name} gained {positions_gained} position(s)")
                    elif prev_pos < curr_pos:
                        positions_lost = curr_pos - prev_pos
                        position_changes.append(f"{driver_name} lost {positions_lost} position(s)")
            
            # Gap deltas (negative = gap closing, positive = gap increasing)
            if driver_name in prev_gaps and driver.gap_ahead is not None and prev_gaps[driver_name] is not None:
                gap_delta = driver.gap_ahead - prev_gaps[driver_name]
                gap_deltas[driver_name] = round(gap_delta, 3)
            
            # Lap time deltas (negative = faster, positive = slower)
            if driver_name in prev_lap_times and driver.lap_time is not None and prev_lap_times[driver_name] is not None:
                lap_time_delta = driver.lap_time - prev_lap_times[driver_name]
                lap_time_deltas[driver_name] = round(lap_time_delta, 3)
        
        return {
            "position_changes": position_changes,
            "gap_deltas": gap_deltas,
            "lap_time_deltas": lap_time_deltas
        }
    
    def get_current_lap_data(self) -> Optional[List[LapData]]:
        """
        Get data for the current lap.
        
        Returns:
            List of LapData for current lap, or None if race hasn't started
        """
        if self.current_lap == 0:
            return None
        return self.laps_data.get(self.current_lap, [])
    
    def get_total_laps(self) -> int:
        """
        Get total number of laps in the race.
        
        Returns:
            Total number of laps
        """
        return self.total_laps
