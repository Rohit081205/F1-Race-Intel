from src.replay_engine import RaceReplay
from src.race_state import RaceState
from src.event_detection import EventDetection
from src.hype_index import HypeIndex
from src.commentary_engine import CommentaryEngine

csv_path = 'data/real_race_silverstone_2023.csv'
replay = RaceReplay(csv_path)
race_state = RaceState(replay.get_total_laps())
event_detector = EventDetection()
hype_calculator = HypeIndex()
commentary_engine = CommentaryEngine()

for i in range(3):
    lap = replay.next_lap()
    if not lap:
        break
    race_state.update_state(lap)
    events = event_detector.detect_events(race_state)
    hype = hype_calculator.calculate(race_state, events)
    commentary = commentary_engine.generate_commentary(race_state, events, hype)
    print(f"Lap {lap['lap_number']}: Hype {hype}, {commentary}")
