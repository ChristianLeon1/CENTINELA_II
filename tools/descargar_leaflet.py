#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2026 CREADOR: Ramírez León Christian Yael

import os
import requests
from pathlib import Path


def preparar_motor_offline():
    # Creamos la carpeta ui/assets/leaflet en la raíz del proyecto
    ruta_base = Path(__file__).resolve().parent.parent / "ui" / "assets" / "leaflet"
    os.makedirs(ruta_base, exist_ok=True)

    # Archivos del motor Leaflet v1.9.4
    archivos = {
        "leaflet.css": "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
        "leaflet.js": "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    for nombre, url in archivos.items():
        ruta_archivo = ruta_base / nombre
        if not ruta_archivo.exists():
            print(f"Descargando motor base: {nombre}...")
            try:
                req = requests.get(url, headers=headers, timeout=10)
                if req.status_code == 200:
                    with open(ruta_archivo, "wb") as f:
                        f.write(req.content)
                    print(f"✓ {nombre} guardado.")
                else:
                    print(f"Error HTTP {req.status_code} al descargar {nombre}")
            except Exception as e:
                print(f"Error de red: {e}")
        else:
            print(f"✓ {nombre} ya existe en local.")

    print("\n¡CENTINELA I ahora tiene su motor de mapas 100% local y autónomo!")


if __name__ == "__main__":
    preparar_motor_offline()
