# ResQMesh AI: Complete System Master Specification & Technical Inventory

> **System Designation**: ResQMesh AI — Offline-First Emergency Response Platform  
> **Repository Root**: `d:\Final_year_project\`  
> **Current Version**: `v1.0.29` (`ResQMeshAI-Setup-v1.0.29.exe`)  
> **Status**: Production-Ready / Fully Verified & Packaged  
> **Core Mandate**: 100% Offline Autonomy • Zero Cloud Dependency • Real Hardware Location • Multi-Hop Mesh Routing • On-Device AI Decision Support (~900 MB Knowledge Base)

---

## 1. Executive System Overview & Mission Architecture

ResQMesh AI is a mission-critical, offline-first tactical command center and distributed peer-to-peer mesh response platform designed to operate when centralized infrastructure (cellular towers, public internet, cloud data centers, and power grids) has experienced total catastrophic failure.

### Core Architectural Pillars:
1. **Zero-Cloud Local First**:
   - The entire platform (database, REST API server, AI inference engine, 3D WebGL globe, vector map tiles, and gazetteer) executes strictly on local device hardware.
   - Zero external API requests; zero phone-home calls; zero telemetry tracking.
2. **Distributed Ad-Hoc Mesh Networking**:
   - Autonomous peer discovery over local LAN, ad-hoc Wi-Fi, Wi-Fi Direct, and Bluetooth Low Energy (BLE).
   - Dynamic multi-hop packet routing up to TTL 5 with reverse-path caching, latency metrics, and loop suppression via `SeenPacketCache`.
3. **On-Device AI RAG (Retrieval-Augmented Generation)**:
   - Embedded disaster management SOP knowledge base indexing authoritative protocols from NDMA (India), WHO, IFRC, and INSARAG.
   - Operates completely on local CPU without OpenAI, Anthropic, or external LLM cloud endpoints.
4. **Active Incident Duplicate Correlation AI**:
   - Background multi-signal AI correlation engine running continuously across incidents.
   - Computes weighted spatial Haversine distance, lexical token overlap, category matching, severity compatibility, and temporal proximity to detect and merge duplicate reports.
5. **Real Physical Device Location & Comprehensive Fallback**:
   - Queries real physical GNSS/GPS sensors, Windows Location API, and high-accuracy browser geolocation.
   - Evaluates true hardware accuracy against an operational $\pm 20\text{ m}$ threshold.
   - Features a 5-case fallback suite (Cases A–E) with structured manual address fields and zero fabricated coordinates.
6. **Authentic Offline Geospatial Mapping Engine**:
   - Hardware-accelerated MapLibre GL JS WebGL vector map.
   - 100% authentic Survey of India district and state boundaries for Telangana.
   - 175,803 real OpenStreetMap road ways partitioned into an open-world Zoom-13 spatial grid tile pyramid with an in-memory LRU cache.
   - Instant startup (< 350 ms) and 60 FPS pin dragging.
7. **Hero 3D Earth WebGL Globe**:
   - Three.js WebGL globe rendering sovereign nation boundaries offline from vector assets.
   - Distance-aware marker scaling (`markerScale = 0.28 + tDist * 0.72`) with permanent WebGL lifecycle and zero camera resets.

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

## 2. Exhaustive Technology & Dependency Inventory

### 2.1 Desktop Command Center (`desktop/`)

| Technology / Library | Exact Version | Type | Architectural Purpose & Configuration |
| :--- | :--- | :--- | :--- |
| **Electron** | `^44.0.0` | Runtime Shell | Host platform providing native OS windowing, file system access, hardware location, and background daemon lifecycle. |
| **React** | `^18.2.0` | UI Library | Component hierarchy, state management, and virtual DOM reconciliation for the tactical dashboard. |
| **React DOM** | `^18.2.0` | UI Library | Web rendering bindings for React components. |
| **TypeScript** | `^5.3.3` | Language | Strict static typing across components, event buses, telemetry interfaces, and data models. |
| **Vite** | `^5.0.12` | Build Tool / Bundler | Next-generation ESM bundler providing instant HMR in dev and optimized tree-shaken chunks in production. |
| **MapLibre GL JS** | `^5.24.0` | Map Engine | GPU-accelerated WebGL cartographic engine for the offline Telangana map picker with custom styling. |
| **Three.js** | `^0.185.1` | 3D Graphics | WebGL rendering engine powering the Hero 3D Earth Globe with Raycasting and spherical coordinate projection. |
| **PMTiles** | `^4.5.0` | Vector Tile Format | Cloud-optimized vector tile reader for local archive storage. |
| **Leaflet** | `^1.9.4` | Fallback Map | Lightweight 2D map library retained for legacy coordinate plotting. |
| **Electron-Builder** | `^26.15.3` | Packaging / Installer | Compiles Windows NSIS installers (`x64`), packages ASAR archives, and bundles the PyInstaller backend. |
| **@vitejs/plugin-react**| `^4.2.1` | Vite Plugin | Fast Refresh and JSX transformation support for React inside Vite. |
| **@types/three** | `^0.185.4` | Type Definitions | TypeScript typings for Three.js geometries, materials, scenes, cameras, and OrbitControls. |
| **@types/leaflet** | `^1.9.8` | Type Definitions | TypeScript typings for Leaflet map elements and layer handlers. |
| **@types/react** | `^18.2.48` | Type Definitions | TypeScript typings for React core hooks, components, and synthetic events. |
| **@types/react-dom** | `^18.2.18` | Type Definitions | TypeScript typings for React DOM entry points. |

### 2.2 Python Backend Server (`backend/`)

| Technology / Library | Exact Version | Type | Architectural Purpose & Configuration |
| :--- | :--- | :--- | :--- |
| **Python** | `3.10.8 (x64)` | Runtime Environment | High-performance backend runtime executing the API daemon, mesh router, and AI pipeline. |
| **FastAPI** | `>=0.110.0` | Web Framework | Modern, high-performance async REST API framework with automatic OpenAPI documentation and Pydantic validation. |
| **Uvicorn** | `>=0.28.0` | ASGI Web Server | Lightning-fast ASGI web server running the FastAPI application on `127.0.0.1:8000`. |
| **SQLAlchemy** | `>=2.0.28` | ORM / Database Toolkit | Object-relational mapping and database abstraction for SQLite tables (incidents, nodes, resources, routes). |
| **SQLite3** | `3.x (Built-in)` | Embedded Database | Zero-configuration, serverless, transactional SQL database engine stored in `backend/resqmesh.db`. |
| **Pydantic** | `>=2.6.4` | Data Validation | Strict data parsing, type enforcement, and schema serialization for incident reports and mesh packets. |
| **Pydantic Settings** | `>=2.2.1` | Config Management | Environment variable parsing and application configuration loading. |
| **ZeroConf** | `>=0.131.0` | Network Discovery | Pure Python Multicast DNS (mDNS) / DNS-SD library for automatic LAN peer discovery. |
| **Requests** | `>=2.31.0` | HTTP Client | Synchronous HTTP client for inter-node direct mesh sync and telemetry forwarding. |
| **Pytest** | `>=8.1.1` | Testing Framework | Comprehensive unit and integration testing suite covering router, API, sync, and triage engines. |
| **Pytest-Asyncio** | `>=0.23.5` | Async Testing | Test runners for asynchronous FastAPI endpoints and async router methods. |
| **Python-Multipart** | `>=0.0.9` | Request Parser | Streaming parser for multipart form data (incident photo uploads and attachments). |
| **Cryptography** | `>=42.0.0` | Security / Encryption | Cryptographic primitives for packet signing and sensitive field hashing. |
| **PyInstaller** | `6.x` | Binary Compiler | Packages the complete Python runtime, FastAPI app, and dependencies into `backend/dist/resqmesh-server/`. |

### 2.3 Mobile P2P Node (`mobile/`)

| Technology / Library | Exact Version | Type | Architectural Purpose & Configuration |
| :--- | :--- | :--- | :--- |
| **React Native** | `0.73.6` | Mobile Framework | Cross-platform native mobile application framework for field responder handheld devices. |
| **React** | `18.2.0` | UI Library | Declarative UI components for mobile incident broadcasting and squad messaging. |
| **React Navigation** | `^7.3.13` | Navigation Library | Stack navigation and tab routing for mobile screens. |
| **React Native SQLite**| `^6.0.1` | Embedded Database | Native SQLite bindings (`react-native-sqlite-storage`) for local offline mobile incident caching. |
| **React Native Screens** | `^4.26.2` | Native Optimization | Native view management for smooth 60 FPS transitions on Android and iOS. |
| **React Native Safe Area**| `^5.8.0` | UI Utility | Safe area inset handling for notch and gesture navigation displays. |
| **UUID** | `^14.0.1` | Identification | RFC4122 UUID v4 generation for decentralized incident and packet identification. |

---

## 3. Subsystem Deep-Dive Specifications

### 3.1 Subsystem A: Desktop Command Center (Electron Shell)
- **Entry Points**:
  - `desktop/electron/main.js`: Main Electron process. Launches the browser window, configures secure IPC handlers (`get-node-port`, `load-geojson`, `open-external-url`), manages window lifecycle, and spawns the compiled Python server daemon (`resqmesh-server.exe`).
  - `desktop/electron/preload.js`: Context isolation bridge exposing `window.resqmeshAPI` securely to the renderer process.
  - `desktop/src/main.tsx`: React application root mounting into `index.html`.
  - `desktop/src/App.tsx`: Master state controller managing active navigation views, modal dialogs, global event listeners, and periodic telemetry polls.
- **Glassmorphic Design System (`desktop/src/styles/designTokens.ts`)**:
  - Background Canvas: `#060A12` (deep tactical navy)
  - Surface Cards: `#0D1422` with `1px solid #1E293B` borders and `20px` corner radii
  - Accent Color: `#38BDF8` (electric cyan with glow filters)
  - Typography: System sans-serif with monospace coordinate/telemetry readouts (`Courier New`, `Menlo`)

