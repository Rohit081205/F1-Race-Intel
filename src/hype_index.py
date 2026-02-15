"""
Hype Index Module

Calculates a real-time excitement score (0-100) based on statistical metrics 
and event detection amplification.
"""

from typing import List, Dict
import numpy as np
from src.race_state import RaceState


class HypeIndex:
    """
    Calculates the excitement level of the race using a weighted multi-factor formula.
    """
    
    def calculate(self, race_state: RaceState, events: List[Dict]) -> float:
        """
        Calculate the Hype Index (0-100) for the current lap.
        
        Args:
            race_state: Current state of the race
            events: List of events detected in the current lap
            
        Returns:
            A float between 0 and 100 representing the hype level.
        """
        if len(race_state.lap_history) == 0:
            return 0.0
            
        current_snapshot = race_state.lap_history[-1]
        drivers = current_snapshot['drivers']
        total_drivers = len(drivers)
        
        # --- 1. Statistical Base Score (Weight: 70%) ---
        
        # A. Gap Volatility (Weight: 0.25)
        # Standard deviation of gaps among top 5 drivers
        top_gaps = [d.gap_ahead for d in drivers[:min(5, total_drivers)]]
        std_dev = float(np.std(top_gaps)) if len(top_gaps) > 1 else 0.0
        volatility_score = min(1.0, std_dev / 5.0)
        
        # B. Proximity Density (Weight: 0.20)
        # Proportion of driver pairs with gap < 1.0s
        close_pairs = 0
        total_pairs = total_drivers - 1
        if total_pairs > 0:
            for i in range(1, total_drivers):
                if drivers[i].gap_ahead < 1.0:
                    close_pairs += 1
            proximity_score = close_pairs / total_pairs
        else:
            proximity_score = 0.0
            
        # C. Position Change Intensity (Weight: 0.15)
        # Number of position change strings this lap
        position_change_count = len(current_snapshot['deltas']['position_changes'])
        position_score = min(1.0, position_change_count / 5.0)
        
        # D. Pit Activity (Weight: 0.10)
        # Pits in current lap divided by total drivers
        pit_activity = race_state.get_recent_pit_activity()
        pit_activity_score = min(1.0, pit_activity['current_lap_pits'] / total_drivers) if total_drivers > 0 else 0.0
        
        # Combine base metrics (Sum of weights = 0.25+0.20+0.15+0.10 = 0.70)
        # We normalize the internal weights relative to the 70% share
        base_component = (
            volatility_score * 0.25 +
            proximity_score * 0.20 +
            position_score * 0.15 +
            pit_activity_score * 0.10
        )
        
        # --- 2. Event Amplification (Weight: 30%) ---
        
        event_total_score = sum(event.get("score", 0.0) for event in events)
        normalized_event_score = min(1.0, event_total_score / 3.0)
        
        # --- 3. Final Hype Index Calculation ---
        
        # base_component is already weighted relative to 0.70, but it ranges 0 to 0.7
        # normalized_event_score ranges 0 to 1.0
        
        # To strictly follow "base_score * 70 + normalized_event_score * 30":
        # We treat base_component as a value from 0 to 1 regarding its internal weights
        # Actually, base_component = (v*0.25 + p*0.20 + pos*0.15 + pit*0.10) / 0.70 would be 0-1
        
        raw_base_score = (
            volatility_score * 0.25 +
            proximity_score * 0.20 +
            position_score * 0.15 +
            pit_activity_score * 0.10
        ) / 0.70 if 0.70 > 0 else 0.0
        
        hype_index = (raw_base_score * 70) + (normalized_event_score * 30)
        
        # Clamp and round
        final_hype = max(0.0, min(100.0, hype_index))
        return round(final_hype, 2)
