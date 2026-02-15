from src.replay_engine import RaceReplay
from src.race_state import RaceState
from src.event_detection import EventDetection
from src.hype_index import HypeIndex

replay = RaceReplay("data/sample_race.csv")
race_state = RaceState(replay.get_total_laps())
event_detector = EventDetection()
hype_calculator = HypeIndex()

print("=" * 80)
print("Testing Hype Index Module")
print("=" * 80)

while True:
    lap_data = replay.next_lap()
    if lap_data is None:
        break
    
    race_state.update_state(lap_data)
    events = event_detector.detect_events(race_state)
    hype_score = hype_calculator.calculate(race_state, events)
    
    print(f"\nLap {lap_data['lap_number']} Analysis:")
    print(f"  Phase: {race_state.current_phase}")
    print(f"  Events Detected: {len(events)}")
    print(f"  HYPE INDEX: {hype_score}/100")
    
    if events:
        for e in events:
            print(f"    - [{e['event_type']}] Score: {e['score']}")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