### 3.2 Subsystem B: Authentic Offline Geospatial Mapping Engine
- **Engine**: MapLibre GL JS (`5.24.0`) integrated inside `desktop/src/components/LocationPickerModal.tsx`.
- **Authoritative Survey of India Vector Datasets**:
  - State Boundary: `desktop/src/assets/geo/telangana-boundary.json` (30 KB, clean topological union).
  - District Boundaries: `desktop/src/assets/geo/telangana-districts.json` (66 KB, authentic Survey of India polygons for `Adilabad`, `Hyderabad`, `Karimnagar`, `Khammam`, `Mahabubnagar`, `Medak`, `Nalgonda`, `Nizamabad`, `Rangareddy`, `Warangal`).
- **Road Vector Tile Pyramid**:
  - Preprocessor: `scripts/build_tile_pyramid.py`
  - Arterial Backbone: `desktop/public/geo/hyderabad-arterials.json` (13,316 features, 4.2 MB) containing all motorways, expressways, trunks, primaries, secondaries, and tertiaries across 1,500+ km².
  - Spatial Grid Tiles: 163 individual Zoom-13 GeoJSON tiles located in `desktop/public/geo/tiles/13/{x}_{y}.json` (average size: 199 KB).
  - Spatial Manifest: `desktop/public/geo/tiles/manifest.json` indexing tile bounding boxes for instant $O(1)$ intersection queries.
