# Telemetry-Driven Race Intelligence Engine

A simulated live Formula One race commentary system using historical lap-by-lap data.

## Environment Setup (Windows)

To set up the proper virtual environment and install dependencies, run the following commands:

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the dashboard server
uvicorn src.server:app --reload --port 8000
```

## Core Modules
- `replay_engine`: Load CSV and simulate race progression.
- `event_detection`: Analytical detection of battles, overtakes, and strategy.
- `race_state`: Phase detection and historical memory.
- `hype_index`: Mathematical excitement scoring.
- `commentary_engine`: Context-aware F1-style commentary.
- `server.py`: FastAPI backend.

## Usage
1. Follow the **Environment Setup** instructions above.
2. Open your browser to `http://localhost:8000`.
3. Click "START RACE" to begin the simulation using the **2023 Silverstone GP** dataset.
