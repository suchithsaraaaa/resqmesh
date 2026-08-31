const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('resqmeshAPI', {
  isElectron: true,
  platform: process.platform,
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getNodePort: () => ipcRenderer.invoke('get-node-port'),
  openExternalUrl: (url) => ipcRenderer.invoke('open-external-url', url),
  loadGeoJson: (relPath) => ipcRenderer.invoke('load-geojson', relPath),
});
