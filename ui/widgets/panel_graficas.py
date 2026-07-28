#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2026 CREADOR: Christian Yael Ramírez León

import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget

from ui.theme import PALETTE

# Configuración global de pyqtgraph para que coincida con el tema
pg.setConfigOption("background", None)
pg.setConfigOption("foreground", PALETTE["TEXT"]["SECONDARY"])
pg.setConfigOption("antialias", True)


# --- 1. Clase Base para la Gráfica ---
class CustomGraph(pg.PlotWidget):
    def __init__(self, name="", units="", pen=None, brush=None, parent=None):
        super().__init__(parent)

        # Configuración de Ejes y Rejilla
        self.showGrid(x=True, y=True, alpha=0.3)
        self.setLabel("left", name, units=units)
        self.setLabel("bottom", "Tiempo", units="s")

        # Rango inicial del eje X (0 a 15 segundos)
        self.setXRange(0, 15)

        # Deshabilitar interacción del mouse para que no rompa la lógica automática
        self.setMouseEnabled(x=False, y=True)
        self.getPlotItem().setMenuEnabled(False)

        # Ajuste de margen izquierdo para que los números no se corten
        self.getPlotItem().getAxis("left").setWidth(60)

        # Crear la curva de datos
        self.data_line = self.plot(pen=pen, fillLevel=0, brush=brush)

    def update_data(self, x_data, y_data):
        """Actualiza la línea con nuevos datos."""
        self.data_line.setData(x_data, y_data)


# --- 2. Panel Principal de Gráficas ---
class PanelGraficas(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("isPanel", True)

        # --- Variables para la lógica de paginación (Scroll) ---
        self.current_max_x = 15.0  # El límite actual
        self.window_size = 15.0  # El tamaño de la ventana
        # -----------------------------------------------------

        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- COLUMNA IZQUIERDA: VOLTAJE ---
        col_voltage = QVBoxLayout()
        col_voltage.setSpacing(5)

        # Estilo (Cian)
        pen_v = pg.mkPen(PALETTE["ACCENT"]["ACTIVE"], width=2)
        brush_v = (
            *QColor(PALETTE["ACCENT"]["ACTIVE"]).getRgb()[:3],
            30,
        )  # Transparencia

        self.graph_voltage = CustomGraph("Voltaje", "V", pen=pen_v, brush=brush_v)
        col_voltage.addWidget(self.graph_voltage)

        # --- COLUMNA DERECHA: CORRIENTE ---
        col_current = QVBoxLayout()
        col_current.setSpacing(5)

        # Estilo (Amarillo/Ámbar)
        pen_c = pg.mkPen(PALETTE["STATUS"]["WARNING"], width=2)
        brush_c = (*QColor(PALETTE["STATUS"]["WARNING"]).getRgb()[:3], 30)

        self.graph_current = CustomGraph("Corriente", "A", pen=pen_c, brush=brush_c)
        col_current.addWidget(self.graph_current)

        # Añadir columnas al layout principal
        main_layout.addLayout(col_voltage, 1)
        main_layout.addLayout(col_current, 1)

    # --- Lógica de Paginación del Eje X ---
    def check_and_scroll_xaxis(self, current_time):
        """
        Verifica si el tiempo actual ha superado el límite de la ventana.
        Si es así, desplaza el eje X al siguiente bloque de 15 segundos.
        """
        if current_time > self.current_max_x:
            while current_time > self.current_max_x:
                self.current_max_x += self.window_size

            min_x = self.current_max_x - self.window_size
            max_x = self.current_max_x

            # Aplicar el nuevo rango a AMBAS gráficas
            self.graph_voltage.setXRange(min_x, max_x)
            self.graph_current.setXRange(min_x, max_x)

    # --- Slots de Actualización ---

    @Slot(list, list)
    def update_voltage_graph(self, x_data: list, y_data: list):
        if x_data:
            self.check_and_scroll_xaxis(x_data[-1])
            self.graph_voltage.update_data(x_data, y_data)

    @Slot(list, list)
    def update_current_graph(self, x_data, y_data):
        if x_data:
            self.check_and_scroll_xaxis(x_data[-1])
            self.graph_current.update_data(x_data, y_data)
