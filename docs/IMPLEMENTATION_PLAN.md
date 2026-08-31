# Implementation Plan: Standalone Windows Desktop Application for ResQMesh AI

Transform ResQMesh AI from a browser/mobile prototype into a fully autonomous, production-quality **Windows Desktop Application** distributed via a professional Windows Installer (`ResQMeshAI-Setup.exe`). The application will run independently on multiple offline Windows laptops, discovering peers over local LAN/Wi-Fi hotspots, synchronizing disaster events via an idempotent outbox engine, and providing role-based disaster response capabilities (Responder vs Command Center).

---

## User Review Required

> [!IMPORTANT]
> **No Manual Process Execution**: The user will never launch Python, Node, or Uvicorn from the command line. The compiled Electron application automatically supervises the embedded native Node Core Engine (`resqmesh-server.exe`) and manages its complete lifecycle.

> [!IMPORTANT]
> **Firewall Strategy**: The NSIS installer will request standard UAC permission once at installation to register inbound and outbound Windows Firewall rules for TCP port `8000` (Node API/WebSocket) and UDP port `52525` (Discovery Broadcast). If denied by an evaluator, the app will display a non-fatal warning and provide in-app diagnostic advice.

> [!NOTE]
> **Ollama LLM Decoupling**: High-memory local LLMs (e.g. Llama-3-8B) will NOT be forced into the installer bundle. The system includes an ultra-fast on-device RAG engine and rule-based heuristic guidance that runs on any laptop (<50MB RAM). Ollama is strictly an optional acceleration layer if present.

---

## Architecture Overview

