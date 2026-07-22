# ResQMesh AI

**ResQMesh AI** is an offline-first emergency response platform combining peer-to-peer mesh networking (BLE, Wi-Fi Direct, mDNS LAN) with on-device AI (local LLMs & RAG SOP retrieval) to coordinate disaster response without central internet infrastructure.

---

## Architecture Overview

- **Mobile App (`mobile/`)**: React Native mobile app for field responders (incident creation, off-grid peer messaging, location tracking).
- **Backend API (`backend/`)**: Python / FastAPI local backend serving local SQLite operations, AI pipeline, and sync server.
- **Desktop Command Center (`desktop/`)**: Electron / React dashboard for incident monitoring, live mapping, and task dispatch.
- **Shared Schemas (`shared/`)**: JSON Schemas defining data event contracts (Incidents, Messages, Resources, Sync Acks) shared across client runtimes.

---

## Project Structure

```
.
├── backend/            # Python FastAPI service, database models, AI runtime, network listeners
├── mobile/             # React Native mobile application
├── desktop/            # Electron / React desktop command center dashboard
├── shared/             # Shared JSON event schemas and contracts
└── tests/              # Multi-node mesh simulation & integration test suites
```

---

## Development Setup

### Backend Prerequisites
- Python 3.10+
- SQLite 3

```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
pip install -r requirements.txt
```

---

## License
MIT License
