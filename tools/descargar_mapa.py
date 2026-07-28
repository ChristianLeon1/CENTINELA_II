#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0**zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def descargar_zoom_18_cdmx(
    lat_min, lat_max, lon_min, lon_max, carpeta_destino="mapas_satelite"
):
    ruta_base = Path(__file__).resolve().parent.parent
    ruta_destino_absoluta = ruta_base / carpeta_destino
    os.makedirs(ruta_destino_absoluta, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }

    ZOOM = 18

    # --- FASE 1: ANÁLISIS MATEMÁTICO ---
    print("=" * 60)
    print(f"      ANÁLISIS DE TELEMETRÍA TÁCTICA: DESCARGA ZOOM {ZOOM}")
    print("=" * 60)

    x_min, y_max_tile = deg2num(lat_min, lon_min, ZOOM)
    x_max, y_min_tile = deg2num(lat_max, lon_max, ZOOM)

    x0, x1 = min(x_min, x_max), max(x_min, x_max)
    y0, y1 = min(y_min_tile, y_max_tile), max(y_min_tile, y_max_tile)

    total_tiles = (x1 - x0 + 1) * (y1 - y0 + 1)

    # Estimación de métricas
    tiempo_estimado_segundos = total_tiles * 0.15
    tiempo_estimado_horas = tiempo_estimado_segundos / 3600
    peso_estimado_gb = (total_tiles * 35) / 1024 / 1024

    # --- CÁLCULO DE HORA DE FINALIZACIÓN ---
    hora_actual = datetime.now()
    hora_finalizacion = hora_actual + timedelta(seconds=tiempo_estimado_segundos)

    print(f"-> Total de imágenes a descargar: {total_tiles:,} archivos.")
    print(f"-> Peso aproximado en disco:     ~{peso_estimado_gb:.2f} GB")
    print(f"-> Tiempo estimado de descarga:  ~{tiempo_estimado_horas:.2f} horas.")
    print(
        f"-> HORA ESTIMADA DE CONCLUSIÓN:  {hora_finalizacion.strftime('%I:%M %p del %d/%m/%Y')}"
    )
    print("-" * 60)

    # --- FASE 2: SEGURO DE SEGURIDAD ---
    print("El proceso iniciará en 5 segundos...")
    print("Presiona Ctrl + C si deseas abortar ahora.")
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n[SISTEMA] Descarga abortada por el operador.")
        return

    # --- FASE 3: EXTRACCIÓN MASIVA ---
    print("\n[PROCESO] Iniciando descarga de mosaicos satitales...")
    descargadas = 0
    errores = 0
    existentes = 0

    start_time = time.time()

    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{ZOOM}/{y}/{x}"
            ruta_img = os.path.join(
                ruta_destino_absoluta, str(ZOOM), str(x), f"{y}.jpg"
            )

            if not os.path.exists(ruta_img):
                os.makedirs(os.path.dirname(ruta_img), exist_ok=True)
                try:
                    req = requests.get(url, headers=headers, timeout=12)
                    if req.status_code == 200:
                        with open(ruta_img, "wb") as f:
                            f.write(req.content)
                        descargadas += 1
                        time.sleep(0.1)  # Delay crítico anti-ban
                    else:
                        errores += 1
                except Exception:
                    errores += 1
            else:
                existentes += 1
                descargadas += 1

            if (descargadas % 5 == 0) or (descargadas == total_tiles):
                porcentaje = (descargadas / total_tiles) * 100
                print(
                    f"\rProgreso: {porcentaje:.2f}% | Descargados: {descargadas}/{total_tiles} | Ya existían: {existentes} | Errores: {errores}",
                    end="",
                    flush=True,
                )

    end_time = time.time()
    duracion_real_horas = (end_time - start_time) / 3600

    print("\n\n" + "=" * 60)
    print("      RESUMEN FINAL DE LA OPERACIÓN OFFLINE")
    print("=" * 60)
    print(f"Tiempo real de ejecución: {duracion_real_horas:.2f} horas.")
    print(f"Mosaicos descargados con éxito: {descargadas - errores - existentes}")
    print(f"Mosaicos recuperados del caché: {existentes}")
    print(f"Mosaicos con error de red:     {errores}")
    print("=" * 60)


if __name__ == "__main__":
    LAT_NORTE = 19.65
    LAT_SUR = 19.20
    LON_OESTE = -99.35
    LON_ESTE = -98.90

    descargar_zoom_18_cdmx(
        lat_min=LAT_SUR, lat_max=LAT_NORTE, lon_min=LON_OESTE, lon_max=LON_ESTE
    )
