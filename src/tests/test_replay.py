from src.replay_engine import RaceReplay
import json

replay = RaceReplay("data/sample_race.csv")

print("=" * 80)
print("Testing RaceReplay Engine")
print("=" * 80)

for i in range(1, 7):
    print(f"\n--- Call {i}: next_lap() ---")
    result = replay.next_lap()
    
    if result is None:
        print("Result: None (Race finished)")
    else:
        print(f"Lap Number: {result['lap_number']}")
        print(f"Number of drivers: {len(result['drivers'])}")
        print("\nDrivers:")
        for driver in result['drivers']:
            print(f"  P{driver.position}: {driver.driver} - Lap: {driver.lap_time}s, Gap: {driver.gap_ahead}s, "
                  f"Tire: {driver.tire_compound} (age {driver.tire_age}), Pit: {driver.pit_stop}")
        
        print("\nDeltas:")
        if result['deltas']['position_changes']:
            print(f"  Position changes: {result['deltas']['position_changes']}")
        else:
            print("  Position changes: None")
        
        if result['deltas']['gap_deltas']:
            print(f"  Gap deltas (sample): {dict(list(result['deltas']['gap_deltas'].items())[:3])}")
        
        if result['deltas']['lap_time_deltas']:
            print(f"  Lap time deltas (sample): {dict(list(result['deltas']['lap_time_deltas'].items())[:3])}")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
