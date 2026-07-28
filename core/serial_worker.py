#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2026 CREADOR: Ramírez León Christian Yael
# SUBSISTEMA: Estación Terrena - Misión Noctiluca (CENTINELA I)

import csv
import sys
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    QFileSystemWatcher,
    QIODevice,
    QObject,
    QThread,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo


class SerialWorker(QObject):
    """
    Módulo de lógica que maneja la conexión serial, monitoreo y parseo.
    - Blindado contra cruces de hilos (Thread Affinity).
    - Reconexión automática inteligente ante desconexiones físicas (ResourceError).
    - Parseo de cuaterniones y filtros anti-ruido (ttyS).
    """

    # --- Señales hacia la UI ---
    port_list_updated = Signal(list)
    status_update = Signal(str, str)

    cinematica_updated = Signal(dict)
    visor_3d_updated = Signal(float, float, float, float)
    gps_data_updated = Signal(dict)
    altimetro_data_updated = Signal(int)
    graficas_data_updated = Signal(dict)
    calidad_aire_updated = Signal(dict)
    baterias_data_updated = Signal(int, int)
    paquetes_data_updated = Signal(int, int)
    estados_data_updated = Signal(dict)

    # --- ENCABEZADO (27 COLUMNAS TOTALES - Humedad Removida) ---
    CSV_HEADER = [
        "Contador_Paquetes_GS",
        "Acc_x",
        "Acc_y",
        "Acc_z",
        "Q0_w",
        "Q1_x",
        "Q2_y",
        "Q3_z",
        "Compass",
        "Latitud",
        "Longitud",
        "Altitud_GPS",
        "Hora_GPS",
        "Bateria_CANSAT",
        "Tiempo_encendido",
        "Tiempo_Mision",
        "No_Paquete_Enviado",
        "Temperatura",
        "Presion",
        "Altitud_Barometro",
        "Voltaje",
        "Corriente_Interna",
        "Estado_SD",
        "Estado_Autogiro",
        "Modo_Ahorro_Energia",
        "Etapa_mision",
        "Velocidad_Calculada_Z",
    ]

    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.known_port_list = []
        self.port_monitor = None
        self.serial_buffer = b""

        self.is_simulating = False
        self.gs_packet_count = 0
        self.last_packet_id = 0
        self.lost_packets = 0
        self.vel_window = []
        self.velocidad_z = 0.0

        self.MAX_GRAPH_POINTS = 1200
        self.graph_time = []
        self.graph_pressure = []
        self.graph_temp = []
        self.graph_voltaje = []
        self.graph_int_corr = []

        self.csv_file = None
        self.csv_writer = None

        self.last_update_30hz = 0
        self.last_update_20hz = 0
        self.last_update_05s = 0

        # --- VARIABLES PARA RECONEXIÓN AUTOMÁTICA ---
        self.target_port = None
        self.target_baud = 115200
        self.auto_reconnect = False

    @Slot()
    def init_worker(self):
        # Asignar 'self' garantiza que el puerto pertenece a este QThread
        self.serial_port = QSerialPort(self)
        self.serial_port.readyRead.connect(self.on_ready_read)
        self.serial_port.errorOccurred.connect(self.handle_serial_error)

        # Monitoreo reactivo de hardware en Linux
        if sys.platform.startswith("linux"):
            self.port_monitor = QFileSystemWatcher(self)
            self.port_monitor.addPath("/dev")
            self.port_monitor.directoryChanged.connect(self.check_available_ports)

        # Primer escaneo de puertos
        self.check_available_ports()

    @Slot()
    def check_available_ports(self):
        try:
            ports = QSerialPortInfo.availablePorts()
            # Filtramos puertos basura internos de Linux directamente en el core
            port_names = [p.portName() for p in ports if "ttyS" not in p.portName()]
        except Exception as e:
            self.status_update.emit(f"Error listando puertos: {e}", "danger")
            port_names = []

        if port_names != self.known_port_list:
            self.known_port_list = port_names
            self.port_list_updated.emit(port_names)

            # --- LÓGICA DE RECONEXIÓN FÍSICA ---
            if self.auto_reconnect and self.target_port in port_names:
                self.status_update.emit(
                    f"Puerto {self.target_port} detectado. Reconectando en 1s...",
                    "warning",
                )
                # Pausa táctica para que udev asigne permisos al puerto ttyUSB/ttyACM
                QTimer.singleShot(1000, self._attempt_reconnect)

    @Slot()
    def _attempt_reconnect(self):
        if self.auto_reconnect and self.target_port:
            self.start_connection(self.target_port, self.target_baud)

    @Slot(str, int)
    def start_connection(self, port: str, baud: int):
        if self.serial_port and self.serial_port.isOpen():
            return

        # Almacenamos destino por si hay desconexión abrupta
        self.target_port = port
        self.target_baud = baud

        self.serial_port.setPortName(port)
        self.serial_port.setBaudRate(baud)

        if self.serial_port.open(QIODevice.OpenModeFlag.ReadWrite):
            self.serial_port.clear(QSerialPort.Direction.AllDirections)

            if self.auto_reconnect:
                # Retomando misión: No limpiamos variables ni abrimos otro CSV
                self.status_update.emit(
                    f"Reconectado a {port}. Continuando vuelo...", "success"
                )
                self.auto_reconnect = False
            else:
                # Conexión fresca
                self.status_update.emit(f"Conectado a {port}", "success")
                self.reset_session_data()
                self.open_csv_file()
        else:
            self.status_update.emit(
                f"Error al abrir {port}: {self.serial_port.errorString()}", "danger"
            )

    @Slot()
    def stop_connection(self):
        # Desconexión manual voluntaria
        self.is_simulating = False
        self.auto_reconnect = False

        if self.serial_port and self.serial_port.isOpen():
            self.serial_port.close()
            self.status_update.emit("Desconectado manualmente.", "info")

        self.close_csv_file()

    @Slot(str)
    def send_command_sequence(self, command_str: str):
        if not self.serial_port or not self.serial_port.isOpen():
            self.status_update.emit("Error: No conectado.", "danger")
            return

        self.status_update.emit(f"Enviando: {command_str.strip()}", "info")
        cmd_bytes = command_str.encode("utf-8")
        try:
            self.serial_port.write(cmd_bytes)
        except Exception as e:
            self.status_update.emit(f"Error enviando: {e}", "danger")

    @Slot(QSerialPort.SerialPortError)
    def handle_serial_error(self, error):
        # Si no hay error, ignoramos
        if error == QSerialPort.SerialPortError.NoError:
            return

        # Detectar extracción física del cable USB
        if error == QSerialPort.SerialPortError.ResourceError:
            self.status_update.emit(
                f"Cable desconectado. Esperando {self.target_port}...", "danger"
            )

            if self.serial_port and self.serial_port.isOpen():
                self.serial_port.close()

            # IMPORTANTE: Mantenemos el CSV abierto y encendemos bandera de centinela
            self.auto_reconnect = True
        else:
            error_msg = self.serial_port.errorString()
            self.status_update.emit(f"Error de Puerto: {error_msg}", "danger")

    @Slot()
    def on_ready_read(self):
        self.serial_buffer += self.serial_port.readAll().data()
        while b"\n" in self.serial_buffer:
            packet_bytes, self.serial_buffer = self.serial_buffer.split(b"\n", 1)
            try:
                packet_string = packet_bytes.decode("utf-8").strip()
                if packet_string:
                    self.process_packet(packet_string)
            except UnicodeDecodeError:
                self.status_update.emit("Error decode UTF-8", "danger")

    @Slot(str)
    def run_simulation(self, file_path: str):
        self.is_simulating = True
        self.status_update.emit("Iniciando Simulación...", "success")
        self.reset_session_data()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            start_idx = (
                1 if len(lines) > 0 and "Contador_Paquetes_GS" in lines[0] else 0
            )

            for i in range(start_idx, len(lines)):
                if not self.is_simulating:
                    break
                line = lines[i].strip()
                if not line:
                    continue

                parts = line.split(",")

                if len(parts) == 27:
                    raw_parts = parts[1:26]
                    raw_data = ",".join(raw_parts)
                elif len(parts) == 25:
                    raw_data = line
                else:
                    continue

                self.process_packet(raw_data)
                QThread.msleep(16)

            if self.is_simulating:
                self.status_update.emit("Fin de la simulación.", "info")

        except Exception as e:
            self.status_update.emit(f"Error en simulación: {e}", "danger")
        finally:
            self.is_simulating = False

    def process_packet(self, packet_string: str):
        parts = packet_string.split(",")

        # Actualizado a 25 porque se quitó Humedad
        if len(parts) != 25:
            self.status_update.emit(
                f"Trama descartada. Longitud incorrecta: Recibidos {len(parts)}, Esperados 25.",
                "warning",
            )
            return

        esquema = [
            ("ax", 0, float),
            ("ay", 1, float),
            ("az", 2, float),
            ("q0", 3, float),
            ("q1", 4, float),
            ("q2", 5, float),
            ("q3", 6, float),
            ("compass", 7, float),
            ("lat", 8, float),
            ("lon", 9, float),
            ("alt_gps", 10, float),
            ("hora_gps", 11, str),
            ("bat_cansat", 12, lambda x: int(round(float(x)))),
            ("t_encendido", 13, float),
            ("t_mision", 14, float),
            ("no_paquete_enviado", 15, lambda x: int(round(float(x)))),
            ("temp", 16, float),
            ("pres", 17, float),
            ("alt_baro", 18, float),
            ("Volt", 19, float),
            ("Int_Corr", 20, float),
            ("estado_sd", 21, lambda x: bool(int(round(float(x))))),
            ("estado_autogiro", 22, lambda x: bool(int(round(float(x))))),
            ("modo_ahorro", 23, lambda x: bool(int(round(float(x))))),
            ("etapa_id", 24, lambda x: int(round(float(x)))),
        ]

        data = {}

        # Parseo defensivo
        for nombre, idx, conversor in esquema:
            try:
                if conversor == str:
                    data[nombre] = parts[idx].strip()
                else:
                    data[nombre] = conversor(parts[idx].strip())
            except ValueError:
                self.status_update.emit(
                    f"Corrupción de datos en '{nombre}' (Índice {idx}).", "danger"
                )
                return

        try:
            self.gs_packet_count += 1
            now = time.time()

            # Cinematica Z
            self.vel_window.append((data["t_mision"], data["alt_baro"]))
            if len(self.vel_window) > 20:
                self.vel_window.pop(0)
            if len(self.vel_window) > 1:
                dt = self.vel_window[-1][0] - self.vel_window[0][0]
                dh = self.vel_window[-1][1] - self.vel_window[0][1]
                if dt > 0:
                    self.velocidad_z = dh / dt

            # Gráficas
            self.graph_time.append(data["t_mision"])
            self.graph_pressure.append(data["pres"])
            self.graph_temp.append(data["temp"])
            self.graph_voltaje.append(data["Volt"])
            self.graph_int_corr.append(data["Int_Corr"])

            if len(self.graph_time) > self.MAX_GRAPH_POINTS:
                self.graph_time.pop(0)
                self.graph_pressure.pop(0)
                self.graph_temp.pop(0)
                self.graph_voltaje.pop(0)
                self.graph_int_corr.pop(0)

            # Paquetes perdidos
            if data["no_paquete_enviado"] > (self.last_packet_id + 1):
                self.lost_packets += (
                    data["no_paquete_enviado"] - self.last_packet_id - 1
                )
            self.last_packet_id = data["no_paquete_enviado"]

            # Escritura en CSV Oficial
            if self.csv_writer:
                row = [self.gs_packet_count] + parts + [f"{self.velocidad_z:.3f}"]
                self.csv_writer.writerow(row)

            # --- EMISIÓN CONTROLADA DE SEÑALES ---
            # 30 Hz (3D y GPS)
            if (now - self.last_update_30hz) > 0.016:
                self.visor_3d_updated.emit(
                    data["q0"], data["q1"], data["q2"], data["q3"]
                )
                self.gps_data_updated.emit(
                    {
                        "location": [data["lat"], data["lon"]],
                        "alt_gps": data["alt_gps"],
                        "start_time": data["hora_gps"],
                        "flight_time": data["t_mision"],
                    }
                )
                self.last_update_30hz = now

            # 20 Hz (Cinemática e Instrumentos Rápidos)
            if (now - self.last_update_20hz) > 0.05:
                self.cinematica_updated.emit(
                    {
                        "ax": data["ax"],
                        "ay": data["ay"],
                        "az": data["az"],
                        "vel": self.velocidad_z,
                        "yaw": data["compass"],
                    }
                )
                self.paquetes_data_updated.emit(
                    data["no_paquete_enviado"], self.lost_packets
                )
                self.altimetro_data_updated.emit(int(data["alt_baro"]))
                self.last_update_20hz = now

            # 2 Hz (Gráficas y Baterías)
            if (now - self.last_update_05s) > 0.5:
                self.graficas_data_updated.emit(
                    {
                        "time": self.graph_time,
                        "temp": self.graph_temp,
                        "pres": self.graph_pressure,
                    }
                )
                self.calidad_aire_updated.emit(
                    {
                        "time": self.graph_time,
                        "voltaje": self.graph_voltaje,
                        "temp2": self.graph_int_corr,  # Enviamos Int_Corr bajo temp2 para la UI
                    }
                )
                self.baterias_data_updated.emit(data["bat_cansat"], 0)

                etapas = {
                    0: "Calibración",
                    1: "Esperando en rampa",
                    2: "Ascenso",
                    3: "Apogeo",
                    4: "Descenso",
                }
                self.estados_data_updated.emit(
                    {
                        "etapa": etapas.get(data["etapa_id"], "DESCONOCIDO"),
                        "lanzamiento": False,
                        "camara": False,
                        "sd": data["estado_sd"],
                    }
                )
                self.last_update_05s = now

        except Exception as e:
            self.status_update.emit(
                f"Error interno procesando paquete válido: {e}", "danger"
            )

    def reset_session_data(self):
        self.last_packet_id = 0
        self.lost_packets = 0
        self.gs_packet_count = 0
        self.vel_window.clear()
        self.velocidad_z = 0.0

        self.graph_time.clear()
        self.graph_pressure.clear()
        self.graph_temp.clear()
        self.graph_voltaje.clear()
        self.graph_int_corr.clear()

        now = time.time()
        self.last_update_30hz = now
        self.last_update_20hz = now
        self.last_update_05s = now

    def open_csv_file(self):
        self.close_csv_file()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"log_vuelo_{timestamp}.csv"
        BASE_DIR = Path(__file__).resolve().parent.parent
        LOGS_DIR = BASE_DIR / "logs"
        LOGS_DIR.mkdir(exist_ok=True)
        try:
            self.csv_file = open(
                str(LOGS_DIR / filename), "w", newline="", encoding="utf-8"
            )
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow(self.CSV_HEADER)
            self.status_update.emit(f"Grabando en: logs/{filename}", "success")
        except Exception as e:
            self.status_update.emit(f"Error creando CSV: {e}", "danger")

    def close_csv_file(self):
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
