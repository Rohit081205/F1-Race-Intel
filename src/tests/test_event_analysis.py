from src.replay_engine import RaceReplay
from src.race_state import RaceState
from src.event_detection import EventDetection

replay = RaceReplay("data/sample_race.csv")
race_state = RaceState(replay.get_total_laps())
event_detector = EventDetection()

while True:
    lap_data = replay.next_lap()
    if lap_data is None:
        break
    
    race_state.update_state(lap_data)
    events = event_detector.detect_events(race_state)
    
    print(f"\nLap {lap_data['lap_number']} Events:")
    for event in events:
        print(event)
