from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from app.config import STATIC_DIR
from app.routes import (
    serve_index,
    download_sample_csv,
    api_upload_csv,
    api_load_sample,
    api_generate_reply,
    api_clear_cache,
    api_health
)

routes = [
    Route("/", endpoint=serve_index, methods=["GET"]),
    Route("/api/upload", endpoint=api_upload_csv, methods=["POST"]),
    Route("/api/load-sample", endpoint=api_load_sample, methods=["POST"]),
    Route("/api/reply", endpoint=api_generate_reply, methods=["POST"]),
    Route("/api/sample-csv", endpoint=download_sample_csv, methods=["GET"]),
    Route("/api/clear-cache", endpoint=api_clear_cache, methods=["POST"]),
    Route("/api/health", endpoint=api_health, methods=["GET"]),
    Mount("/static", app=StaticFiles(directory=str(STATIC_DIR)), name="static"),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(debug=True, routes=routes, middleware=middleware)
