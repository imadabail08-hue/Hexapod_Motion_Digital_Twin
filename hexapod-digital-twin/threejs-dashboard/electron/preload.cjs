const { contextBridge, ipcRenderer } = require('electron');

// Expose safe desktop system APIs to renderer
contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  isElectron: true,
  appVersion: '1.0.0',
});

