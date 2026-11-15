import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="FishFlow API",
    description="High-precision Solunar & Barometric Fish Activity Engine (Free & Homelab Optimized)",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "FishFlow Unified Service",
        "version": "1.0.0"
    }


# Static frontend mounting for single-container homelab deployment
possible_static_paths = [
    os.getenv("STATIC_DIR"),
    os.path.join(os.path.dirname(__file__), "..", "static"),
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"),
    "/app/static"
]

static_dir = None
for p in possible_static_paths:
    if p and os.path.isdir(p) and os.path.exists(os.path.join(p, "index.html")):
        static_dir = os.path.abspath(p)
        break

if static_dir:
    assets_path = os.path.join(static_dir, "assets")
    if os.path.isdir(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        if full_path.startswith("api") or full_path == "health" or full_path.startswith("docs") or full_path == "openapi.json":
            raise HTTPException(status_code=404, detail="Not Found")
        
        # Confinement check to prevent path traversal (CWE-22)
        resolved_target = os.path.abspath(os.path.join(static_dir, full_path))
        if resolved_target.startswith(static_dir) and os.path.isfile(resolved_target):
            return FileResponse(resolved_target)
        return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
