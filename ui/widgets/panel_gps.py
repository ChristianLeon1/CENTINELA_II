#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2025 CREADOR: Christian Yael Ramírez León

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget

# --- RESOLUCIÓN DE RUTAS TÁCTICAS ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class PanelGPS(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Layout Principal (Ocupará el 100% del ancho del contenedor)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Contenedor del Mapa
        self.gps_frame = QFrame()
        self.gps_frame.setProperty("isPanel", True)

        frame_layout = QVBoxLayout(self.gps_frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)

        self.gps_w = QWebEngineView()
        self.gps_w.setStyleSheet("background-color: #101829;")
        frame_layout.addWidget(self.gps_w)

        main_layout.addWidget(self.gps_frame)

        # Inicializar el motor de mapas local
        self._inicializar_mapa_web()

    def _inicializar_mapa_web(self):
        """Inyecta el motor del mapa Leaflet con un HUD simplificado en la esquina inferior derecha"""
        ruta_mapas = str(BASE_DIR / "mapas_satelite").replace("\\", "/")
        ruta_leaflet = str(BASE_DIR / "ui" / "assets" / "leaflet").replace("\\", "/")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="file://{ruta_leaflet}/leaflet.css" />
            <script src="file://{ruta_leaflet}/leaflet.js"></script>
            <style>
                body {{ margin: 0; padding: 0; background-color: #101829; font-family: 'Courier New', monospace; }}
                #map {{ width: 100vw; height: 100vh; }}
                .leaflet-container {{ background: #1c2533; }}
                
                /* HUD FLOTANTE: Esquina inferior derecha */
                #hud-overlay {{
                    position: absolute;
                    bottom: 20px;
                    right: 20px;
                    z-index: 1000;
                    background-color: rgba(16, 24, 41, 0.85);
                    border: 1px solid #00E5FF;
                    border-radius: 6px;
                    padding: 12px 18px;
                    box-shadow: 0 0 10px rgba(0, 229, 255, 0.2);
                    pointer-events: none;
                    min-width: 180px;
                }}
                .hud-row {{ margin: 6px 0; font-size: 15px; }}
                .hud-label {{ color: #00E5FF; font-weight: bold; margin-right: 10px; }}
                .hud-value {{ color: #FFFFFF; text-shadow: 0 0 5px rgba(255, 255, 255, 0.5); }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            
            <div id="hud-overlay">
                <div class="hud-row"><span class="hud-label">LAT:</span> <span class="hud-value" id="hud-lat">--.------</span></div>
                <div class="hud-row"><span class="hud-label">LON:</span> <span class="hud-value" id="hud-lon">--.------</span></div>
                <div class="hud-row"><span class="hud-label">ALT:</span> <span class="hud-value" id="hud-alt">-- m</span></div>
            </div>

            <script>
                var map;
                var marker;

                window.onload = function() {{
                    if (typeof L === 'undefined') {{
                        console.error("[CENTINELA] Error crítico: No se encontró Leaflet local.");
                        return;
                    }}

                    map = L.map('map', {{
                        center: [19.5031, -99.1350],
                        zoom: 18,
                        minZoom: 18,
                        maxZoom: 18,
                        zoomControl: false,
                        attributionControl: false
                    }});

                    L.tileLayer('file://{ruta_mapas}/{{z}}/{{x}}/{{y}}.jpg', {{
                        errorTileUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
                    }}).addTo(map);

                    marker = L.circleMarker([19.5031, -99.1350], {{
                        radius: 8, color: '#FF0000', fillColor: '#FF0000', fillOpacity: 0.8, weight: 2
                    }}).addTo(map);
                }};

                // Función de actualización optimizada sin variables de tiempo
                function actualizarPosicion(lat, lon, alt) {{
                    if (typeof map !== 'undefined' && typeof marker !== 'undefined') {{
                        map.setView([lat, lon], 18);
                        marker.setLatLng([lat, lon]);
                        
                        document.getElementById('hud-lat').innerText = lat.toFixed(6);
                        document.getElementById('hud-lon').innerText = lon.toFixed(6);
                        document.getElementById('hud-alt').innerText = alt.toFixed(2) + " m";
                    }}
                }}
            </script>
        </body>
        </html>
        """

        base_url = QUrl.fromLocalFile(str(BASE_DIR) + "/")
        self.gps_w.setHtml(html_content, base_url)

    @Slot(dict)
    def update_data(self, data: dict):
        """SLOT público: Filtra y envía únicamente coordenadas y altitud de GPS"""
        if "location" in data:
            lat = data["location"][0]
            lon = data["location"][1]
            alt = data.get("alt_gps", 0.0)

            if lat != 0.0 and lon != 0.0:
                script = f"actualizarPosicion({lat}, {lon}, {alt});"
                self.gps_w.page().runJavaScript(script)
