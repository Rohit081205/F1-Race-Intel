"""
Commentary Engine Module

Generates professional F1-style live commentary based on race state, 
detected events, and the current hype index.
"""

from typing import List, Dict
from src.race_state import RaceState

class CommentaryEngine:
    """
    Generates deterministic, context-aware commentary using a tiered template system.
    """
    
    def __init__(self):
        """
        Initialize the commentary engine with structured templates.
        """
        # Event priority order (higher index = higher priority)
        self.priority_order = [
            "Tire Degradation Phase",
            "Undercut Window",
            "Battle Formation",
            "Overtake Potential Spike",
            "High Pressure Closing Phase"
        ]
        
        # Hype levels
        self.LEVEL_LOW = "analytical"    # 0-30
        self.LEVEL_MID = "tension"       # 31-65
        self.LEVEL_HIGH = "intensity"    # 66-100
        
        # Templates dictionary
        self.templates = {
            "High Pressure Closing Phase": {
                self.LEVEL_LOW: [
                    "We are in the final stages and {d2} is keeping the pressure on {d1}.",
                    "The gap between the leaders is narrowing as we approach the flag."
                ],
                self.LEVEL_MID: [
                    "This is getting tight! {d2} is breathing down the neck of {d1} as the laps count down!",
                    "Look at that gap! {d2} is doing everything to break the resistance of {d1}."
                ],
                self.LEVEL_HIGH: [
                    "Into the final moments and it is absolutely neck and neck for {d1} and {d2}!",
                    "Unbelievable pressure here! {d2} is looking for any way past {d1} in these closing stages!"
                ]
            },
            "Overtake Potential Spike": {
                self.LEVEL_LOW: [
                    "{d2} has a significant pace advantage over {d1} right now.",
                    "The telemetry shows {d2} is significantly faster through this sector than {d1}."
                ],
                self.LEVEL_MID: [
                    "{d2} is within striking distance of {d1}! The overtake looks imminent.",
                    "Watch {d2} here, the pace delta to {d1} is enough to make a move soon."
                ],
                self.LEVEL_HIGH: [
                    "{d2} is absolutely charging! {d1} is a sitting duck with this pace difference!",
                    "Here comes {d2}! Late on the brakes, looking for the inside line on {d1}!"
                ]
            },
            "Battle Formation": {
                self.LEVEL_LOW: [
                    "{d2} is now within DRS range of {d1}.",
                    "The gap between {d1} and {d2} is down to under a second."
                ],
                self.LEVEL_MID: [
                    "The battle is on between {d1} and {d2}! {d2} is hounding the back of that car.",
                    "We have a real fight on our hands now as {d2} closes right up to {d1}."
                ],
                self.LEVEL_HIGH: [
                    "They are wheel-to-wheel! {d2} is challenging {d1} for every inch of track!",
                    "Nose to tail through the corners! {d2} is relentless in this hunt for {d1}!"
                ]
            },
            "Undercut Window": {
                self.LEVEL_LOW: [
                    "Strategic options opening up for {d2} if they choose to pit now.",
                    "The tire advantage for {d2} compared to {d1} suggests a strategic play."
                ],
                self.LEVEL_MID: [
                    "The undercut is looking very powerful for {d2} right now.",
                    "Ferrari might be looking at the numbers for {d2} to jump {d1} in the pits."
                ],
                self.LEVEL_HIGH: [
                    "This is the moment! {d2} has the grip to fly past {d1} if they pull the trigger now!",
                    "CRITICAL STRATEGY: {d2} can capitalize on {d1}'s older tires this very lap!"
                ]
            },
            "Tire Degradation Phase": {
                self.LEVEL_LOW: [
                    "{d1} is starting to struggle with the life of these {compound} tires.",
                    "Tire wear becoming an analytical factor for {d1} at this stage."
                ],
                self.LEVEL_MID: [
                    "{d1} is losing time now as the {compound} tires began to drop off.",
                    "The cliff is approaching for {d1}. Those tires are looking very worn."
                ],
                self.LEVEL_HIGH: [
                    "{d1} is sliding everywhere! Those tires are absolutely finished!",
                    "Significant loss of grip for {d1}! They are defenseless on this rubber!"
                ]
            }
        }
        
        # Fallback templates (Phase-aware)
        self.fallback_templates = {
            "Opening": [
                "The pack is settling in after the start. Lap {lap}.",
                "Early stages here. Drivers managing gaps and battery deployment."
            ],
            "Strategy": [
                "Strategy taking center stage in this middle phase. Lap {lap}.",
                "Teams are watching the pit window closely as we reach the midpoint."
            ],
            "Closing": [
                "The race is entering its final chapter. Lap {lap}.",
                "Final push for the runners as they balance fuel and tire life."
            ],
            "Safety": [
                "Track conditions are currently impacted. Safety status active.",
                "Caution across the field as the track status changes. Lap {lap}."
            ]
        }

    def _get_hype_level(self, hype_index: float) -> str:
        """Helper to determine hype level name."""
        if hype_index <= 30:
            return self.LEVEL_LOW
        elif hype_index <= 65:
            return self.LEVEL_MID
        else:
            return self.LEVEL_HIGH

    def generate_commentary(self, race_state: RaceState, events: List[Dict], hype_index: float) -> str:
        """
        Main method to generate a single line of F1 commentary.
        """
        lap_num = race_state.current_lap
        hype_level = self._get_hype_level(hype_index)
        
        # 1. Event Selection (Priority Based)
        selected_event = None
        if events:
            # Sort events by priority defined in __init__
            sorted_events = sorted(
                events, 
                key=lambda x: self.priority_order.index(x['event_type']) if x['event_type'] in self.priority_order else -1,
                reverse=True
            )
            selected_event = sorted_events[0]
            
        # 2. Generate Commentary String
        if selected_event and selected_event['event_type'] in self.templates:
            event_type = selected_event['event_type']
            drivers = selected_event['drivers_involved']
            
            options = self.templates[event_type][hype_level]
            template = options[lap_num % len(options)]
            
            # Format with driver names
            d1 = drivers[0] if len(drivers) > 0 else "Unknown"
            d2 = drivers[1] if len(drivers) > 1 else "Unknown"
            
            # Additional context formatting
            details = selected_event.get('details', {})
            compound = details.get('tire_compound', 'rubber')
            
            return template.format(d1=d1, d2=d2, compound=compound)
            
        # 3. Fallback logic if no event or template not found
        phase_options = self.fallback_templates.get(race_state.current_phase, self.fallback_templates["Strategy"])
        base_commentary = phase_options[lap_num % len(phase_options)].format(lap=lap_num)
        
        # Append situational data to fallback
        drivers = race_state.lap_history[-1]['drivers'] if race_state.lap_history else []
        if len(drivers) >= 2:
            p1 = drivers[0]
            p2 = drivers[1]
            gap = p2.gap_ahead
            
            if hype_level == self.LEVEL_LOW:
                return f"{base_commentary} {p1.driver} leads {p2.driver} by {gap} seconds."
            else:
                return f"{base_commentary} The gap at the front is {gap} seconds between {p1.driver} and {p2.driver}."
        
        return base_commentary