- **Runtime Tile Manager (`desktop/src/services/OfflineTileManager.ts`)**:
  - In-Memory LRU Cache (`MAX_CACHE_TILES = 60`): Stores decoded FeatureCollections; cache hits return in **0 ms**.
  - $O(1)$ Viewport Resolver: Calculates screen bounding box $[W, S, E, N]$ and fetches only the 2–4 tiles intersecting the screen when zoom $\ge 11.8$.
  - Idle Neighbor Prefetching: Asynchronously pre-caches 1-ring surrounding tiles in the background.
  - Startup Benchmark: Opens and becomes interactive in **< 350 milliseconds** (down from 101 seconds).
- **Offline Gazetteer Search**:
  - `desktop/src/services/OfflineGeocoder.ts` indexing 77 authentic locations (39 Telangana cities/towns + 38 Hyderabad landmarks).
  - Autocomplete search executes in **< 1 ms** completely offline.

### 3.3 Subsystem C: Hero 3D Earth WebGL Globe
- **Engine**: Three.js (`0.185.1`) integrated inside `desktop/src/components/GlobeHeroView.tsx`.
- **Features**:
  - Authentic offline country boundary projection rendered on a 3D sphere from `desktop/src/assets/world-countries.json`.
  - Permanent WebGL Lifecycle: Initialized once with `[]` dependency array; canvas, camera, and OrbitControls are never torn down.
  - Sacred Camera State: User manual drag/rotation locks camera; automatic rotation default is static with toggle.
  - Distance-Aware Incident Marker Scaling: In the WebGL render loop:
    $$\text{markerScale} = 0.28 + t_{\text{dist}} \times 0.72$$
    Zooming in shrinks pins to small, elegant dots (`● → • → ·`) preventing visual occlusion while keeping coordinates strictly fixed.
  - Raycasting: Clicking any incident pin triggers a smoothstep camera flight (`3t^2 - 2t^3`) and opens the floating tactical detail card.

### 3.4 Subsystem D: Distributed Peer-to-Peer Mesh Network Engine
- **Router (`backend/app/network/router.py`)**:
  - Dynamic routing table with real-time route discovery.
  - Hop count tracking (TTL 1 to 5) with loop prevention.
  - Round-trip latency measurement (ms) and link quality classification (`EXCELLENT` < 50ms, `GOOD` < 150ms, `MULTI_HOP` >= 150ms).
  - Loop suppression via `SeenPacketCache` with 5-minute bounded sliding window.
  - Automatic reverse-path caching for bidirectional messaging.
- **Mesh APIs (`backend/app/api/node.py`)**:
  - `GET /node/routes`: Returns active multi-hop routing table sorted by hop count.
  - `GET /node/topology`: Returns complete graph topology (local node, 1-hop direct neighbors, multi-hop relayed nodes, and interconnecting links).
