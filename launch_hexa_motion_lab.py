"""
launch_hexa_motion_lab.py

High-Speed Local Server for HEXA MOTION LAB Digital Twin.
Serves the production bundle and automatically opens the browser at http://localhost:5173
"""

import http.server
import socketserver
import webbrowser
import os
import threading
import time

PORT = 5173
DIRECTORY = os.path.join(os.path.dirname(__file__), "hexapod-digital-twin", "threejs-dashboard", "dist")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # Suppress noisy HTTP logs
        pass

def open_browser():
    time.sleep(0.8)
    url = f"http://localhost:{PORT}"
    print(f"\n=======================================================")
    print(f"   HEXA MOTION LAB - DIGITAL TWIN PROFESSIONNEL       ")
    print(f"=======================================================")
    print(f"   Ouverture automatique du navigateur sur :")
    print(f"   >>> {url} <<<")
    print(f"=======================================================\n")
    webbrowser.open(url)

if __name__ == "__main__":
    if not os.path.exists(DIRECTORY):
        print(f"Erreur: Dossier {DIRECTORY} introuvable.")
        exit(1)

    threading.Thread(target=open_browser, daemon=True).start()

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serveur local actif sur le port {PORT} (Ctrl+C pour quitter)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nArret du serveur.")
