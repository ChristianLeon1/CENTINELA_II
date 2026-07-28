#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2026 CREADOR: Christian Yael Ramírez León

import pyqtgraph as pg
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from ui.theme import PALETTE

pg.setConfigOption("background", None)
pg.setConfigOption("foreground", PALETTE["TEXT"]["SECONDARY"])
pg.setConfigOption("antialias", True)


class PanelCalidadAire(QFrame):
    """
    Panel modificado para mostrar Presión y Temperatura
    con paginación automática del eje X cada 15 segundos.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("isPanel", True)

        # --- VARIABLES PARA LA PAGINACIÓN (SCROLL) ---
        self.current_max_x = 15.0  # Límite actual
        self.window_size = 15.0  # Tamaño de ventana
        # --------------------------------------------

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(10)

        main_layout.addWidget(container_widget)

        titulo = QLabel("Presión y Temperatura")
        titulo.setProperty("isTitulo", True)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(titulo)

        # --- 1. Gráfica Superior (Presión) ---
        self.plot_presion = pg.PlotWidget()
        self.plot_presion.showGrid(x=True, y=True, alpha=0.3)
        self.plot_presion.setLabel("left", "Presión", units="Pa")
        self.plot_presion.setLabel("bottom", "Tiempo", units="s")
        self.plot_presion.getPlotItem().setMenuEnabled(False)

        self.plot_presion.setXRange(0, 15)
        self.plot_presion.setMouseEnabled(x=False, y=True)

        pen_pres = pg.mkPen(PALETTE["ACCENT"]["ACTIVE"], width=2)
        brush_pres = (*QColor(PALETTE["ACCENT"]["ACTIVE"]).getRgb()[:3], 50)

        self.line_presion = self.plot_presion.plot(
            pen=pen_pres, fillLevel=0, brush=brush_pres, name="Presión"
        )
        container_layout.addWidget(self.plot_presion, 1)

        # --- 2. Gráfica Inferior (Temperatura) ---
        self.plot_temp = pg.PlotWidget()
        self.plot_temp.showGrid(x=True, y=True, alpha=0.3)
        self.plot_temp.setLabel("left", "Temperatura", units="°C")
        self.plot_temp.setLabel("bottom", "Tiempo", units="s")
        self.plot_temp.getPlotItem().setMenuEnabled(False)

        self.plot_temp.setXRange(0, 15)
        self.plot_temp.setMouseEnabled(x=False, y=True)

        pen_temp = pg.mkPen(PALETTE["STATUS"]["WARNING"], width=2)
        brush_temp = (*QColor(PALETTE["STATUS"]["WARNING"]).getRgb()[:3], 50)

        self.line_temp = self.plot_temp.plot(
            pen=pen_temp, fillLevel=0, brush=brush_temp, name="Temperatura"
        )
        container_layout.addWidget(self.plot_temp, 1)

    # --- Lógica de Paginación del Eje X ---
    def check_and_scroll_xaxis(self, current_time):
        if current_time > self.current_max_x:
            while current_time > self.current_max_x:
                self.current_max_x += self.window_size

            min_x = self.current_max_x - self.window_size
            max_x = self.current_max_x

            self.plot_presion.setXRange(min_x, max_x)
            self.plot_temp.setXRange(min_x, max_x)

    # --- SLOTS DE ACTUALIZACIÓN ---
    @Slot(list, list)
    def update_pressure_graph(self, x_data: list, pres_data: list):
        if x_data:
            self.check_and_scroll_xaxis(x_data[-1])
            self.line_presion.setData(x_data, pres_data)

    @Slot(list, list)
    def update_temp_graph(self, x_data: list, temp_data: list):
        if x_data:
            self.check_and_scroll_xaxis(x_data[-1])
            self.line_temp.setData(x_data, temp_data)