- **Interactive SVG Topology Visualizer (`desktop/src/components/PeerTopologyModal.tsx`)**:
  - Center Node: Local Commander Node with pulsing blue aura.
  - Inner Orbit ($r=95$): Direct 1-hop peers with solid green links and live latency tags.
  - Outer Orbit ($r=185$): Multi-hop relayed nodes with dashed cyan links and hop count badges.
  - Dedicated Routing Table Tab displaying Destination ID, Next-Hop Relay, Total Hops, Latency, and Link Quality.

### 3.5 Subsystem E: On-Device AI RAG Decision Support System
- **Knowledge Base (`backend/app/rag/documents/`)**:
  17 authoritative emergency SOP documents covering:
  - Building Collapse & Urban Search and Rescue (`insarag_building_collapse_01.md`)
  - Cyclone Response & High Wind Protocols (`ndma_cyclone_sop_01.md`)
  - Earthquake Structural Safety & Post-Shock Response (`ndma_earthquake_sop_01.md`)
  - Emergency Communications & Mesh Protocols (`resqmesh_emergency_comms_01.md`)
  - Flood Evacuation, Swiftwater Rescue & Relief (`ndma_flood_sop_01.md`)
  - Hazardous Materials (HAZMAT) & Chemical Spill Response (`erg_hazmat_response_01.md`)
  - Mass Casualty Management & START Triage Protocol (`who_start_triage_01.md`)
  - Trauma First Aid & Severe Bleeding Control (`ifrc_trauma_first_aid_01.md`)
  - Incident Command System Guidelines (`mha_incident_response_system_01.md`)
  - Firefighting & Structural Fire Response (`usfa_structural_fire_01.md`)
  - Heat Wave Action Plans, Landslides, Disaster Logistics, Public Health, and Shelter.
- **RAG Dashboard Panel (`desktop/src/components/AiAdvisorPanel.tsx`)**:
  - Compact on-device AI advisor querying `POST /ai/query`.
  - Quick-query chips for high-frequency disaster scenarios.
  - Displays authoritative response, referenced SOP documents, and confidence score.

### 3.6 Subsystem F: Active Incident Duplicate / Merge AI
- **Engine (`desktop/src/services/IncidentMergeService.ts` & `desktop/src/components/IncidentMergeAiPanel.tsx`)**:
  - Continuous active scanning running on incident creation, sync, peer connection, and in background every 12 seconds with debounce.
  - Multi-Signal Scoring Function:
    $$S_{\text{total}} = 0.35 \cdot S_{\text{spatial}} + 0.30 \cdot S_{\text{text}} + 0.15 \cdot S_{\text{category}} + 0.10 \cdot S_{\text{severity}} + 0.10 \cdot S_{\text{temporal}}$$
  - Review Modal (`desktop/src/components/DuplicateIncidentsModal.tsx`): Side-by-side comparative inspection with `[ Merge Incidents ]`, `[ Keep Separate ]`, and `[ Dismiss Match ]` actions.

### 3.7 Subsystem G: Real Physical Location Engine & Fallback Suite
- **Location Service (`desktop/src/services/LocationService.ts`)**:
  - Multi-source priority: (1) Hardware GNSS/GPS, (2) Windows Location, (3) Browser Geolocation.
  - Accuracy threshold: Strict evaluation against $\pm 20\text{ m}$ target. Reports accurate, low-accuracy ($> 20\text{ m}$), or inaccurate ($> 1\text{ km}$).
  - Comprehensive Fallback Suite (Cases A–E):
    - Case A: High-accuracy GPS ($\le 20\text{ m}$) $\rightarrow$ green badge.
    - Case B: Low-accuracy GPS ($> 20\text{ m}$) $\rightarrow$ yellow warning, stores GPS + displays manual address fields.
    - Case C: GPS unavailable $\rightarrow$ red alert, stores `lat: null, lon: null`, manual address preserved.
    - Case D: Manual Map Selection $\rightarrow$ exact WGS84 coordinates labelled `MANUAL MAP SELECTION / NOT GNSS VERIFIED`.
    - Case E: Manual Typed Entry $\rightarrow$ structured address fields (`Address`, `Landmark`, `City`, `District`, `State`, `Pincode`).
- **Incident Photo Capture**:
  - Integrated native photo capture (`Capture Photo`) and file attachment (`Attach Photos`).
  - Supports JPG, JPEG, PNG, WEBP (< 10 MB) with thumbnail preview and individual removal (`✕`).

### 3.8 Subsystem H: Live Tactical Activity Feed
- **Component (`desktop/src/components/LiveTacticalActivityFeed.tsx`)**:
  - Positioned directly below the 3D Earth Globe.
  - Real-time event streaming connected via `TacticalEventBus.ts`.
  - Categories: `ALL`, `INCIDENTS`, `MESH`, `RESOURCES`, `SYSTEM`.
  - Scroll-lock detection: If scrolled up, a floating `↓ X new events` pill appears.
  - In-memory ring buffer capped at 500 events with deduplication.

