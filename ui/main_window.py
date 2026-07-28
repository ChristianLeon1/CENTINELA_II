#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2026 CREADOR: Christian Yael Ramírez León

import json
from pathlib import Path

import psutil
from PySide6.QtCore import QRect, QSize, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QColor, QPainter
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QHBoxLayout,
                               QLabel, QLineEdit, QMainWindow, QPlainTextEdit,
                               QToolBar, QVBoxLayout, QWidget)

from ui.theme import PALETTE
from ui.widgets.panel_altimetro import PanelAltimetro
from ui.widgets.panel_calidad_aire import PanelCalidadAire
from ui.widgets.panel_estados import PanelEstados
from ui.widgets.panel_gps import PanelGPS
from ui.widgets.panel_graficas import PanelGraficas
from ui.widgets.panel_inferior import PanelInferior
from ui.widgets.panel_superior import PanelSuperior
from ui.widgets.panel_visor_3d import PanelVisor3D
from ui.widgets.panel_visor_imagenes import PanelVisorImagenes


class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(45, 24)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        track_rect = QRect(0, 2, 40, 20)
        handle_radius = 8

        if self.isChecked():
            track_color = QColor(PALETTE["ACCENT"]["ACTIVE"])
            handle_pos = 22
        else:
            track_color = QColor(PALETTE["TEXT"]["DISABLED"])
            handle_pos = 2

        p.setBrush(track_color)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(track_rect, 10, 10)
        p.setBrush(QColor(PALETTE["TEXT"]["PRIMARY"]))
        p.drawEllipse(handle_pos, 4, handle_radius * 2, handle_radius * 2)


