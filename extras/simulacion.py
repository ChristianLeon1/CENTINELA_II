#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2026 CREADOR: Ramírez León Christian Yael

import datetime

import numpy as np
import pandas as pd

# --- CONFIGURACIÓN DE LA SIMULACIÓN ---
num_muestras = 2000  # Cantidad de paquetes a simular
frecuencia_hz = 30  # Muestras por segundo
archivo_salida = "telemetria_esfm_ordenada.csv"

# Nuevos parámetros geográficos (Coordenada Inicial)
LAT_INICIAL = 19.50245088879069
LON_INICIAL = -99.13281605313541
ALT_SUELO_MSL = 2240.0

# Tasa de desplazamiento (grados por segundo)
# 0.00005 grados equivalen a unos ~5.5 metros por segundo.
# Al tener la misma tasa en latitud y longitud, el movimiento será una línea diagonal a 45 grados.
TASA_LAT = 0.00005
TASA_LON = 0.00005


def generar_simulacion():
    datos = []
    tiempo_inicial = datetime.datetime.now()

    # Variables de estado físico y tiempo
    dt = 1.0 / frecuencia_hz
    t = 0.0
    z = 0.0  # Altura relativa inicial (m)
    v = 15.0  # Velocidad inicial de ascenso (m/s)
    etapa = 1  # Máquina de estados
    t_espera = 0.0  # Cronómetro para la etapa 2

    for i in range(num_muestras):
        # LÓGICA DEL PERFIL DE VUELO
        g_factor = 1.0  # Multiplicador de gravedad

        if etapa == 1:  # 1. Ascenso
            z += v * dt
            if z >= 450.0:
                z = 450.0
                v = 0.0
                t_espera = t
                etapa = 2

        elif etapa == 2:  # 2. Espera de 5 segundos
            v = 0.0
            if (t - t_espera) >= 5.0:
                v = 0.0
                etapa = 3

        elif etapa == 3:  # 3. Caída libre hasta 200 m
            g_factor = 0.0
            v -= 9.81 * dt
            z += v * dt
            if z <= 200.0:
                z = 200.0
                v = -10.0  # Apertura paracaídas
                etapa = 4

        elif etapa == 4:  # 4. Descenso constante
            z += v * dt
            if z <= 0.0:
                z = 0.0
                v = 0.0
                etapa = 5

        elif etapa == 5:  # 5. Aterrizaje
            z = 0.0
            v = 0.0

        # Dinámica del giroscopio/rotación (15 grados por segundo)
        angulo_deg = (t * 15.0) % 360
        angulo_rad = np.radians(angulo_deg)

        # SIMULACIÓN DE CUATERNIONES (Rotación en un eje simulando el 'Roll')
        half_angle = angulo_rad / 2.0
        q_w = np.cos(half_angle)
        q_x = np.sin(half_angle)  # Girando sobre el eje X
        q_y = 0.0
        q_z = 0.0

        # Aceleración repartida
        acc_x = (9.81 * g_factor) * np.sin(angulo_rad)
        acc_y = 0.0 + np.random.normal(0, 0.05)
        acc_z = (9.81 * g_factor) * np.cos(angulo_rad)

        # Dinámica del entorno
        temp_actual = 23.5 - (z * 0.0065) + np.random.normal(0, 0.2)
        pres_actual = 77550.0 - (z * 11.3) + np.random.normal(0, 10)

        # Calculamos la batería ANTES de crear el diccionario
        bat_actual = int(max(0, 100 - (t * 0.05)))

        # LÓGICA DE DESPLAZAMIENTO DIAGONAL
        # La posición cambia linealmente respecto al tiempo transcurrido (t)
        lat_actual = LAT_INICIAL + (TASA_LAT * t)
        lon_actual = LON_INICIAL + (TASA_LON * t)

        # Diccionario ESTRICTO de 28 columnas
        paquete = {
            "Contador_Paquetes_GS": int(i + 1),  # 0
            "Acc_x": round(acc_x, 3),  # 1
            "Acc_y": round(acc_y, 3),  # 2
            "Acc_z": round(acc_z, 3),  # 3
            "Q0_w": round(q_w, 4),  # 4  <-- Cuaternión
            "Q1_x": round(q_x, 4),  # 5  <-- Cuaternión
            "Q2_y": round(q_y, 4),  # 6  <-- Cuaternión
            "Q3_z": round(q_z, 4),  # 7  <-- Cuaternión
            "Compass": 180.0,  # 8
            "Latitud": round(lat_actual, 7),  # 9 <-- Actualizado en movimiento
            "Longitud": round(lon_actual, 7),  # 10 <-- Actualizado en movimiento
            "Altitud_GPS": round(ALT_SUELO_MSL + z, 2),  # 11
            "Hora_GPS": (tiempo_inicial + datetime.timedelta(seconds=int(t))).strftime(
                "%H:%M:%S"
            ),  # 12
            "Bateria_CANSAT": bat_actual,  # 13
            "Tiempo_encendido": round(t, 2),  # 14
            "Tiempo_Mision": round(t, 2),  # 15
            "No_Paquete_Enviado": int(i + 1),  # 16
            "Temperatura": round(temp_actual, 2),  # 17
            "Presion": round(pres_actual, 2),  # 18
            "Altitud_Barometro": round(z + np.random.normal(0, 0.1), 2),  # 19
            "TVOC": float(int(110 + np.random.randint(0, 15))),  # 20
            "CO2": float(int(420 + np.random.randint(0, 40))),  # 21
            "Humedad": round(48.0 + np.random.normal(0, 0.5), 1),  # 22
            "Estado_SD": 1,  # 23
            "Estado_Autogiro": 1 if etapa > 2 else 0,  # 24
            "Modo_Ahorro_Energia": 1 if bat_actual < 20 else 0,  # 25
            "Etapa_mision": etapa,  # 26
            "Velocidad_Calculada_Z": round(v, 3),  # 27
        }

        datos.append(paquete)
        t += dt  # Avanzar el tiempo simulado

    # Pandas respeta el orden del diccionario al crear el DataFrame
    df = pd.DataFrame(datos)

    # No guardar el índice para evitar una columna extra al inicio
    df.to_csv(archivo_salida, index=False)

    print(f"Éxito: Archivo '{archivo_salida}' generado.")
    print(f"Total de columnas: {len(df.columns)} (Deben ser exactamente 28)")
    print("Columnas en el archivo:", list(df.columns))


if __name__ == "__main__":
    generar_simulacion()
