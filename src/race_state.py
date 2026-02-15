"""
Race State Module

Maintains race state memory, tracks lap history, and detects dynamic race phases.
"""

from typing import List, Dict, Optional
from collections import deque
from src.replay_engine import LapData


class RaceState:
    """
    Maintains comprehensive race state with rolling history and dynamic phase detection.
    """
    
    def __init__(self, total_laps: int):
        """
        Initialize race state tracker.
        
        Args:
            total_laps: Total number of laps in the race
        """
        self.total_laps = total_laps
        self.current_lap = 0
        self.lap_history = deque(maxlen=5)
        self.current_phase = "Opening"
    
    def update_state(self, lap_snapshot: Dict):
        """
        Update race state with new lap data.
        
        Args:
            lap_snapshot: Output from RaceReplay.next_lap() containing lap_number, drivers, and deltas
        """
        if lap_snapshot is None:
            return
        
        self.current_lap = lap_snapshot['lap_number']
        self.lap_history.append(lap_snapshot)
        self.current_phase = self.detect_race_phase()
    
    def detect_race_phase(self) -> str:
        """
        Detect current race phase dynamically based on lap progress and race conditions.
        
        Phase Priority: Safety > Closing > Strategy > Opening
        
        Returns:
            Phase string: "Safety", "Closing", "Strategy", or "Opening"
        """
        if self.current_lap == 0 or len(self.lap_history) == 0:
            return "Opening"
        
        current_snapshot = self.lap_history[-1]
        drivers = current_snapshot['drivers']
        
        # Safety Phase: track_status != "Green" (highest priority)
        for driver in drivers:
            if driver.track_status != "Green":
                return "Safety"
        
        # Closing Phase: final 20% of race
        closing_threshold = max(1, int(self.total_laps * 0.8))
        if self.current_lap >= closing_threshold:
            return "Closing"
        
        # Strategy Phase: >2 pit stops in last 3 laps
        recent_pit_count = self._count_pits_in_last_n_laps(3)
        if recent_pit_count > 2:
            return "Strategy"
        
        # Opening Phase: first 15% of race (lowest priority)
        opening_threshold = max(1, int(self.total_laps * 0.15))
        if self.current_lap <= opening_threshold:
            return "Opening"
        
        # Default to Strategy if not in other phases
        return "Strategy"
    
    def _count_pits_in_last_n_laps(self, n: int) -> int:
        """
        Count total pit stops in the last n laps.
        
        Args:
            n: Number of recent laps to check
            
        Returns:
            Total number of pit stops
        """
        pit_count = 0
        laps_to_check = min(n, len(self.lap_history))
        
        for i in range(laps_to_check):
            lap_snapshot = self.lap_history[-(i + 1)]
            drivers = lap_snapshot['drivers']
            
            for driver in drivers:
                if driver.pit_stop:
                    pit_count += 1
        
        return pit_count
    
    def get_gap_trend(self, driver_name: str) -> Optional[float]:
        """
        Calculate gap trend for a driver (current gap - gap 2 laps ago).
        
        Args:
            driver_name: Name of the driver
            
        Returns:
            Gap difference (negative = closing, positive = increasing), or None if insufficient data
        """
        if len(self.lap_history) < 3:
            return None
        
        # Get current lap data
        current_lap = self.lap_history[-1]
        current_driver = self._find_driver(current_lap['drivers'], driver_name)
        
        if current_driver is None:
            return None
        
        # Get lap data from 2 laps ago
        lap_2_ago = self.lap_history[-3]
        driver_2_ago = self._find_driver(lap_2_ago['drivers'], driver_name)
        
        if driver_2_ago is None:
            return None
        
        # Calculate trend (negative = gap closing, positive = gap increasing)
        gap_trend = current_driver.gap_ahead - driver_2_ago.gap_ahead
        return round(gap_trend, 3)
    
    def _find_driver(self, drivers: List[LapData], driver_name: str) -> Optional[LapData]:
        """
        Find driver in a list of LapData objects.
        
        Args:
            drivers: List of LapData objects
            driver_name: Name of driver to find
            
        Returns:
            LapData object or None if not found
        """
        for driver in drivers:
            if driver.driver == driver_name:
                return driver
        return None
    
    def get_position_changes(self) -> List[str]:
        """
        Get position changes from the most recent lap.
        
        Returns:
            List of position change strings
        """
        if len(self.lap_history) == 0:
            return []
        
        current_lap = self.lap_history[-1]
        return current_lap['deltas']['position_changes']
    
    def get_recent_pit_activity(self) -> Dict[str, int]:
        """
        Get pit stop activity metrics.
        
        Returns:
            Dictionary with current_lap_pits and last_3_laps_pits
        """
        current_lap_pits = 0
        
        if len(self.lap_history) > 0:
            current_lap = self.lap_history[-1]
            for driver in current_lap['drivers']:
                if driver.pit_stop:
                    current_lap_pits += 1
        
        last_3_laps_pits = self._count_pits_in_last_n_laps(3)
        
        return {
            'current_lap_pits': current_lap_pits,
            'last_3_laps_pits': last_3_laps_pits
        }