Each installed instance of ResQMesh AI is a **Peer Node**:
- **Application Shell**: Electron 28+ with React 18 & TypeScript.
- **Node Core Engine**: Standalone compiled binary (`resqmesh-server.exe`) running locally as a child process.
- **Local Database**: SQLite (`resqmesh.db`) stored in `%APPDATA%\ResQMeshAI\data\`.
- **Peer Discovery**: RFC 6762 mDNS Zeroconf (`_resqmesh._tcp.local.`) + UDP broadcast fallback on port `52525`.
- **Data Synchronization**: Idempotent Event Model, Persistent Outbox/Inbox, Last-Writer-Wins (LWW) delta synchronization.
- **Distribution**: Standalone NSIS installer with setup wizard, firewall configuration, desktop/start menu shortcuts, and uninstaller.

---

## Proposed Sequential Implementation Phases

### Phase 1: Shared Event Model & Local Database Architecture
- Unify event definitions (`incident.created`, `incident.updated`, `report.created`, `message.created`, `resource.updated`).
- Implement SQLAlchemy entities in `backend/app/models.py`:
  - `Node`: Node ID, name, role (`responder` | `commander`), public key, last seen, IP.
  - `OperationalIncident`: Real-world master incident, status, severity, category, location.
  - `Report`: Individual responder sighting (immutable raw observation), attached incident ID.
  - `ChatMessage`: Mesh broadcast text, sender node, timestamp.
  - `EventLog`: Immutable ledger of all events with UUID and vector timestamp for duplicate suppression.
  - `OutboxItem`: Pending events to send to peers, retry counters, ACK states.
  - `SyncVector`: Node-to-node synchronization version vectors.

### Phase 2: Local Node Core Engine & Lifecycle Service
- Expose local REST & WebSocket endpoints for Electron UI and peer synchronization:
  - `/api/node/status` & `/api/node/setup`: Initial first-run onboarding (Node Name, Role).
  - `/api/peers/`: Live list of discovered LAN nodes, latency, sync state.
  - `/api/events/sync`: Bidirectional delta sync endpoint.
  - `/api/incidents/`, `/api/reports/`, `/api/comms/`: Operational data endpoints.
- Package entrypoint into `backend/server_entrypoint.py` with dynamic port detection.

### Phase 3: Electron Desktop Application Shell & Process Supervisor
- Implement `desktop/electron/main.js`:
  - Automatically spawns `resqmesh-server.exe` on app startup.
  - Monitors child process health and performs graceful shutdown on window close.
  - Provides native system tray, single-instance lock, and crash recovery.
- Implement `desktop/electron/preload.js` with context-isolated IPC.

### Phase 4: LAN Peer Discovery Engine (mDNS + UDP Broadcast)
- Implement dual-mode discovery in `backend/app/network/`:
  - **mDNS Zeroconf**: Broadcasts node metadata (`name`, `role`, `node_id`, `api_port`).
  - **UDP Broadcast Fallback**: Broadcasts JSON discovery pings every 5 seconds on port `52525` to handle routers blocking mDNS multicast.
  - Maintains live in-memory `PeerRegistry` with offline pruning after 15 seconds of silence.

### Phase 5: Peer Transport, Handshake & Event Synchronization
- Implement authenticated TCP / WebSocket peer connection handshake.
- Exchange Node IDs and verify Ed25519 digital signatures.
- Outbox/Inbox sync loop:
  1. Peer connects $\rightarrow$ exchange `SyncVector` (highest event IDs per node).
  2. Compute missing event deltas $\rightarrow$ stream missing events with CRC32 framing.
  3. Ingest events idempotently $\rightarrow$ send ACK $\rightarrow$ resolve conflicts via Last-Writer-Wins.

### Phase 6: Store-and-Forward Mesh Relay
- Hop-limited flooding protocol:
  - Each forwarded packet carries `ttl` (default: 5) and `hop_count`.
  - `SeenPacketCache` (LRU cache of 10,000 event IDs) suppresses duplicate transmissions.
  - Intermediary relay nodes forward events to newly discovered nodes even if the originating node is offline.

### Phase 7: Role-Based Desktop UI (Responder Mode vs Command Center)
- Reorganize Desktop UI in `desktop/src/`:
  - **First-Run Onboarding Modal**: Choose Node Name (`Laptop-A`) and Role (`Responder` vs `Commander`).
  - **Responder Mode**: Streamlined layout for field operators (Report Incident with Landmark selection, Tactical Chat, My Reports, Connected Peers).
  - **Command Center Mode**: Full operations center (Tactical Map, AI Duplicate Review Card, Resource Dispatch, RAG SOP Guidance, Network Topology).

### Phase 8: On-Device AI Decision Support & SOP RAG
- **Incident Correlation**: Multi-factor similarity scoring (Haversine spatial distance + temporal delta + category match + text token overlap) to flag duplicates.
- **Local SOP RAG**: Sparse cosine similarity vector index pre-seeded with FEMA/NDMA emergency operating procedures (Fire, Flood, Trauma, Structural, HazMat) generating 3-step tactical guidance without internet.

### Phase 9: Windows NSIS Packaging & Installer Experience
- Create `installer/nsis/installer.nsh`:
  - Setup wizard with custom install location, Start Menu shortcuts, and Desktop icon.
  - Windows Firewall configuration hook via `netsh advfirewall`.
  - Bundled PyInstaller executable and static frontend assets.
  - Clean uninstaller (`Uninstall ResQMesh AI.exe`) with option to preserve or purge local database.

### Phase 10: Multi-Laptop Simulation, Verification & Runbook
- Build automated integration test suite simulating 3+ virtual laptops with network partition, reconnection, and event convergence.
- Produce `docs/EVALUATION_MANUAL.md` for evaluators with step-by-step test scenarios.

---

## Verification Plan

### Automated Tests
- Unit test suite: `pytest tests/backend/` (Models, Sync Engine, Discovery, AI Correlation, RAG).
- Multi-node simulation test: `python tests/simulation/mesh_simulator.py` (Validating partition reconnection and LWW consensus).
- Electron build verification: `npm run build` in `desktop/`.

### Manual Multi-Laptop Verification Procedure
1. Install `ResQMeshAI-Setup.exe` on **Laptop A** and **Laptop B**.
2. Connect both laptops to an offline Wi-Fi router or mobile hotspot (Zero Internet).
3. Launch ResQMesh AI on both laptops.
4. Verify Laptop A automatically discovers Laptop B in the "Connected Peers" panel.
5. Create an incident on Laptop A; verify it appears in real-time on Laptop B.
6. Disconnect Laptop B from Wi-Fi; create a second incident on Laptop A.
7. Reconnect Laptop B to Wi-Fi; verify the missing incident synchronizes automatically without duplicates.
8. Test AI Duplicate Correlation by submitting a report with similar landmark description.
9. Verify uninstallation via Windows Settings > Installed Apps.
