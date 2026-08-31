import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def get_database_url() -> str:
    """Resolve SQLite database path to writable platform user AppData directory."""
    env_db = os.environ.get("RESQMESH_DATABASE_URL")
    if env_db:
        return env_db

    if sys.platform == "win32":
        app_data = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if app_data:
            base_dir = Path(app_data) / "ResQMesh AI" / "data"
        else:
            base_dir = Path.home() / ".resqmesh" / "data"
    else:
        base_dir = Path.home() / ".resqmesh" / "data"

    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    db_file = base_dir / "resqmesh.db"
    return f"sqlite:///{db_file.as_posix()}"


SQLALCHEMY_DATABASE_URL = get_database_url()

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
