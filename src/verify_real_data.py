from src.replay_engine import RaceReplay
from src.race_state import RaceState
from src.event_detection import EventDetection
from src.hype_index import HypeIndex
from src.commentary_engine import CommentaryEngine

# Initialize all components with real data
csv_path = "data/real_race_silverstone_2023.csv"
replay = RaceReplay(csv_path)
race_state = RaceState(replay.get_total_laps())
event_detector = EventDetection()
hype_calculator = HypeIndex()
commentary_engine = CommentaryEngine()

print("=" * 100)
print(f"F1 RACE INTELLIGENCE - REAL DATA TEST: {csv_path}")
print("=" * 100)

for lap_num in range(1, 4):
    # 1. Replay Engine
    lap_data = replay.next_lap()
    if lap_data is None:
        break
    
    # 2. Race State
    race_state.update_state(lap_data)
    
    # 3. Event Detection
    events = event_detector.detect_events(race_state)
    
    # 4. Hype Index
    hype_score = hype_calculator.calculate(race_state, events)
    
    # 5. Commentary Generation
    commentary = commentary_engine.generate_commentary(race_state, events, hype_score)
    
    # Output
    print(f"\n[LAP {lap_data['lap_number']}] | Phase: {race_state.current_phase:<10} | Hype: {hype_score:>5}/100")
    if events:
        print(f"  Events ({len(events)}): {', '.join([e['event_type'] for e in events])}")
    print(f"  >> COMMENTARY: {commentary}")
    
    # Detailed telemetry for top 3
    print("  TELEMETRY (TOP 3):")
    for d in lap_data['drivers'][:3]:
        print(f"    - {d.driver}: Pos {d.position} | Gap {d.gap_ahead:.3f} | Lap {d.lap_time:.3f}")

print("\n" + "=" * 100)
print("Verification Complete!")
print("=" * 100)
