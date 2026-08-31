from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.app.database import engine, Base
    import backend.app.models  # Ensure all SQLAlchemy models register on Base.metadata
    from backend.app.api import reports, incidents, messages, ai, node, attachments
except ImportError:
    from app.database import engine, Base
    import app.models
    from app.api import reports, incidents, messages, ai, node, attachments

# Initialize database tables on app startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ResQMesh AI Backend API",
    description="Offline-First Emergency Response Platform REST API",
    version="1.0.0"
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
app.include_router(node.router)
app.include_router(reports.router)
app.include_router(incidents.router)
app.include_router(attachments.router)
app.include_router(messages.router)
app.include_router(ai.router)


try:
    from backend.app.network.discovery import DiscoveryEngine
    from backend.app.sync.outbox_worker import StoreAndForwardWorker
except ImportError:
    from app.network.discovery import DiscoveryEngine
    from app.sync.outbox_worker import StoreAndForwardWorker


@app.on_event("startup")
def startup_services():
    try:
        DiscoveryEngine.get_instance().start()
    except Exception as e:
        print(f"[Warning] Could not start discovery engine: {e}")

    try:
        StoreAndForwardWorker.get_instance().start()
    except Exception as e:
        print(f"[Warning] Could not start outbox worker: {e}")


@app.on_event("shutdown")
def shutdown_services():
    try:
        DiscoveryEngine.get_instance().stop()
    except Exception:
        pass

    try:
        StoreAndForwardWorker.get_instance().stop()
    except Exception:
        pass


@app.get("/")
@app.get("/status")
@app.get("/health")
def health_check():
    """System health and operational status check endpoint."""
    return {
        "status": "ok",
        "service": "ResQMesh AI Backend",
        "version": "1.0.0",
        "mode": "offline-mesh-operational",
    }

