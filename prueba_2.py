import numpy as np
import pandas as pd
import pydeck as pdk

# 1. Coordenadas origen: Centro de la CDMX (Zócalo)
LAT_ORIGEN = 19.432608
LON_ORIGEN = -99.133209

# Factores de conversión
METROS_A_LAT = 1 / 111000
METROS_A_LON = 1 / 104700

# Parámetros de la misión
ALTITUD_APOGEO = 1000
DESVIACION_METROS = 500

num_puntos = 100
num_ascenso = num_puntos // 2
num_descenso = num_puntos - num_ascenso

# --- FASE 1: Ascenso ---
alt_ascenso = np.linspace(0, ALTITUD_APOGEO, num_ascenso)
lat_ascenso = np.full(num_ascenso, LAT_ORIGEN)
lon_ascenso = np.full(num_ascenso, LON_ORIGEN)

# --- FASE 2: Descenso ---
alt_descenso = np.linspace(ALTITUD_APOGEO, 0, num_descenso)
lon_descenso = np.linspace(
    LON_ORIGEN, LON_ORIGEN + (DESVIACION_METROS * METROS_A_LON), num_descenso
)
lat_descenso = np.full(num_descenso, LAT_ORIGEN)

# Concatenar
longitudes = np.concatenate([lon_ascenso, lon_descenso])
latitudes = np.concatenate([lat_ascenso, lat_descenso])
altitudes = np.concatenate([alt_ascenso, alt_descenso])

ruta_3d = [[lon, lat, alt] for lon, lat, alt in zip(longitudes, latitudes, altitudes)]

df_trayectoria = pd.DataFrame({"coordenadas": [ruta_3d]})

# 2. Capa de la trayectoria
capa_trayectoria = pdk.Layer(
    "PathLayer",
    data=df_trayectoria,
    get_path="coordenadas",
    get_color=[0, 255, 255],
    width_scale=1,
    width_min_pixels=5,
    get_width=3,
)

# 3. ESTILO SATELITAL LOCAL
# Conectamos el mapa a nuestro servidor local en el puerto 8000
# 3. ESTILO SATELITAL LOCAL CORREGIDO
estilo_satelite_local = {
    "version": 8,
    "sources": {
        "local-satellite": {
            "type": "raster",
            "tiles": [
                # Asegúrate de que la URL comience estrictamente con http://localhost:8000/
                "http://localhost:8000/mapas_satelite/{z}/{x}/{y}.jpg"
            ],
            "tileSize": 256,
            # RESTRICCIÓN CLAVE: Limitamos las peticiones exclusivamente a las carpetas que existen
            "minzoom": 18,
            "maxzoom": 18,
        }
    },
    "layers": [{"id": "satellite", "type": "raster", "source": "local-satellite"}],
}
# 4. Vista de la cámara
vista_camara = pdk.ViewState(
    latitude=LAT_ORIGEN,
    longitude=LON_ORIGEN + (DESVIACION_METROS * METROS_A_LON) / 2,
    zoom=18,  # Fijado a 14 para coincidir con las imágenes que descargaste
    pitch=65,
    bearing=60,
)

# 5. Construir el mapa
mapa = pdk.Deck(
    layers=[capa_trayectoria],
    initial_view_state=vista_camara,
    map_provider="mapbox",
    map_style=estilo_satelite_local,
)

mapa.to_html("mapa_trayectoria_offline.html")
print("¡Archivo generado! Recuerda iniciar el servidor local antes de abrirlo.")
