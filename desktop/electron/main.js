const { app, BrowserWindow, ipcMain, shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn, execSync } = require('child_process');

let mainWindow = null;
let serverProcess = null;
const NODE_PORT = parseInt(process.env.RESQMESH_PORT || '8000', 10);

// Ensure single instance lock
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

function getAppDataDir() {
  const base = process.env.LOCALAPPDATA || process.env.APPDATA || path.join(process.env.USERPROFILE || '', '.resqmesh');
  const dir = path.join(base, 'ResQMesh AI', 'logs');
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  return dir;
}

function getDataDir() {
  const base = process.env.LOCALAPPDATA || process.env.APPDATA || path.join(process.env.USERPROFILE || '', '.resqmesh');
  const dir = path.join(base, 'ResQMesh AI', 'data');
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  return dir;
}

function checkPortInUse(port) {
  return new Promise((resolve) => {
    const tester = http.createServer()
      .once('error', (err) => {
        if (err.code === 'EADDRINUSE') resolve(true);
        else resolve(false);
      })
      .once('listening', () => {
        tester.once('close', () => resolve(false)).close();
      })
      .listen(port, '127.0.0.1');
  });
}

function checkResQMeshHealthy(port) {
  return new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${port}/node/status`, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(1500, () => {
      req.destroy();
      resolve(false);
    });
  });
}

function findServerBinary() {
  const candidates = [
    // 1. Packaged Electron resources directory
    path.join(process.resourcesPath || '', 'resqmesh-server', 'resqmesh-server.exe'),
    path.join(process.resourcesPath || '', 'server', 'resqmesh-server.exe'),
    path.join(process.resourcesPath || '', 'resqmesh-server.exe'),
    // 2. Relative distribution package
    path.join(__dirname, '..', '..', 'dist', 'ResQMesh-AI-Windows-x64', 'server', 'resqmesh-server.exe'),
    // 3. Backend compiled dist directory
    path.join(__dirname, '..', '..', 'backend', 'dist', 'resqmesh-server', 'resqmesh-server.exe'),
  ];

  for (const p of candidates) {
    if (fs.existsSync(p)) {
      return p;
    }
  }
  return null;
}

async function startBackendServer() {
  const portBusy = await checkPortInUse(NODE_PORT);
  if (portBusy) {
    const isHealthyResQMesh = await checkResQMeshHealthy(NODE_PORT);
    if (isHealthyResQMesh) {
      console.log(`[ResQMesh] Active ResQMesh engine already running on port ${NODE_PORT}. Reusing instance.`);
      return;
    }
    dialog.showErrorBox(
      'ResQMesh AI — Port Conflict Detected',
      `ResQMesh AI could not bind to port ${NODE_PORT} because another application is using it.\n\nPlease close the conflicting application or set the RESQMESH_PORT environment variable before restarting.`
    );
    return;
  }

  const binaryPath = findServerBinary();
  const logDir = getAppDataDir();
  const dataDir = getDataDir();
  const logFile = fs.createWriteStream(path.join(logDir, 'server.log'), { flags: 'a' });

  console.log(`[ResQMesh] Resolving backend engine binary...`);

  const spawnOpts = {
    stdio: ['ignore', 'pipe', 'pipe'],
    detached: false,
    cwd: dataDir,
    env: {
      ...process.env,
      RESQMESH_PORT: String(NODE_PORT),
    },
  };

  if (binaryPath) {
    console.log(`[ResQMesh] Launching standalone engine: ${binaryPath} (cwd: ${dataDir})`);
    serverProcess = spawn(binaryPath, ['--port', String(NODE_PORT)], spawnOpts);
  } else {
    console.log(`[ResQMesh] Binary not found. Launching via Python server_entrypoint...`);
    const pyScript = path.join(__dirname, '..', '..', 'backend', 'server_entrypoint.py');
    serverProcess = spawn('python', [pyScript, '--port', String(NODE_PORT)], spawnOpts);
  }

  if (serverProcess) {
    serverProcess.stdout.pipe(logFile);
    serverProcess.stderr.pipe(logFile);

    serverProcess.on('error', (err) => {
      console.error(`[ResQMesh] Failed to start backend engine:`, err);
      dialog.showErrorBox(
        'ResQMesh AI — Backend Launch Failure',
        `Failed to start ResQMesh engine daemon:\n${err.message}\n\nPlease check logs at:\n${path.join(logDir, 'server.log')}`
      );
    });

    serverProcess.on('exit', (code) => {
      console.log(`[ResQMesh] Backend engine exited with code: ${code}`);
    });
  }
}

function stopBackendServer() {
  if (serverProcess && serverProcess.pid) {
    console.log(`[ResQMesh] Stopping backend engine PID: ${serverProcess.pid}`);
    try {
      if (process.platform === 'win32') {
        execSync(`taskkill /pid ${serverProcess.pid} /T /F`);
      } else {
        serverProcess.kill('SIGTERM');
      }
    } catch (e) {
      // Process already terminated
    }
    serverProcess = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1366,
    height: 850,
    minWidth: 1080,
    minHeight: 680,
    show: true,
    backgroundColor: '#020617',
    title: 'ResQMesh AI — Autonomous Emergency Coordination Node',
    icon: path.join(__dirname, '..', 'assets', 'icon.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
      webSecurity: false,
    },
  });

  // Remove standard menu bar for sleek tactical look
  mainWindow.setMenuBarVisibility(false);

  // Load production bundle
  const distIndex = path.join(__dirname, '..', 'dist', 'index.html');
  if (fs.existsSync(distIndex)) {
    mainWindow.loadFile(distIndex);
  } else if (process.env.FRONTEND_PORT) {
    mainWindow.loadURL(`http://localhost:${process.env.FRONTEND_PORT}`);
  } else {
    mainWindow.loadFile(distIndex).catch((err) => {
      console.error('[ResQMesh] Failed to load index.html:', err);
    });
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC Handlers
ipcMain.handle('get-app-version', () => app.getVersion());
ipcMain.handle('get-node-port', () => NODE_PORT);
ipcMain.handle('open-external-url', (event, url) => shell.openExternal(url));
ipcMain.handle('load-geojson', async (event, relPath) => {
  const possiblePaths = [
    path.join(__dirname, '..', 'dist', relPath),
    path.join(__dirname, '..', 'public', relPath),
    path.join(process.resourcesPath || '', 'app', 'dist', relPath),
    path.join(process.resourcesPath || '', 'app', 'public', relPath),
    path.join(process.resourcesPath || '', relPath),
  ];
  for (const p of possiblePaths) {
    if (fs.existsSync(p)) {
      try {
        const content = await fs.promises.readFile(p, 'utf-8');
        return JSON.parse(content);
      } catch (err) {
        console.error(`[ResQMesh] Error reading geojson at ${p}:`, err);
      }
    }
  }
  return null;
});

app.whenReady().then(() => {
  // 1. Create and show window INSTANTLY (under 1 second)
  createWindow();
  // 2. Concurrently boot the backend daemon in the background
  startBackendServer();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopBackendServer();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  stopBackendServer();
});
