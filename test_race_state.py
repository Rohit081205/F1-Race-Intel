from src.replay_engine import RaceReplay
from src.race_state import RaceState

# Initialize replay and race state
replay = RaceReplay("data/sample_race.csv")
race_state = RaceState(total_laps=replay.get_total_laps())

print("=" * 80)
print("Testing RaceState Module")
print("=" * 80)

for i in range(1, 7):
    print(f"\n--- Lap {i} ---")
    lap_data = replay.next_lap()
    
    if lap_data is None:
        print("Race finished")
        break
    
    # Update race state
    race_state.update_state(lap_data)
    
    print(f"Current Lap: {race_state.current_lap}")
    print(f"Race Phase: {race_state.current_phase}")
    print(f"Position Changes: {race_state.get_position_changes()}")
    
    # Test gap trend for HAM
    ham_trend = race_state.get_gap_trend("HAM")
    print(f"HAM Gap Trend: {ham_trend}")
    
    # Test pit activity
    pit_activity = race_state.get_recent_pit_activity()
    print(f"Pit Activity: {pit_activity}")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
