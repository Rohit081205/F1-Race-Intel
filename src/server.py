"""
FastAPI Server for Race Intelligence Engine

Exposes the race intelligence system through a typed REST API.
Manages the lifecycle of a race and orchestrates the backend modules.
"""

from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

# Module imports
from src.replay_engine import RaceReplay, LapData
from src.race_state import RaceState
from src.event_detection import EventDetection
from src.hype_index import HypeIndex
from src.commentary_engine import CommentaryEngine

# --- Pydantic Models ---

class DriverState(BaseModel):
    driver: str
    position: int
    lap_time: float
    gap_ahead: float
    tire_compound: str
    tire_age: int

class RaceEvent(BaseModel):
    lap: int
    event_type: str
    drivers_involved: List[str]
    score: float

class RaceStateResponse(BaseModel):
    lap_number: int
    total_laps: int
    race_phase: str
    hype_index: float
    drivers: List[DriverState]
    events: List[RaceEvent]
    commentary: str

# --- Application Setup ---

app = FastAPI(title="F1 Race Intelligence Engine")

# Global lifecycle state (for demo purposes)
class RaceLifecycle:
    def __init__(self):
        self.replay: Optional[RaceReplay] = None
        self.state: Optional[RaceState] = None
        self.event_detector = EventDetection()
        self.hype_calculator = HypeIndex()
        self.commentary_engine = CommentaryEngine()
        self.current_response: Optional[RaceStateResponse] = None

race = RaceLifecycle()

# Mount static files and serve index at root
dashboard_path = Path("dashboard")
if dashboard_path.exists():
    app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")

@app.get("/")
async def read_index():
    index_file = dashboard_path / "index.html"
    if index_file.exists():
        from fastapi.responses import FileResponse
        return FileResponse(index_file)
    return {"message": "F1 Race Intelligence Engine API - Dashboard not found"}

# --- Helper Logic ---

def build_response(lap_data: Dict, race_state: RaceState, events: List[Dict], hype: float, commentary: str) -> RaceStateResponse:
    """
    Cleaner transformation of internal objects to Pydantic models.
    """
    drivers = [
        DriverState(
            driver=d.driver,
            position=d.position,
            lap_time=d.lap_time,
            gap_ahead=d.gap_ahead,
            tire_compound=d.tire_compound,
            tire_age=d.tire_age
        )
        for d in lap_data['drivers']
    ]
    
    event_list = [
        RaceEvent(
            lap=e['lap'],
            event_type=e['event_type'],
            drivers_involved=e['drivers_involved'],
            score=e['score']
        )
        for e in events
    ]
    
    return RaceStateResponse(
        lap_number=race_state.current_lap,
        total_laps=race_state.total_laps,
        race_phase=race_state.current_phase,
        hype_index=hype,
        drivers=drivers,
        events=event_list,
        commentary=commentary
    )

# --- API Endpoints ---

@app.post("/api/race/start", response_model=RaceStateResponse)
async def start_race(csv_path: str = "data/real_race_silverstone_2023.csv"):
    """
    Initialize and start a new race simulation.
    """
    if not Path(csv_path).exists():
        raise HTTPException(status_code=404, detail=f"CSV file not found at {csv_path}")
        
    race.replay = RaceReplay(csv_path)
    race.state = RaceState(total_laps=race.replay.get_total_laps())
    
    # Auto-start at Lap 1
    lap_data = race.replay.next_lap()
    race.state.update_state(lap_data)
    
    events = race.event_detector.detect_events(race.state)
    hype = race.hype_calculator.calculate(race.state, events)
    commentary = race.commentary_engine.generate_commentary(race.state, events, hype)
    
    race.current_response = build_response(lap_data, race.state, events, hype, commentary)
    return race.current_response

@app.post("/api/race/next-lap", response_model=RaceStateResponse)
async def next_lap():
    """
    Advance the race replay by one lap.
    """
    if not race.replay or not race.state:
        raise HTTPException(status_code=400, detail="Race not started. Call /api/race/start first.")
        
    lap_data = race.replay.next_lap()
    
    if lap_data is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    race.state.update_state(lap_data)
    
    events = race.event_detector.detect_events(race.state)
    hype = race.hype_calculator.calculate(race.state, events)
    commentary = race.commentary_engine.generate_commentary(race.state, events, hype)
    
    race.current_response = build_response(lap_data, race.state, events, hype, commentary)
    return race.current_response

@app.get("/api/race/state", response_model=RaceStateResponse)
async def get_state():
    """
    Get the current snapshot of the race.
    """
    if not race.current_response:
        raise HTTPException(status_code=400, detail="No active race state found.")
    return race.current_response
