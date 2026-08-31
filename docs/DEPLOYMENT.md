# ResQMesh AI: Complete Windows Deployment & Multi-Laptop Guide

ResQMesh AI is a standalone, installable Windows application designed for complete offline disaster emergency coordination across two or more laptops.

---

## 1. Single-Click Windows Production Installer

The application is bundled into a self-contained Windows NSIS Setup Wizard:
**Location**: `d:\Final_year_project\release\ResQMeshAI-Setup-v1.0.1.exe` (Size: ~131 MB)

### Included Components in Installer:
1. **Electron Chromium Desktop Shell**: Interactive emergency tactical dashboard, live maps, AI triage advisor, and mesh network monitor.
2. **Native Background Engine (`resqmesh-server.exe`)**: Compiled FastAPI/Uvicorn daemon bundled inside `resources/resqmesh-server/`. Runs locally on `127.0.0.1:8000` (auto-managed child process with clean process-tree teardown).
3. **P2P Discovery Engine**: Dual-mode mDNS Zeroconf + UDP broadcast beacons (`0.0.0.0:52525`).
4. **Offline SQLite Engine**: Stored in `%APPDATA%\ResQMeshAI\data\` for delay-tolerant store-and-forward outbox sync.
5. **On-Device AI Engine**: Multi-factor spatial/temporal/text incident clustering and offline RAG SOP retrieval.
6. **Windows Start Menu & Desktop Shortcuts**: Created automatically by the installer.
7. **Built-in Uninstaller**: Automatically registers in Windows **Add or Remove Programs** and creates `Uninstall ResQMesh AI.exe`.

---

## 2. Multi-Laptop Field Deployment Setup

To demonstrate or evaluate multi-laptop mesh networking:

### Step 1: Copy Installer
Copy `ResQMeshAI-Setup-v1.0.1.exe` onto a USB flash drive.

### Step 2: Install on Laptop 1 (Command Center)
1. Run `ResQMeshAI-Setup-v1.0.1.exe`.
2. Follow the NSIS setup wizard and complete the installation.
3. Launch **ResQMesh AI** from Desktop or Start Menu.
4. On first launch, the **Node Onboarding Modal** will appear:
   - Name: `Laptop-HQ`
   - Role: Select **🎯 Commander**
   - Click **Join Emergency Mesh**.

### Step 3: Install on Laptop 2 (Field Responder)
1. Run the identical `ResQMeshAI-Setup-v1.0.1.exe` on the second laptop.
2. Launch **ResQMesh AI**.
3. In the Onboarding Modal:
   - Name: `Laptop-Squad-Alpha`
   - Role: Select **🚒 Field Responder**
   - Click **Join Emergency Mesh**.

### Step 4: Connect Laptops to Offline Network
- Connect both laptops to the same local Wi-Fi router, phone mobile hotspot, or Ethernet switch.
- **ZERO internet connection is required.** Both laptops communicate 100% peer-to-peer over the local subnet.
- *Firewall Note*: If Windows Defender prompts to allow network access, click **Allow access**. Alternatively, run `scripts\configure_firewall.bat` as Administrator.

### Step 5: Verify P2P Mesh & Delta Synchronization
1. Within 5–10 seconds, the top status badge on both laptops will update from `Searching for Peers...` to:
   **`● 1 Peers Connected [LAN]`**.
2. Click the badge to open the **Peer Mesh Topology Modal** and inspect the authenticated link details (IP address, port, node role).
3. On Laptop 2, click **🚨 Broadcast Incident** and submit a test report (e.g. "Transformer Fire near Station").
4. Within seconds, Laptop 1 will receive the report over the mesh, auto-cluster it on the map, and update its sync state to `All Outbox ACKed`.

---

## 3. How to Cleanly Uninstall

The installer includes a built-in uninstaller:
1. Open Windows **Settings** > **Installed Apps** (or Control Panel > Programs and Features).
2. Locate **ResQMesh AI**.
3. Click **Uninstall**.
4. The uninstaller removes all application files, shortcuts, and Electron dependencies.
