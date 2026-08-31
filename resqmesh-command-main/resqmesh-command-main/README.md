# ResQMesh Command

Goal

Build a modern, high-tech, offline-first Emergency Disaster Response Command Center dashboard called "ResQMesh AI Command Center". It connects to a local FastAPI backend running at `http://localhost:8000`.

---

🎨 Design & Aesthetic Requirements

- Theme: Dark Tactical / Emergency Operations Center (EOC) aesthetic.

- Color Palette:

- Background: Deep Slate `#020617` / `#0f172a`

- Cards & Panels: `#1e293b` with `#334155` subtle borders

- Primary / Highlights: Electric Cyan `#38bdf8` & Emergency Orange `#f97316`

- Severity Badges:

- `critical`: Crimson Red `#ef4444` (pulsing glow)

- `high`: Amber Orange `#f97316`

- `medium`: Warning Yellow `#f59e0b`

- `low`: Emerald Green `#10b981`

- Typography: Clean, monospace-friendly sans-serif (e.g. Inter / JetBrains Mono).

- Layout: Grid layout with a top status bar, interactive map pane on the left, and multi-tab operational panels on the right.

---

🧭 Dashboard Layout & Components

1. Top Header Bar:

- Logo + Title: "ResQMesh AI Command Center"

- Live System Status Badge: `● Mesh Status: ACTIVE (Offline P2P Network)`

- Clock (UTC + Local)

- Quick Filter toggles (All, Critical Only, Fire, Flood, Medical, Structural)

- "New Incident" button opening a modal form.

2. Main Screen Grid (2-Column Layout):

- Left Column (60% width):

- Interactive Leaflet / Map View:

- Map centered at coordinates (e.g. `[12.9716, 77.5946]`) with dark tile theme.

- Custom glowing markers for each active `Operational Incident` colored by severity.

- Marker click opens popup with Title, Category, Report Count, Severity, and a "View Incident Details" button.

- Incident Table / Grid List (below map):

- Sortable table of active incidents with title, category, severity badge, linked reports count, status dropdown (`open`, `in_progress`, `resolved`, `closed`), and timestamp.

- Right Column (40% width - Tabbed or Stacked Panels):

- Panel 1: AI Duplicate Incident Correlation Review (`IncidentReviewCard`):

- Displays incoming field reports that AI detected as probable duplicates (confidence score >= 45%).

- Shows similarity score badge (e.g. `82% Match`), matching master incident title, and text excerpts.

- Action buttons: `[✓ Approve Merge]` (links report) and `[✕ Spawn As New Incident]`.

- Panel 2: Emergency SOP Recommendations (RAG Guidance):

- Displays 3 tactical action steps retrieved from official Standard Operating Procedures based on selected incident category.

- Panel 3: Resource & Team Dispatch (`ResourceDispatchPanel`):

- List of requested resources (e.g., "5x Medical First Aid Kits", "2x Inflatable Boats").

- Status badge (`pending`, `dispatched`, `fulfilled`).

- `[Dispatch Team]` button with visual feedback.

- Panel 4: Mesh Tactical Chat:

- Real-time chat feed between field responders and command center.

- Input box to broadcast messages over the mesh network.

---

🔌 API Integration & Data Contracts

Base URL: `http://localhost:8000`

1. System Health

- Endpoint: `GET /status` or `GET /health`

- Response:

```json

{

"status": "online",

"service": "ResQMesh AI Backend",

"version": "1.0.0",

"mode": "offline-mesh-operational"

}

2. Operational Incidents

List All Incidents: GET /incidents/

Optional Query Params: status, severity, category

Response: Array of Incident objects:

json

[

  {

"incident_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",

"title": "Structural Fire - Station Area",

"status": "open",

"severity": "critical",

"category": "fire",

"latitude": 12.9716,

"longitude": 77.5946,

"summary": "Heavy smoke and transformer fire near main station area",

"created_at": "2026-08-20T11:00:00Z",

"updated_at": "2026-08-20T11:05:00Z",

"reports": [],

"messages": [],

"resources": []

  }

]

Create New Incident: POST /incidents/

Request Body:

json

{

"title": "Flash Flood Inundation",

"category": "flood",

"severity": "high",

"latitude": 12.9800,

"longitude": 77.6000,

"summary": "Water levels rising near West Bridge residential sector",

"status": "open"

}

Get Incident By ID: GET /incidents/{incident_id}

Update Incident Status/Details: PUT /incidents/{incident_id}

Request Body:

json

{

"status": "in_progress",

"severity": "critical",

"summary": "Updated response summary"

}

3. Field Reports & AI Correlation

List All Reports: GET /reports/

Optional Query Params: incident_id, category

Submit New Report: POST /reports/

Request Body:

json

{

"device_id": "FIELD-NODE-01",

"user_id": "responder-alpha",

"category": "fire",

"description": "Transformer explosion near north bridge with 2 trapped casualties",

"latitude": 12.9718,

"longitude": 77.5948,

"incident_id": null

}

4. Tactical Mesh Chat Messages

List Messages: GET /messages/

Optional Query Param: incident_id

Send Message: POST /messages/

Request Body:

json

{

"sender_device_id": "CMD-DESKTOP-01",

"sender_user_id": "commander-1",

"text": "Rescue Team Bravo dispatched with 2 inflatable boats.",

"incident_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"

} use tokens efficiently and write code smartly, only whats needed no more no less

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/a49e86be-a114-417d-b249-69792665b42b).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