---

## 4. Comprehensive Workspace Directory & File Tree

```
d:\Final_year_project\
│
├── PROJECT.md                               # Complete master technical specification (This File)
├── README.md                                # Project introduction and quick-start guide
├── build_knowledge_base.py                  # Build script compiling disaster SOP documents into RAG index
│
├── .agents\
│   └── rules\
│       └── project-rules.md                 # Lead Software Architect rules, output format & sequential versioning
│
├── backend\
│   ├── requirements.txt                     # Backend Python dependency specifications
│   ├── resqmesh.db                          # SQLite transactional database
│   │
│   ├── app\
│   │   ├── main.py                          # FastAPI app entry point, CORS, lifespan, and route registration
│   │   ├── config.py                        # Pydantic BaseSettings environment configuration
│   │   ├── database.py                      # SQLAlchemy engine and declarative session factory
│   │   ├── models.py                        # Database ORM models (Incident, Node, Resource, Route)
│   │   ├── schemas.py                       # Pydantic data schemas for request/response validation
│   │   │
│   │   ├── api\
│   │   │   ├── incidents.py                 # REST endpoints: CRUD incidents, triage priority, status updates
│   │   │   ├── node.py                      # REST endpoints: Peer registration, node status, /routes, /topology
│   │   │   ├── resources.py                 # REST endpoints: Resource requests, inventory, allocations
│   │   │   ├── sync.py                      # REST endpoints: P2P delta synchronization and packet ingestion
│   │   │   ├── ai.py                        # REST endpoints: Local RAG SOP query engine and recommendations
│   │   │   └── auth.py                      # REST endpoints: Role-based tactical access authentication
│   │   │
│   │   ├── network\
│   │   │   ├── router.py                    # Dynamic multi-hop router, latency tracking, loop suppression
│   │   │   ├── node.py                      # NodeManager managing active peer connections and heartbeats
│   │   │   ├── connection.py                # TCP socket connection handler and streaming client
│   │   │   └── packet.py                    # Binary and JSON mesh packet serialization / deserialization
│   │   │
│   │   └── rag\
│   │       ├── engine.py                    # Local RAG vector index retrieval and SOP query matching
│   │       └── documents\                   # 17 Authoritative disaster SOP markdown documents
│   │           ├── building_collapse\
│   │           ├── cyclones\
│   │           ├── earthquakes\
│   │           ├── emergency_comms\
│   │           ├── evacuation\
│   │           ├── fire\
│   │           ├── floods\
│   │           ├── hazmat\
│   │           ├── heat_waves\
│   │           ├── incident_command\
│   │           ├── landslides\
│   │           ├── logistics\
│   │           ├── mass_casualty\
│   │           ├── medical\
│   │           ├── public_health\
│   │           ├── search_and_rescue\
│   │           └── shelter_relief\
│   │
│   ├── dist\
│   │   └── resqmesh-server\                 # Standalone compiled PyInstaller backend executable
│   │       └── resqmesh-server.exe
│   │
│   └── tests\                               # Pytest automated test suite (100% pass)
│       ├── test_api.py                      # REST API endpoint tests
│       ├── test_router.py                   # Multi-hop routing and loop suppression tests
│       ├── test_sync.py                     # Delta synchronization tests
│       └── test_triage.py                   # Incident triage priority scoring tests
│
├── desktop\
│   ├── package.json                         # Desktop frontend dependencies, scripts & electron-builder config
│   ├── package-lock.json                    # Exact pinned dependency resolution tree
│   ├── vite.config.ts                       # Vite build configuration, React plugin & proxy rules
│   ├── tsconfig.json                        # TypeScript compiler options
│   │
│   ├── electron\
│   │   ├── main.js                          # Electron main process, window creation, IPC handlers & server spawn
│   │   └── preload.js                       # Secure IPC preload script exposing window.resqmeshAPI
│   │
│   ├── public\
│   │   └── geo\
│   │       ├── hyderabad-arterials.json     # 13,316 fast OpenStreetMap primary/secondary road ways (4.2 MB)
│   │       ├── hyderabad-roads.json         # 175,803 complete OpenStreetMap metropolitan road network (35.88 MB)
│   │       ├── hyderabad-water.json         # 635 authentic water bodies and lakes (660 KB)
│   │       └── tiles\
│   │           ├── manifest.json            # Spatial manifest indexing 163 Zoom-13 tile bounding boxes
│   │           └── 13\                      # 163 Preprocessed Zoom-13 road tiles (~199 KB each)
│   │               ├── 5873_3686.json
│   │               ├── 5881_3695.json
│   │               └── ...
│   │
│   ├── src\
│   │   ├── App.tsx                          # Master dashboard shell, navigation views & periodic telemetry
│   │   ├── main.tsx                         # React 18 DOM mount point
│   │   ├── index.html                       # HTML5 entry template
│   │   │
│   │   ├── assets\
│   │   │   ├── india-states.json            # India sovereign state boundaries
│   │   │   ├── world-countries.json         # World country polygons for 3D Earth Globe
│   │   │   └── geo\
│   │   │       ├── telangana-boundary.json  # Authentic Survey of India Telangana state outline (30 KB)
│   │   │       ├── telangana-districts.json # Authentic Survey of India 10 district polygons (66 KB)
│   │   │       ├── telangana-highways.json  # National highways: NH 44, NH 65, NH 163, NH 765, ORR (4.5 KB)
│   │   │       ├── telangana-roads.json     # State highways and arterial corridors (3.6 KB)
│   │   │       ├── telangana-cities.json    # 39 Authoritative Telangana cities and towns (10 KB)
│   │   │       ├── hyderabad-primary-roads.json # Bundled 13,316 arterial roads for instant startup (1.08 MB)
│   │   │       ├── hyderabad-water.json     # 635 Lakes and water features (660 KB)
│   │   │       └── hyderabad-places.json    # 38 Strategic neighborhood landmarks (5.4 KB)
│   │   │
│   │   ├── components\
│   │   │   ├── GlobeHeroView.tsx            # Three.js 3D Earth WebGL Globe with raycasting & zoom scaling
│   │   │   ├── LocationPickerModal.tsx      # MapLibre GL offline map picker with on-demand tile streaming
│   │   │   ├── TacticalGisMap.tsx           # Full-screen tactical GIS operational map
│   │   │   ├── LiveTacticalActivityFeed.tsx # Real-time chronological event stream with scroll lock
│   │   │   ├── IncidentMergeAiPanel.tsx     # Dashboard AI panel actively detecting duplicate incidents
│   │   │   ├── DuplicateIncidentsModal.tsx  # Side-by-side comparative inspection & merge review modal
│   │   │   ├── CreateIncidentModal.tsx      # Incident reporting modal with location fallback & photo capture
│   │   │   ├── IncidentDetailModal.tsx      # Detailed incident inspection, triage score, and squad dispatch
│   │   │   ├── PeerTopologyModal.tsx        # Interactive SVG orbital mesh topology & routing table visualizer
│   │   │   ├── AiAdvisorPanel.tsx           # On-device AI RAG advisor with quick disaster chips
│   │   │   ├── RequestResourceModal.tsx     # Logistics resource request modal with squad allocation
│   │   │   ├── ResourceManagementView.tsx   # Master logistics inventory and allocation manager
│   │   │   └── SquadsView.tsx               # Tactical squad readiness, member assignments, and field status
│   │   │
│   │   ├── services\
│   │   │   ├── OfflineTileManager.ts        # In-memory LRU cache, on-demand tile streaming, and prefetching
│   │   │   ├── OfflineGeocoder.ts           # 100% offline reverse geocoder and 77-entry local gazetteer
│   │   │   ├── LocationService.ts           # Real hardware GNSS/GPS, Windows Location & browser position engine
│   │   │   ├── TacticalEventBus.ts          # Central operational event bus with ring buffer cap (500)
│   │   │   ├── IncidentMergeService.ts      # Multi-signal AI incident duplicate correlation engine
│   │   │   └── MeshNodeService.ts           # Client-side API abstraction for mesh networking and peer status
│   │   │
│   │   └── styles\
│   │       └── designTokens.ts              # Master design system tokens (colors, typography, radii, shadows)
│   │
│   └── dist\                                # Compiled production frontend assets
│
├── mobile\                                  # Handheld mobile field node app (React Native)
│   ├── package.json
│   ├── App.tsx
│   └── src\
│
├── scripts\
│   ├── build_tile_pyramid.py                # Preprocessor partitioning 175,803 roads into Zoom-13 spatial tiles
│   ├── build_gis_assets.py                  # Preprocessor extracting Survey of India GIS vector layers
│   └── configure_firewall.bat               # Windows firewall rules for UDP/TCP mesh ports
│
├── docs\
│   ├── RELEASES.md                          # Sequential release log and installation guide (v1.0.0 – v1.0.26)
│   ├── DEPLOYMENT.md                        # Production deployment architecture
│   ├── IMPLEMENTATION_PLAN.md               # Historical roadmap and phase milestones
│   └── VIVA_DEMONSTRATION_RUNBOOK.md        # Academic demonstration script and verification steps
│
└── release\                                 # Production Windows NSIS Setup Installers
    ├── ResQMeshAI-Setup-v1.0.0.exe
    ├── ...
    ├── ResQMeshAI-Setup-v1.0.24.exe
    ├── ResQMeshAI-Setup-v1.0.25.exe
    └── ResQMeshAI-Setup-v1.0.26.exe         # Current Recommended Production Installer (145.49 MB)
```

