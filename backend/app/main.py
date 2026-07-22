from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.app.database import engine, Base
    from backend.app.api import reports, incidents, messages
except ImportError:
    from app.database import engine, Base
    from app.api import reports, incidents, messages

# Initialize database tables on app startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ResQMesh AI Backend API",
    description="Offline-First Emergency Response Platform REST API",
    version="0.1.0"
)

# CORS middleware for Desktop (Electron) and Web frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(reports.router)
app.include_router(incidents.router)
app.include_router(messages.router)


@app.get("/health")
def health_check():
    """System health check endpoint."""
    return {"status": "ok", "service": "ResQMesh AI Backend", "version": "0.1.0"}
