#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2025 CREADOR: Christian Yael Ramírez León

# ui/widgets/panel_cinematica.py

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from ui.widgets.compass_widget import Compass
from ui.widgets.gaugemeter import ModernSpeedometer


class PanelCinematica(QFrame):
    """
    Panel de cinemática para el visor 3D.
    Muestra Aceleración, Velocidad y una Brújula con sus respectivas etiquetas.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("isPanel", True)

        # Aumentamos un poco la altura para dar espacio a los textos inferiores
        self.setFixedHeight(200)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(10)

        # Instanciamos los medidores
        self.velocimeter = ModernSpeedometer(max_value=100, unit="m/s", steps=10)
        self.acc_x = ModernSpeedometer(max_value=20, unit="m/s²", steps=5)
        self.acc_y = ModernSpeedometer(max_value=20, unit="m/s²", steps=5)
        self.acc_z = ModernSpeedometer(max_value=20, unit="m/s²", steps=5)
        self.compass = Compass()

        # Agregamos cada indicador con su respectiva etiqueta usando un método auxiliar
        main_layout.addLayout(
            self._create_instrument_column(self.velocimeter, "Velocidad"), 1
        )
        main_layout.addLayout(self._create_instrument_column(self.acc_x, "Acel. X"), 1)
        main_layout.addLayout(self._create_instrument_column(self.acc_y, "Acel. Y"), 1)
        main_layout.addLayout(self._create_instrument_column(self.acc_z, "Acel. Z"), 1)
        main_layout.addLayout(
            self._create_instrument_column(self.compass, "Brújula"), 1
        )

    def _create_instrument_column(self, widget, label_text):
        """
        Crea un layout vertical que contiene el medidor y su etiqueta centrada debajo.
        """
        col_layout = QVBoxLayout()
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.setSpacing(5)

        # Etiqueta descriptiva
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)

        # Opcional: Estilo de la fuente para que se integre bien con el panel (Ajusta los colores a tu gusto)
        label.setStyleSheet("font-size: 11px; font-weight: bold; color: palette(text);")

        # El widget ocupa la mayor parte del espacio (stretch=1), el label ocupa solo lo necesario (stretch=0)
        col_layout.addWidget(widget, 1)
        col_layout.addWidget(label, 0)

        return col_layout

    @Slot(dict)
    def update_cinematica(self, data: dict):
        """
        Slot público para recibir datos de cinemática y actualizar la UI.
        """
        if "ax" in data:
            val_ax = data["ax"]
            self.acc_x.set_value(abs(val_ax))

        if "ay" in data:
            val_ay = data["ay"]
            self.acc_y.set_value(abs(val_ay))

        if "az" in data:
            val_az = data["az"]
            self.acc_z.set_value(abs(val_az))

        if "vel" in data:
            val_vel = data["vel"]
            self.velocimeter.set_value(abs(val_vel))

        if "yaw" in data:
            val_yaw = int(data["yaw"])
            val_yaw = val_yaw % 360
            self.compass.set_heading(val_yaw)
