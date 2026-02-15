from src.replay_engine import RaceReplay
from src.race_state import RaceState
from src.event_detection import EventDetection

# Initialize components
replay = RaceReplay("data/sample_race.csv")
race_state = RaceState(total_laps=replay.get_total_laps())
event_detector = EventDetection()

print("=" * 80)
print("Testing Event Detection Module")
print("=" * 80)

for i in range(1, 6):
    print(f"\n{'='*80}")
    print(f"LAP {i}")
    print('='*80)
    
    lap_data = replay.next_lap()
    if lap_data is None:
        break
    
    race_state.update_state(lap_data)
    
    print(f"Race Phase: {race_state.current_phase}")
    print(f"Position Changes: {race_state.get_position_changes()}")
    
    # Detect events
    events = event_detector.detect_events(race_state)
    
    if events:
        print(f"\n🔔 {len(events)} Event(s) Detected:")
        for event in events:
            print(f"\n  Type: {event['event_type']}")
            print(f"  Drivers: {', '.join(event['drivers_involved'])}")
            print(f"  Score: {event['score']}")
            print(f"  Details: {event['details']}")
    else:
        print("\n✓ No events detected this lap")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
