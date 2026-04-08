import os
import json
import sys
from pathlib import Path

# Allow running this file directly (e.g. `python database.py`) by ensuring the repo's `src/`
# directory is on `sys.path` so imports like `from lib.orm import DB` work.
SRC_DIR = Path(__file__).resolve().parents[4]
if SRC_DIR.is_dir() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
print(f"Project root determined to be: {project_root}")
# Import after config/print so a missing dependency doesn't hide the engine selection output.
from lib.orm import DB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, "..", "config.json")
try:
    with open(config_path, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

db_cfg = config.get("db", {})
engine_type = db_cfg.get("engine_type", "sqlite").lower()

port_config = config.get("port", {})
BACKEND_PORT = int(port_config.get("back-end"))

if engine_type == "sqlite":
    
    db_file = "AIEvaluationData.db"

db_folder = os.path.join(project_root, "data")
os.makedirs(db_folder, exist_ok=True)

# Full DB path
db_path = os.path.join(db_folder, db_file)


print(f"Database file path: {db_path}")

# SQLite requires a file URL
db_url = f"sqlite:///{db_path}"

db = DB(db_url=db_url, debug=False)

def get_db():
    return db

