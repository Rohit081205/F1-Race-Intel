"""
Event Detection Module

Detects racing events using rule-based logic and scoring thresholds.
"""

from typing import List, Dict
from src.replay_engine import LapData
from src.race_state import RaceState


class EventDetection:
    """
    Detects key racing events based on telemetry data and race state.
    """
    
    def __init__(self):
        """
        Initialize event detection with threshold constants.
        """
        # Proximity and gap thresholds
        self.PROXIMITY_THRESHOLD = 1.2
        self.CLOSING_TREND_THRESHOLD = -0.3
        self.PACE_ADVANTAGE_THRESHOLD = -0.2
        
        # Tire age thresholds by compound
        self.TIRE_AGE_SOFT = 15
        self.TIRE_AGE_MEDIUM = 25
        self.TIRE_AGE_HARD = 35
        
        # Strategy thresholds
        self.UNDERCUT_TIRE_ADVANTAGE = 5
        self.HIGH_PRESSURE_GAP = 2.0
    
    def detect_events(self, race_state: RaceState) -> List[Dict]:
        """
        Detect all racing events for the current lap.
        
        Args:
            race_state: Current race state with lap history
            
        Returns:
            List of event dictionaries
        """
        events = []
        
        if len(race_state.lap_history) == 0:
            return events
        
        current_lap_data = race_state.lap_history[-1]
        drivers = current_lap_data['drivers']
        lap_number = current_lap_data['lap_number']
        deltas = current_lap_data['deltas']
        
        # Detect events for each driver pair
        for i in range(len(drivers) - 1):
            driver_ahead = drivers[i]
            driver_behind = drivers[i + 1]
            
            # Get gap trend for driver behind
            gap_trend = race_state.get_gap_trend(driver_behind.driver)
            
            # Get lap time delta for driver behind
            lap_time_delta = deltas['lap_time_deltas'].get(driver_behind.driver, 0)
            
            # 1. Battle Formation Detection
            battle_event = self._detect_battle_formation(
                lap_number, driver_ahead, driver_behind, gap_trend
            )
            if battle_event:
                events.append(battle_event)
            
            # 2. Overtake Potential Spike Detection
            overtake_event = self._detect_overtake_potential(
                lap_number, driver_ahead, driver_behind, gap_trend, lap_time_delta
            )
            if overtake_event:
                events.append(overtake_event)
            
            # 4. Undercut Window Detection
            undercut_event = self._detect_undercut_window(
                lap_number, driver_ahead, driver_behind
            )
            if undercut_event:
                events.append(undercut_event)
            
            # 5. High Pressure Closing Phase Detection
            if race_state.current_phase == "Closing":
                pressure_event = self._detect_high_pressure_closing(
                    lap_number, driver_ahead, driver_behind, gap_trend
                )
                if pressure_event:
                    events.append(pressure_event)
        
        # 3. Tire Degradation Detection (individual driver analysis)
        for driver in drivers:
            lap_time_delta = deltas['lap_time_deltas'].get(driver.driver, 0)
            degradation_event = self._detect_tire_degradation(
                lap_number, driver, lap_time_delta
            )
            if degradation_event:
                events.append(degradation_event)
        
        return events
    
    def _detect_battle_formation(self, lap_number: int, driver_ahead: LapData, 
                                 driver_behind: LapData, gap_trend: float) -> Dict:
        """
        Detect battle formation between two drivers.
        
        Triggers when gap < PROXIMITY_THRESHOLD and gap is closing.
        """
        gap = driver_behind.gap_ahead
        
        if gap >= self.PROXIMITY_THRESHOLD:
            return None
        
        if gap_trend is None or gap_trend >= self.CLOSING_TREND_THRESHOLD:
            return None
        
        # Calculate score based on closing rate
        score = min(1.0, abs(gap_trend) / 1.0)
        
        return {
            "lap": lap_number,
            "event_type": "Battle Formation",
            "drivers_involved": [driver_ahead.driver, driver_behind.driver],
            "score": round(score, 3),
            "details": {
                "gap": round(gap, 3),
                "gap_trend": round(gap_trend, 3)
            }
        }
    
    def _detect_overtake_potential(self, lap_number: int, driver_ahead: LapData,
                                   driver_behind: LapData, gap_trend: float, 
                                   lap_time_delta: float) -> Dict:
        """
        Detect overtake potential spike.
        
        Triggers when gap is small and driver behind has pace advantage.
        """
        gap = driver_behind.gap_ahead
        
        if gap >= self.PROXIMITY_THRESHOLD:
            return None
        
        # Require gap to be actually closing
        if gap_trend is None or gap_trend >= 0:
            return None
        
        if lap_time_delta >= self.PACE_ADVANTAGE_THRESHOLD:
            return None
        
        # Weighted score combining proximity, closing trend, and pace
        proximity_score = 1.0 - (gap / self.PROXIMITY_THRESHOLD)
        closing_score = min(1.0, abs(gap_trend) / 1.0) if gap_trend < 0 else 0
        pace_score = min(1.0, abs(lap_time_delta) / 1.0) if lap_time_delta < 0 else 0
        
        score = (proximity_score * 0.4 + closing_score * 0.3 + pace_score * 0.3)
        
        return {
            "lap": lap_number,
            "event_type": "Overtake Potential Spike",
            "drivers_involved": [driver_ahead.driver, driver_behind.driver],
            "score": round(score, 3),
            "details": {
                "gap": round(gap, 3),
                "gap_trend": round(gap_trend, 3),
                "lap_time_delta": round(lap_time_delta, 3)
            }
        }
    
    def _detect_tire_degradation(self, lap_number: int, driver: LapData,
                                 lap_time_delta: float) -> Dict:
        """
        Detect tire degradation phase.
        
        Triggers when tire age exceeds compound threshold and lap times increasing.
        """
        tire_age = driver.tire_age
        compound = driver.tire_compound
        
        # Determine threshold based on compound
        if compound == "Soft":
            threshold = self.TIRE_AGE_SOFT
        elif compound == "Medium":
            threshold = self.TIRE_AGE_MEDIUM
        elif compound == "Hard":
            threshold = self.TIRE_AGE_HARD
        else:
            threshold = self.TIRE_AGE_MEDIUM
        
        if tire_age <= threshold:
            return None
        
        # Check if lap times are increasing (positive delta = slower)
        if lap_time_delta <= 0:
            return None
        
        # Score proportional to tire age excess
        age_excess = tire_age - threshold
        score = min(1.0, age_excess / 10.0)
        
        return {
            "lap": lap_number,
            "event_type": "Tire Degradation Phase",
            "drivers_involved": [driver.driver],
            "score": round(score, 3),
            "details": {
                "tire_compound": compound,
                "tire_age": tire_age,
                "threshold": threshold,
                "lap_time_delta": round(lap_time_delta, 3)
            }
        }
    
    def _detect_undercut_window(self, lap_number: int, driver_ahead: LapData,
                                driver_behind: LapData) -> Dict:
        """
        Detect undercut window opportunity.
        
        Triggers when driver behind has fresher tires and is close enough.
        """
        gap = driver_behind.gap_ahead
        
        if gap >= 3.0:
            return None
        
        tire_age_diff = driver_ahead.tire_age - driver_behind.tire_age
        
        if tire_age_diff < self.UNDERCUT_TIRE_ADVANTAGE:
            return None
        
        # Score proportional to tire advantage
        score = min(1.0, tire_age_diff / 15.0)
        
        return {
            "lap": lap_number,
            "event_type": "Undercut Window",
            "drivers_involved": [driver_ahead.driver, driver_behind.driver],
            "score": round(score, 3),
            "details": {
                "gap": round(gap, 3),
                "tire_age_advantage": tire_age_diff,
                "ahead_tire_age": driver_ahead.tire_age,
                "behind_tire_age": driver_behind.tire_age
            }
        }
    
    def _detect_high_pressure_closing(self, lap_number: int, driver_ahead: LapData,
                                      driver_behind: LapData, gap_trend: float) -> Dict:
        """
        Detect high pressure closing phase battle.
        
        Triggers in closing phase when gap is small and decreasing.
        """
        gap = driver_behind.gap_ahead
        
        if gap >= self.HIGH_PRESSURE_GAP:
            return None
        
        if gap_trend is None or gap_trend >= 0:
            return None
        
        # Score based on proximity intensity
        proximity_score = 1.0 - (gap / self.HIGH_PRESSURE_GAP)
        closing_score = min(1.0, abs(gap_trend) / 1.0)
        
        score = (proximity_score * 0.6 + closing_score * 0.4)
        
        return {
            "lap": lap_number,
            "event_type": "High Pressure Closing Phase",
            "drivers_involved": [driver_ahead.driver, driver_behind.driver],
            "score": round(score, 3),
            "details": {
                "gap": round(gap, 3),
                "gap_trend": round(gap_trend, 3)
            }
        }
