from src.replay_engine import RaceReplay
from src.race_state import RaceState
from src.event_detection import EventDetection
from src.hype_index import HypeIndex
from src.commentary_engine import CommentaryEngine

# Initialize all components
replay = RaceReplay("data/sample_race.csv")
race_state = RaceState(replay.get_total_laps())
event_detector = EventDetection()
hype_calculator = HypeIndex()
commentary_engine = CommentaryEngine()

print("=" * 100)
print("F1 RACE INTELLIGENCE - FULL BACKEND PIPELINE TEST")
print("=" * 100)

while True:
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
        print(f"Events ({len(events)}): {', '.join([e['event_type'] for e in events])}")
    print(f">> COMMENTARY: {commentary}")

print("\n" + "=" * 100)
print("Pipeline Test Complete!")
print("=" * 100)
