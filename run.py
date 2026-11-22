import os
import sys
from pathlib import Path
import uvicorn

# Ensure ReviewLens root is in python path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import PORT, HOST

if __name__ == "__main__":
    port = int(os.getenv("PORT", PORT))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"🚀 Starting ReviewLens AI Review Insights on http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
