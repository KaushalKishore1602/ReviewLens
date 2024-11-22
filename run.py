import uvicorn
import sys
from pathlib import Path

# Ensure ReviewLens root is in python path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import PORT, HOST

if __name__ == "__main__":
    print(f"🚀 Starting ReviewLens AI Review Insights on http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
