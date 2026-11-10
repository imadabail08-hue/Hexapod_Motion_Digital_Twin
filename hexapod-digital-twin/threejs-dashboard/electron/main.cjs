const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow = null;
let bridgeProcess = null;

function startSerialBridge() {
  const rootDir = path.resolve(__dirname, '..', '..', '..');
  const venvPython = path.join(rootDir, '.venv', 'Scripts', 'python.exe');
  const scriptPath = path.join(rootDir, 'serial_bridge.py');

  const pyExecutable = fs.existsSync(venvPython) ? venvPython : 'python';

  if (fs.existsSync(scriptPath)) {
    console.log(`[MAIN] Launching serial bridge with ${pyExecutable}...`);
    try {
      bridgeProcess = spawn(pyExecutable, ['-u', scriptPath], {
        cwd: rootDir,
        stdio: ['ignore', 'pipe', 'pipe'],
      });

      bridgeProcess.stdout.on('data', (data) => {
        const text = data.toString().trim();
        if (text) console.log(`[BRIDGE] ${text}`);
      });

      bridgeProcess.stderr.on('data', (data) => {
        console.error(`[BRIDGE ERR] ${data.toString().trim()}`);
      });

      bridgeProcess.on('exit', (code) => {
        console.log(`[BRIDGE] Process exited with code ${code}`);
      });
    } catch (err) {
      console.warn(`[MAIN] Could not auto-launch serial bridge: ${err}`);
    }
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'HEXAPOD MOTION DIGITAL TWIN — HEX-01 Industrial HMI',
    backgroundColor: '#080d16',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
    },
  });

  mainWindow.removeMenu();

  const isDev = process.env.NODE_ENV === 'development' || process.env.VITE_DEV === 'true';

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    const indexPath = path.join(__dirname, '..', 'dist', 'index.html');
    console.log('[MAIN] Loading bundled UI from:', indexPath);
    mainWindow.loadFile(indexPath);
  }

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('[MAIN] Page load failed:', errorCode, errorDescription);
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  startSerialBridge();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (bridgeProcess) {
    try {
      bridgeProcess.kill();
    } catch (e) {}
    bridgeProcess = null;
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