---

## 5. RESTful API & Mesh Packet Specifications

The Python backend server operates on `http://127.0.0.1:8000` (or local mesh node IP) and exposes the following endpoints:

### 5.1 Incident Management APIs
| Method | Endpoint | Description | Request Body / Parameters | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/incidents` | List all incidents with optional severity, status, or search filters. | `?status=&severity=&category=` | `Incident[]` |
| `POST` | `/incidents` | Broadcast a new emergency incident report across the mesh. | `IncidentCreateSchema` | `Incident` |
| `GET` | `/incidents/{id}` | Retrieve complete details, triage priority, and audit log for an incident. | Path `id: str` | `IncidentDetail` |
| `PATCH` | `/incidents/{id}` | Update incident status (`OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`). | `IncidentUpdateSchema` | `Incident` |
| `POST` | `/incidents/{id}/photos` | Upload and attach photo evidence to an incident report. | Multipart Form `file: UploadFile` | `PhotoAttachment` |
| `POST` | `/incidents/merge` | Merge two correlated duplicate incidents into a single master incident. | `{ primary_id: str, duplicate_id: str, reason: str }` | `IncidentMergeResult` |

### 5.2 Mesh Networking & Node Topology APIs
| Method | Endpoint | Description | Request Body / Parameters | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/node/status` | Current node telemetry, node ID, tactical role, and battery status. | None | `NodeStatus` |
| `GET` | `/node/peers` | List directly connected 1-hop physical peers discovered on the mesh. | None | `PeerNode[]` |
| `POST` | `/node/peers/connect` | Manually establish a direct TCP socket peering connection to an IP/port. | `{ ip: str, port: int }` | `ConnectionResult` |
| `GET` | `/node/routes` | Active multi-hop routing table sorted by hop count with latency and quality. | None | `MeshRoute[]` |
| `GET` | `/node/topology` | Full network graph topology (local node, 1-hop neighbors, multi-hop relays).| None | `NetworkTopology` |

