# ResQMesh AI: Offline-First Emergency Response Platform & Tactical Mesh Network

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production--Ready-emerald.svg)]()
[![Platform: Windows | Android | iOS](https://img.shields.io/badge/Platform-Windows%20%7C%20Android%20%7C%20iOS-indigo.svg)]()
[![Zero-Cloud Autonomy](https://img.shields.io/badge/Zero--Cloud-100%25%20Offline-orange.svg)]()

> **Live Release Download Web Portal**: [https://res-q-mesh-cinematic-website--suchithssara.replit.app/](https://res-q-mesh-cinematic-website--suchithssara.replit.app/)

---

## 🚀 Executive Overview & Mission

**ResQMesh AI** is a mission-critical, offline-first tactical command center and distributed peer-to-peer mesh response platform designed to operate when centralized infrastructure (cellular towers, public internet, cloud data centers, and power grids) has experienced total catastrophic failure.

During major disasters—such as earthquakes, severe floods, super cyclones, or grid blackouts—communication networks collapse precisely when emergency response is most needed. **ResQMesh AI** restores full operational capability by combining:
1. **Ad-Hoc Peer-to-Peer Mesh Networking**: Relaying incident packets across mobile nodes, desktop command centers, and tactical squad devices without internet.
2. **On-Device AI RAG (Retrieval-Augmented Generation)**: Providing instant, offline disaster management advice and Standard Operating Procedures (SOPs) based on NDMA, WHO, IFRC, and INSARAG guidelines.
3. **Authentic Offline Geospatial Mapping Engine**: Hardware-accelerated MapLibre GL JS vector maps running Survey of India boundaries and 175,800+ road features completely offline with **< 350 ms** instant startup.
4. **Hero 3D Earth WebGL Globe**: A Three.js 3D earth visualizer with distance-aware marker scaling and raycasting detail inspection.
5. **Real Hardware Location & 5-Case Fallback Suite**: Sensor-accurate location querying with true accuracy reporting ($\pm 20\text{ m}$ threshold) and zero fabricated coordinates.

---

## 🌐 Official Download & Live Portal

Download the latest production Windows NSIS standalone setup installer (`ResQMeshAI-Setup.exe`) or explore project documentation:

👉 **[Download ResQMesh AI Production Release](https://res-q-mesh-cinematic-website--suchithssara.replit.app/)**

---

## 🏛️ Core Architectural Pillars

### 1. 100% Zero-Cloud Local Autonomy
- Operates entirely on local hardware (local SQLite database, local FastAPI Python server, embedded RAG SOP index, vector tiles, local gazetteer).
- **Zero external API calls**, zero telemetry tracking, and zero phone-home dependencies. Works in 100% air-gapped environments.

### 2. Distributed Ad-Hoc P2P Mesh Network
- Autonomous peer discovery over local LAN, ad-hoc Wi-Fi, Wi-Fi Direct, and Bluetooth Low Energy (BLE).
- Dynamic multi-hop packet routing up to **TTL 5** with reverse-path caching, latency measurement ($O(1)$ link scoring), and loop suppression via `SeenPacketCache`.

### 3. On-Device AI RAG SOP Engine
- Embedded disaster management SOP knowledge base indexing 17 authoritative emergency protocols from **NDMA (India)**, **WHO**, **IFRC**, and **INSARAG**.
- Runs completely on local hardware without OpenAI, Anthropic, or external cloud LLMs.

### 4. Active Incident Duplicate Correlation AI
- Continuous background multi-signal AI engine scanning incidents across the mesh.
- Computes weighted score using Haversine spatial distance, lexical token overlap, category matching, severity compatibility, and temporal proximity to detect duplicate reports and merge them safely.

### 5. Real Physical Location & 5-Case Fallback Suite
- Prioritizes true physical GNSS/GPS sensors, Windows Location API, and high-accuracy browser position.
- Enforces an operational $\pm 20\text{ m}$ accuracy threshold.
- Features a structured 5-case fallback suite (Cases A–E) for degraded environments, keeping address data intact without generating fake coordinates.

### 6. Authentic Offline MapLibre GL Cartography
- 100% authentic Survey of India district and state boundaries for Telangana.
- 175,803 real OpenStreetMap roads partitioned into 163 Zoom-13 spatial grid tiles with in-memory LRU pre-fetching.
- 77-entry local offline gazetteer with sub-millisecond autocomplete.

---

## ⚙️ System Architecture

```
+---------------------------------------------------------------------------------------+
|                                    RESQMESH AI ARCHITECTURE                           |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|   +------------------------------------+    +-------------------------------------+   |
|   |    ELECTRON COMMAND CENTER         |    |      PYTHON BACKEND DAEMON          |   |
|   |    (React 18 + TypeScript + Vite)  |    |      (FastAPI + SQLite + Uvicorn)   |   |
|   |                                    |    |                                     |   |
|   |   - Hero 3D Earth WebGL Globe      |    |   - SQLite Local Transaction Store  |   |
|   |   - MapLibre GL Offline Map Picker |    |   - ResQMesh Dynamic Router         |   |
|   |   - Live Tactical Activity Feed    |    |   - On-Device AI RAG SOP Engine     |   |
|   |   - Incident Merge AI Panel        |    |   - UDP Broadcast Peer Discovery    |   |
|   |   - Tactical Squad Logistics View  |<-->|   - Multi-Hop Hop Limiter & Cache   |   |
|   |   - Offline Gazetteer Search       |    |   - Role-Based Access Control       |   |
|   +------------------------------------+    +-------------------------------------+   |
|                      |                                         |                      |
|                      v                                         v                      |
|   +------------------------------------+    +-------------------------------------+   |
|   |    OFFLINE GEOSPATIAL ASSETS       |    |      DISTRIBUTED MESH NETWORK       |   |
|   |    (Bundled Locally in App)        |    |      (P2P Ad-Hoc Interconnect)      |   |
|   |                                    |    |                                     |   |
|   |   - 163 Zoom-13 Spatial Road Tiles |    |   - Node-to-Node Socket Peering     |   |
|   |   - Survey of India Districts      |    |   - Direct 1-Hop Neighbor Orbit     |   |
|   |   - National Highways Network      |    |   - Multi-Hop Outer Orbit Relays    |   |
|   |   - 635 Authentic Water Bodies     |    |   - Mobile Field Nodes (React Native|   |
|   +------------------------------------+    +-------------------------------------+   |
|                                                                                       |
+---------------------------------------------------------------------------------------+
```

---

## 🛠️ How It Works

```
[ Field Responder / Citizen ]
           │ (Reports Incident via Handheld Mobile / Desktop)
           ▼
[ Hardware Location Engine ] ──► (GNSS / Windows / Fallback Suite A-E)
           │
           ▼
[ Local SQLite & FastAPI Daemon ]
           │
           ├───────────────────────────────┐
           ▼                               ▼
[ P2P Mesh Network Router ]       [ On-Device AI Pipeline ]
  - UDP/mDNS Peer Discovery         - RAG SOP Advisor (NDMA/WHO)
  - Multi-Hop TTL 5 Relaying        - Duplicate Merge AI Engine
  - Latency & Quality Metrics       - Automated START Triage
           │
           ▼
[ Desktop Command Center Dashboard ]
  - Three.js 3D WebGL Earth Globe
  - MapLibre GL Offline Vector GIS Map
  - Live Tactical Activity Stream
  - Squad Dispatch & Resource Management
```

### Operational Workflow:
1. **Incident Reporting**: A field responder inputs an emergency report (e.g., Flood Evacuation, Building Collapse, Trauma Case). The system acquires hardware GNSS coordinates or falls back to map pin selection or manual address fields.
2. **Mesh Packet Propagation**: The incident is packaged into a signed binary/JSON mesh packet and broadcast across local Wi-Fi, Ethernet, or BLE. Surrounding nodes receive, index, and relay the packet up to 5 hops away.
3. **Command Center Operations**: Command operators see real-time incidents plotted on both the 3D WebGL Earth Globe and the high-precision MapLibre GL GIS Map.
4. **On-Device AI Analysis**: 
   - **RAG SOP Advisor**: Instant tactical response recommendations derived locally from 17 emergency manuals.
   - **Duplicate Correlation Engine**: Automatically flags duplicate incoming reports from different citizens/nodes and presents a side-by-side merge interface.
5. **Logistics & Squad Allocation**: Dispatchers allocate rescue squads, medical supplies, or heavy equipment to active incidents based on automated START triage priority.

---

## 📱 How to Use ResQMesh AI

### Option A: Using the Standalone Windows Desktop Installer (Recommended)
1. Download `ResQMeshAI-Setup.exe` from the **[Official Download Web Portal](https://res-q-mesh-cinematic-website--suchithssara.replit.app/)**.
2. Run the setup installer. It automatically configures the desktop shell, offline geospatial tiles, and embedded backend daemon.
3. Launch **ResQMesh AI** from your Start Menu or Desktop shortcut.

### Option B: Running the Command Center
- **Create an Incident**: Click `+ Report Incident` in the navigation sidebar or top menu. Fill in title, category, severity, and photo attachments. Verify location or pick a point on the offline map.
- **View Offline GIS Map**: Open `GIS Operational Map` to inspect high-resolution road vectors, district boundaries, water bodies, and emergency markers. Use the gazetteer search bar to jump to any location offline.
- **Inspect Peer Topology**: Click `Mesh Network` or open the Peer Topology visualizer to see direct 1-hop peers, multi-hop relayed nodes, round-trip latency, and link quality.
- **Ask AI Advisor**: Open the `AI Decision Advisor` panel, select a quick scenario chip (e.g., *Building Collapse*, *Flood Evacuation*), or type a custom query to get instant offline SOP guidance.
- **Review Duplicate Reports**: Check the `Incident Merge AI Panel`. If correlated duplicate reports are detected, click `Review Match` to inspect side-by-side data and click `Merge Incidents`.
- **Manage Logistics & Squads**: Access `Resource Management` and `Squad Readiness` to track inventory, submit equipment requests, and assign squads to critical incidents.

---

## 💻 Developer Installation & Setup Guide

### 1. Prerequisites
- **Node.js**: `v18.x` or `v20.x`
- **Python**: `3.10.x` (64-bit)
- **Git**: Installed and configured

### 2. Clone the Repository
```bash
git clone https://github.com/suchithsaraaaa/resqmesh.git
cd resqmesh
```

### 3. Backend Setup (`backend/`)
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server daemon
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend API documentation will be available locally at `http://127.0.0.1:8000/docs`.*

### 4. Desktop Command Center Setup (`desktop/`)
```bash
cd desktop

# Install npm packages
npm install

# Run Vite development server
npm run dev

# Or run full Electron application with live backend connection
npm run electron:dev
```

### 5. Mobile Node App (`mobile/`)
```bash
cd mobile

# Install dependencies
npm install

# Start React Native Metro bundler
npm start
```

---

## 🧪 Automated Testing Runbook

To run the complete Python backend test suite covering dynamic mesh routing, REST endpoints, P2P sync, and triage scoring:

```bash
# Run from backend/ or repository root
python -m pytest backend/tests/test_router.py backend/tests/test_api.py backend/tests/test_sync.py backend/tests/test_triage.py
```
*Expected Result*: **100% Passed** (110+ unit & integration tests).

---

## 📦 Production Build & Installer Packaging

### 1. Recompile Standalone Backend Executable
```bash
cd backend
pyinstaller --clean --noconfirm resqmesh-server.spec
cd ..
```
*Generates executable at `backend/dist/resqmesh-server/resqmesh-server.exe`.*

### 2. Compile Desktop Frontend
```bash
cd desktop
npm run build
cd ..
```

### 3. Package Windows Setup Installer
```bash
cd desktop
npm run dist
cd ..
```
*Generates Windows NSIS installer inside `release/ResQMeshAI-Setup-v1.0.XX.exe`.*

---

## 📑 RESTful API Overview

The Python backend exposes local endpoints at `http://127.0.0.1:8000`:

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Incidents** | `GET` | `/incidents` | List all reported incidents with status/severity filters |
| **Incidents** | `POST` | `/incidents` | Broadcast a new emergency incident report |
| **Incidents** | `PATCH` | `/incidents/{id}` | Update incident status (`OPEN`, `IN_PROGRESS`, `RESOLVED`) |
| **Incidents** | `POST` | `/incidents/merge` | Safely merge two correlated duplicate incidents |
| **Mesh Network**| `GET` | `/node/status` | Current node telemetry, tactical role, and battery level |
| **Mesh Network**| `GET` | `/node/peers` | List directly connected 1-hop physical peers |
| **Mesh Network**| `GET` | `/node/routes` | Active multi-hop routing table sorted by hop count |
| **Mesh Network**| `GET` | `/node/topology`| Complete mesh network graph topology |
| **AI SOP RAG** | `POST` | `/ai/query` | Query local disaster SOP knowledge base without internet |
| **AI Triage** | `POST` | `/ai/triage` | Calculate automated START triage priority score |
| **Logistics** | `GET` | `/resources` | Master inventory of available emergency resources |
| **Logistics** | `GET` | `/squads` | Operational status and readiness of tactical rescue squads |

---

## 🧰 Technology Stack

- **Desktop Command Shell**: Electron 44, React 18, TypeScript, Vite 5
- **3D & Cartography Engines**: Three.js (3D WebGL Globe), MapLibre GL JS (Offline Vector Map), PMTiles
- **Backend Service Daemon**: Python 3.10, FastAPI, Uvicorn, SQLAlchemy, SQLite3, Pydantic
- **Mesh Networking**: Custom Dynamic Router, ZeroConf (mDNS/DNS-SD), TCP Sockets, PyCryptodome
- **On-Device AI**: Local Vector SOP Index (NDMA/WHO/INSARAG), Weighted Multi-Signal Duplicate Correlation Engine
- **Mobile Field App**: React Native, React Native SQLite Storage, React Navigation
- **Installer Packaging**: Electron-Builder, PyInstaller, NSIS Installer Framework

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 🌐 Official Download Portal

Download the official production installer, view screenshots, and explore project media:

👉 **[ResQMesh AI Web Portal & Installer Download](https://res-q-mesh-cinematic-website--suchithssara.replit.app/)**