class GroundStation(QMainWindow):
    conexion_solicitada = Signal(str, int)
    desconexion_solicitada = Signal()
    actualizar_puertos_solicitado = Signal()
    comando_solicitado = Signal(str)
    simulacion_solicitada = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Estación Terrena")

        self.data_store = {
            "cinematica": None,
            "visor_3d": None,
            "gps": None,
            "altimetro": None,
            "graficas": None,
            "calidad_aire": None,
            "baterias": None,
            "paquetes": None,
            "estados": None,
        }

        self.setup_toolbar()
        self.setup_central_widget()
        self.setup_ui_timers()

    def setup_ui_timers(self):
        # Timer de 30Hz para 3D (se mantiene independiente por fluidez visual)
        self.timer_30hz = QTimer(self)
        self.timer_30hz.timeout.connect(self.update_ui_30hz)
        self.timer_30hz.start(16)

        # Timer Unificado: Corre a 20Hz (50ms)
        self.timer_unified = QTimer(self)
        self.timer_unified.timeout.connect(self.update_ui_unified)
        self.timer_unified.start(50)

        # Contador para disparar eventos de 500ms
        self.ticks_500ms = 0

    # --- SLOTS DE RECEPCIÓN ---
    @Slot(dict)
    def on_cinematica_updated(self, data: dict):
        self.data_store["cinematica"] = data

    @Slot(float, float, float, float)
    def on_visor_3d_updated(self, q0, q1, q2, q3):
        self.data_store["visor_3d"] = (q0, q1, q2, q3)

    @Slot(dict)
    def on_gps_data_updated(self, data: dict):
        self.data_store["gps"] = data

    @Slot(int)
    def on_altimetro_data_updated(self, alt):
        self.data_store["altimetro"] = alt

    @Slot(dict)
    def on_graficas_data_updated(self, data: dict):
        self.data_store["graficas"] = data

    @Slot(dict)
    def on_calidad_aire_updated(self, data: dict):
        self.data_store["calidad_aire"] = data

    @Slot(int, int)
    def on_baterias_data_updated(self, bc, bcam):
        self.data_store["baterias"] = (bc, bcam)

    @Slot(int, int)
    def on_paquetes_data_updated(self, r, l):
        self.data_store["paquetes"] = (r, l)

    @Slot(dict)
    def on_estados_data_updated(self, data: dict):
        self.data_store["estados"] = data

    def update_ui_30hz(self):
        if self.data_store["visor_3d"]:
            self.panel_visor_3d.update_orientation(*self.data_store["visor_3d"])
            self.panel_visor_3d.update_altura(self.data_store["altimetro"] or 0)

        if self.data_store["gps"]:
            self.panel_gps.update_data(self.data_store["gps"])
            self.data_store["gps"] = None

    def update_ui_unified(self):
        # ==========================================
        # 1. ACTUALIZACIONES RÁPIDAS (20 Hz / 50 ms)
        # ==========================================
        if self.data_store["cinematica"]:
            self.panel_inferior.update_cinematica(self.data_store["cinematica"])

        if self.data_store["paquetes"]:
            self.panel_inferior.update_packet_summary(*self.data_store["paquetes"])

        if self.data_store["altimetro"] is not None:
            self.panel_altimetro.update_altitud(self.data_store["altimetro"])

        # ==========================================
        # 2. ACTUALIZACIONES LENTAS (2 Hz / 500 ms)
        # ==========================================
        self.ticks_500ms += 1
        if self.ticks_500ms >= 10:  # 10 ciclos de 50ms = 500ms
            self.ticks_500ms = 0

            # --- Actualización de Gráficas de Presión y Temp ---
            dg = self.data_store["graficas"]
            if dg and "time" in dg:
                if hasattr(self.panel_calidad_aire, "update_pressure_graph"):
                    self.panel_calidad_aire.update_pressure_graph(
                        dg["time"], dg["pres"]
                    )
                    self.panel_calidad_aire.update_temp_graph(dg["time"], dg["temp"])

            # --- Actualización de Gráficas de Voltaje y Corriente ---
            da = self.data_store["calidad_aire"]
            if da and "time" in da:
                voltaje = da.get("voltaje", da.get("co2", []))
                corriente = da.get("temp2", da.get("tvoc", []))
                humedad = da.get("hum", [])

                self.panel_graficas.update_voltage_graph(da["time"], voltaje)
                self.panel_graficas.update_current_graph(da["time"], corriente)

                if hasattr(self.panel_calidad_aire, "update_humidity_graph"):
                    self.panel_calidad_aire.update_humidity_graph(da["time"], humedad)

            # --- Actualización de Baterías ---
            if self.data_store["baterias"]:
                self.update_cansat_battery(self.data_store["baterias"][0])
                self.actualizar_bateria_pc()

            # --- Actualización de Estados ---
            if self.data_store["estados"]:
                self.panel_estados.update_data(self.data_store["estados"])

            # --- Guardado de Imagen ---
            # if hasattr(self.panel_visor_imagenes, "guardar_imagen"):
            #     self.panel_visor_imagenes.guardar_imagen()

    def setup_central_widget(self):
        central_container = QWidget()
        root_layout = QVBoxLayout(central_container)
        root_layout.setSpacing(10)
        root_layout.setContentsMargins(10, 10, 10, 10)

        self.panel_superior = PanelSuperior()
        root_layout.addWidget(self.panel_superior)

        workspace_layout = QHBoxLayout()
        workspace_layout.setSpacing(10)

        bloque_izquierdo = QWidget()
        lay_izquierdo = QVBoxLayout(bloque_izquierdo)
        lay_izquierdo.setContentsMargins(0, 0, 0, 0)
        lay_izquierdo.setSpacing(10)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        col_izq = QWidget()
        lay_izq = QVBoxLayout(col_izq)
        lay_izq.setContentsMargins(0, 0, 0, 0)
        lay_izq.setSpacing(10)
        self.panel_gps = PanelGPS()
        self.panel_graficas = PanelGraficas()
        self.panel_visor_imagenes = PanelVisorImagenes()

        lay_izq.addWidget(self.panel_gps, 1)
        lay_izq.addWidget(self.panel_visor_imagenes, 1)

        col_cen = QWidget()
        lay_cen = QVBoxLayout(col_cen)
        lay_cen.setContentsMargins(0, 0, 0, 0)
        lay_cen.setSpacing(10)

        lay_cen_top = QHBoxLayout()
        lay_cen_top.setSpacing(10)
        self.panel_visor_3d = PanelVisor3D()
        self.panel_altimetro = PanelAltimetro()
        lay_cen_top.addWidget(self.panel_visor_3d, 3)
        lay_cen_top.addWidget(self.panel_altimetro, 1)

        lay_cen.addLayout(lay_cen_top, 1)

        content_layout.addWidget(col_izq, 1)
        content_layout.addWidget(col_cen, 2)
        lay_izquierdo.addLayout(content_layout, 1)

        self.panel_inferior = PanelInferior()
        lay_izquierdo.addWidget(self.panel_inferior)

        col_der = QWidget()
        lay_der = QVBoxLayout(col_der)
        lay_der.setContentsMargins(0, 0, 0, 0)
        lay_der.setSpacing(10)

        self.panel_estados = PanelEstados()

        self.panel_calidad_aire = PanelCalidadAire()

        lay_der.addWidget(self.panel_estados, 0)
        lay_der.addWidget(self.panel_graficas, 1)
        lay_der.addWidget(self.panel_calidad_aire, 2)

        workspace_layout.addWidget(bloque_izquierdo, 3)
        workspace_layout.addWidget(col_der, 1)

        root_layout.addLayout(workspace_layout, 1)
        self.setCentralWidget(central_container)

    def setup_toolbar(self):
        self.toolbar = QToolBar("Barra de Control")
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.BottomToolBarArea, self.toolbar)

        estilo_bloque = f"""
            background-color: {PALETTE["BACKGROUND"]["PANEL"]}; 
            border: 1px solid {PALETTE["BORDER"]["DEFAULT"]}; 
            border-radius: 4px; 
            padding: 3px 8px; 
            color: {PALETTE["TEXT"]["DISABLED"]}; 
            font-weight: bold;
        """

        ruta_raiz = Path(__file__).resolve().parent.parent
        ruta_json = ruta_raiz / "config_centinela.json"
        puerto_seleccionado = "Ninguno"
        baudrate_seleccionado = "115200"
        mensaje_inicial = "Esperando..."

        try:
            if ruta_json.exists():
                with open(ruta_json, "r", encoding="utf-8") as f:
                    datos_config = json.load(f)
                    puerto_seleccionado = (
                        datos_config.get("puerto", "Ninguno") or "Ninguno"
                    )
                    baudrate_seleccionado = str(datos_config.get("baudrate", 115200))
            else:
                mensaje_inicial = "Archivo JSON no encontrado"
        except Exception:
            mensaje_inicial = "Error leyendo configuración"

        estilo_titulo = f"color: {PALETTE['TEXT']['SECONDARY']};"

        lbl_puerto_title = QLabel(" Puerto Serial: ")
        lbl_puerto_title.setStyleSheet(estilo_titulo)
        self.lbl_puerto_val = QLabel(puerto_seleccionado)
        self.lbl_puerto_val.setStyleSheet(estilo_bloque)

        lbl_baud_title = QLabel(" BaudRate: ")
        lbl_baud_title.setStyleSheet(estilo_titulo)
        self.lbl_baud_val = QLabel(baudrate_seleccionado)
        self.lbl_baud_val.setStyleSheet(estilo_bloque)

        lbl_ahorro_title = QLabel(" Ahorro de energía: ")
        lbl_ahorro_title.setStyleSheet(estilo_titulo)
        self.switch_ahorro = ToggleSwitch()
        self.switch_ahorro.toggled.connect(self.on_ahorro_toggled)

        lbl_autogiro_title = QLabel(" Autogiro: ")
        lbl_autogiro_title.setStyleSheet(estilo_titulo)
        self.switch_autogiro = ToggleSwitch()
        self.switch_autogiro.toggled.connect(self.on_autogiro_toggled)

        # --- INSTANCIACIÓN DE ACCIONES (QACTION) ---
        self.act_iniciar_mision = QAction("Iniciar Tiempo Misión", self)
        self.act_iniciar_mision.triggered.connect(self.on_iniciar_mision_triggered)

        self.act_activar_camara = QAction("Activar Cámara", self)
        self.act_activar_camara.triggered.connect(self.on_activar_camara_triggered)

        # Nueva Acción: Calibrar Altura
        self.act_calib_altura = QAction("Calibrar Altura", self)
        self.act_calib_altura.triggered.connect(self.on_calib_altura_triggered)

        lbl_msg_title = QLabel(" Mensajes: ")
        lbl_msg_title.setStyleSheet(estilo_titulo)
        self.label_mensajes = QLabel(mensaje_inicial)
        self.label_mensajes.setStyleSheet(estilo_bloque)
        self.label_mensajes.setMinimumWidth(500)
        self.label_mensajes.setMaximumWidth(500)

        self.label_bat_cansat = QLabel(" Bateria CanSat: --% ")
        self.label_bat_cansat.setStyleSheet(estilo_titulo)
        self.label_bat_pc = QLabel(" Bateria PC: --% ")
        self.label_bat_pc.setStyleSheet(estilo_titulo)

        # --- ENSAMBLAJE DEL TOOLBAR ---
        self.toolbar.clear()
        self.toolbar.addWidget(lbl_puerto_title)
        self.toolbar.addWidget(self.lbl_puerto_val)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(lbl_baud_title)
        self.toolbar.addWidget(self.lbl_baud_val)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(lbl_ahorro_title)
        self.toolbar.addWidget(self.switch_ahorro)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(lbl_autogiro_title)
        self.toolbar.addWidget(self.switch_autogiro)
        self.toolbar.addSeparator()

        self.toolbar.addAction(self.act_iniciar_mision)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.act_activar_camara)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.act_calib_altura)
        self.toolbar.addSeparator()

        self.toolbar.addWidget(lbl_msg_title)
        self.toolbar.addWidget(self.label_mensajes)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.label_bat_cansat)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.label_bat_pc)

    @Slot()
    def on_iniciar_mision_triggered(self):
        self.comando_solicitado.emit("5\n")
        self.label_mensajes.setText("Comando enviado: Iniciar Tiempo Misión (5)")
        self.act_iniciar_mision.setEnabled(False)

    @Slot()
    def on_activar_camara_triggered(self):
        self.comando_solicitado.emit("6\n")
        self.label_mensajes.setText("Comando enviado: Activar Cámara (6)")

    @Slot()
    def on_calib_altura_triggered(self):
        # 1. Enviar el 7 de inmediato
        self.comando_solicitado.emit("7\n")
        self.label_mensajes.setText("Comando enviado: Calibrando Altura (7 -> 10)")

        # 2. Deshabilitar el botón
        self.act_calib_altura.setEnabled(False)

        # 3. Enviar el 10 sin bloquear el hilo después de 50 ms
        QTimer.singleShot(50, lambda: self.comando_solicitado.emit("10\n"))

    @Slot(bool)
    def on_autogiro_toggled(self, checked):
        self.comando_solicitado.emit("1\n" if checked else "2\n")
        self.label_mensajes.setText(
            "Comando enviado: Autogiro Activado (1)"
            if checked
            else "Comando enviado: Autogiro Desactivado (2)"
        )

    @Slot(bool)
    def on_ahorro_toggled(self, checked):
        self.comando_solicitado.emit("3\n" if checked else "4\n")
        self.label_mensajes.setText(
            "Comando enviado: Modo Ahorro Activado (3)"
            if checked
            else "Comando enviado: Modo Ahorro Desactivado (4)"
        )

    @Slot()
    def actualizar_bateria_pc(self):
        bateria = psutil.sensors_battery()
        if bateria is not None:
            porcentaje = int(bateria.percent)
            self.label_bat_pc.setText(f" Bateria PC: {porcentaje}% ")
            self.label_bat_pc.setStyleSheet(
                f"color: {PALETTE['STATUS']['DANGER']}; font-weight: bold;"
                if porcentaje <= 20
                else f"color: {PALETTE['TEXT']['SECONDARY']};"
            )
        else:
            self.label_bat_pc.setText(" Bateria PC: N/A ")

    @Slot(float)
    def update_cansat_battery(self, porcentaje: float):
        self.label_bat_cansat.setText(f" Bateria CanSat: {porcentaje:.1f}% ")
        self.label_bat_cansat.setStyleSheet(
            f"color: {PALETTE['STATUS']['DANGER']}; font-weight: bold;"
            if porcentaje <= 20.0
            else f"color: {PALETTE['TEXT']['SECONDARY']};"
        )

    @Slot(list)
    def update_port_list(self, ports: list):
        puerto_configurado = self.lbl_puerto_val.text()
        if puerto_configurado == "Ninguno":
            return
        self.label_mensajes.setText(
            f"Puerto {puerto_configurado} detectado y listo."
            if puerto_configurado in ports
            else f"Advertencia: Puerto {puerto_configurado} no encontrado."
        )

    @Slot(str, str)
    def on_connection_status(self, message: str, status_type: str):
        self.label_mensajes.setText(f"{message}")

    def closeEvent(self, event):
        self.desconexion_solicitada.emit()
        QThread.msleep(100)
        event.accept()