### 5.3 On-Device AI RAG APIs
| Method | Endpoint | Description | Request Body / Parameters | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/ai/query` | Query the local disaster SOP knowledge base without internet. | `{ query: str, context: Optional[str] }` | `{ answer: str, sources: str[], confidence: float }` |
| `POST` | `/ai/triage` | Calculate automated START triage priority score for an incident. | `{ symptoms: str[], vitals: dict }` | `{ triage_level: str, priority_score: int }` |

### 5.4 Resource Logistics & Squad Allocation APIs
| Method | Endpoint | Description | Request Body / Parameters | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/resources` | Master inventory of all available emergency logistics resources. | None | `ResourceItem[]` |
| `POST` | `/resources/request` | Submit a tactical logistics request for an active incident. | `ResourceRequestSchema` | `ResourceRequest` |
| `POST` | `/resources/allocate` | Allocate equipment or medical supplies to an operational squad. | `ResourceAllocationSchema` | `AllocationResult` |
| `GET` | `/squads` | Operational status, readiness, and active assignments of rescue squads. | None | `TacticalSquad[]` |

---

## 6. Complete Release Progression History

ResQMesh AI strictly follows the sequential versioning convention defined in `.agents/rules/project-rules.md`:

| Version | Release Installer Artifact | Release Date | Summary of Accomplishments |
| :--- | :--- | :--- | :--- |
| **v1.0.27** | `ResQMeshAI-Setup-v1.0.27.exe` | 2026-08-29 | **Deployment-Ready Production Release (Pristine Zero-Incident Baseline & Clean Schema)**: Purged all hardcoded mock incidents (`DEMO_GLOBAL_INCIDENTS`), cleared all SQLite operational tables (0 rows across incidents, reports, resources, event logs), removed auto-seeding in backend API, and added clean empty states with system-only startup event. |
| **v1.0.26** | `ResQMeshAI-Setup-v1.0.26.exe` | 2026-08-29 | **Critical Map Picker Performance Optimization (< 350ms Startup)**: Eliminated the 101-second initialization freeze by partitioning 175,803 roads into 163 Zoom-13 spatial grid tiles and implementing `OfflineTileManager` with LRU caching, on-demand viewport streaming, persistent MapLibre singleton, and debounced geocoding. |
| **v1.0.25** | `ResQMeshAI-Setup-v1.0.25.exe` | 2026-08-29 | **Authentic Offline Geographic Map Engine (MapLibre GL)**: Purged all synthetic circular blob polygons; integrated authentic Survey of India district and state boundaries for Telangana, 635 water bodies, national highways, and 77-entry local gazetteer search. |
| **v1.0.24** | `ResQMeshAI-Setup-v1.0.24.exe` | 2026-08-29 | **Multi-Hop Mesh Peer Routing Optimization & Interactive Relay Path Visualizer**: Implemented dynamic multi-hop routing table, latency measurement, link quality scoring, `/node/routes`, `/node/topology`, and interactive SVG orbital visualizer. |
| **v1.0.23** | `ResQMeshAI-Setup-v1.0.23.exe` | 2026-08-29 | **Globe Marker Scaling, Active Incident Merge AI Panel & Always-Available Manual Location**: Added distance-aware WebGL marker scaling on 3D globe, continuous background Incident Merge AI panel, interactive map pin picker, and dual location preservation. |
| **v1.0.22** | `ResQMeshAI-Setup-v1.0.22.exe` | 2026-08-29 | **Incident Reporting Location Fallback Suite, Native Camera & Photo Capture, Live Tactical Activity Feed**: Added real-time command-center event stream below 3D globe with scroll-lock detection, 5-case location fallback suite, and native photo capture. |
| **v1.0.21** | `ResQMeshAI-Setup-v1.0.21.exe` | 2026-08-29 | **Real Physical Device Location Engine, True Accuracy Reporting (±20m Threshold) & On-Device AI Advisor**: Integrated real GNSS/Windows/browser location priority, true accuracy reporting, offline GNSS fallback, and compact On-Device AI Advisor panel. |
| **v1.0.20** | `ResQMeshAI-Setup-v1.0.20.exe` | 2026-08-29 | **Permanent 3D Earth WebGL Lifecycle, Sacred Camera State & Zero-Reset Orbit Controls Fix**: Bound Three.js initialization to empty dependency array; eliminated re-render churn during polling and locked camera on user drag. |
| **v1.0.19** | `ResQMeshAI-Setup-v1.0.19.exe` | 2026-08-29 | **Complete UI/UX Revamp, Hero 3D Earth Globe & Glassmorphic Design System**: Modernized interface to 20px rounded SaaS mission control, WebGL 3D Earth Globe with Raycasting, master sidebar, minimal header, and global demo scenario. |
| **v1.0.18** | `ResQMeshAI-Setup-v1.0.18.exe` | 2026-08-29 | **Memory Bottleneck Fix in Electron Build Pipeline**: Moved large GIS assets to `public/geo/` and streamed directly via Electron IPC `load-geojson` to resolve 4GB Node.js AST memory crash. |
| **v1.0.0 – v1.0.17** | `ResQMeshAI-Setup-v1.0.X.exe` | Historical | Initial P2P mesh prototypes, FastAPI daemon, SQLite models, basic triage algorithms, and early packaging milestones. |

---

## 7. Build, Packaging & Verification Runbook

### 7.1 Preprocessing Offline Geographic Assets
To regenerate the Zoom-13 spatial road tile pyramid from raw OpenStreetMap data:
```bash
# Run from repository root
python scripts/build_tile_pyramid.py
```
*Output*: Generates `hyderabad-arterials.json`, 163 spatial tiles in `desktop/public/geo/tiles/13/*.json`, and `desktop/public/geo/tiles/manifest.json`.

### 7.2 Running Automated Backend Tests
To verify all routing, API endpoints, synchronization, and triage algorithms:
```bash
python -m pytest backend/tests/test_router.py backend/tests/test_api.py backend/tests/test_sync.py backend/tests/test_triage.py
```
*Expected Result*: 100% passed (110+ green tests).

### 7.3 Compiling the Python Backend Daemon (PyInstaller)
When backend code is modified, recompile the standalone binary:
```bash
cd backend
pyinstaller --clean --noconfirm resqmesh-server.spec
cd ..
```
*Output*: Standalone executable generated at `backend/dist/resqmesh-server/resqmesh-server.exe`.

### 7.4 Compiling the Desktop Frontend
To validate TypeScript types and compile the optimized Vite production bundle:
```bash
cd desktop
npm run build
cd ..
```
*Output*: Chunks generated in `desktop/dist/`.

### 7.5 Building the Production Windows Installer
To package the standalone installer with electron-builder:
```bash
cd desktop
npm run dist
cd ..
```
*Output*: Standalone NSIS installer generated at `release/ResQMeshAI-Setup-v1.0.XX.exe`.

---

## 8. Hardware & Operating Environment Compliance

- **Operating Systems Supported**: Windows 10 (64-bit), Windows 11 (64-bit), Windows Server 2019/2022.
- **Hardware Minimums**: Intel Core i3 (4th Gen+) / AMD Ryzen 3, 4GB RAM, 2GB available storage, DirectX 11 / WebGL compatible GPU.
- **Network Compatibility**: Standard 802.11 b/g/n/ac Wi-Fi, Ethernet 10/100/1000 Mbps, Ad-Hoc Wi-Fi Direct, Bluetooth 4.2+ (BLE).
- **Offline Security**: Strict Zero-Internet Isolation compliance; runs completely inside air-gapped environments without security degradation.
