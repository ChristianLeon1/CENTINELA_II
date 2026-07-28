#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2025 CREADOR: Christian Yael Ramírez León

# ui/widgets/panel_estados.py

from PySide6.QtCore import QSize, Qt, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from ui.theme import PALETTE


# --- 1. El Widget Reutilizable para el LED ---
class LedIndicator(QWidget):
    """
    Un widget simple que muestra un círculo (LED)
    y una etiqueta de texto debajo. NO es clicable.
    Ahora con un degradado radial.
    """

    def __init__(self, text: str, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.led = QWidget()
        self.led.setFixedSize(25, 25)

        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.led, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.set_active(False)

    def set_active(self, active: bool):
        """
        Cambia el color del LED con un degradado radial.
        """

        if active:
            # Colores para el degradado VERDE
            color_center = "#8BC34A"  # Verde más claro para el centro
            color_edge = "#4CAF50"  # Verde más oscuro para el borde
        else:
            # Colores para el degradado ROJO
            color_center = "#E45349"  # Rojo más claro para el centro
            color_edge = "#8E1D15"  # Rojo más oscuro para el borde

        self.led.setStyleSheet(
            f"""
            QWidget {{
                /* Degradado Radial: desde el centro hacia afuera */
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 0.8, fx: 0.5, fy: 0.5, 
                    stop: 0 {color_center}, 
                    stop: 1 {color_edge}
                );
                border-radius: 12px; /* Ajustado a casi la mitad de 25 para un círculo perfecto */
            }}
        """
        )


# --- 2. El Panel de Estados Principal ---
class PanelEstados(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("isPanel", True)

        main_layout = QVBoxLayout(self)

        # 1. Título "ESTADOS"
        label_titulo = QLabel("ESTADOS")
        label_titulo.setProperty("isTitulo", True)  # Usa el estilo del QSS
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label_titulo)

        # 2. Grid de LEDs (Ajustado a 3 estados en una sola fila)
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(20, 10, 20, 10)
        grid_layout.setSpacing(25)

        # --- LOS 3 ESTADOS SOLICITADOS ---
        self.led_ahorro = LedIndicator("Ahorro de\nEnergía")
        self.led_sd = LedIndicator("Micro SD")
        self.led_autogiro = LedIndicator("Autogiro")

        grid_layout.addWidget(self.led_ahorro, 0, 0, Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.led_sd, 0, 1, Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.led_autogiro, 0, 2, Qt.AlignmentFlag.AlignCenter)

        main_layout.addLayout(grid_layout)

        # --- --- --- --- --- --- --- ---
        # --- WIDGET DE ETAPA DE MISIÓN ---
        # --- --- --- --- --- --- --- ---

        # Espacio entre los LEDs y la etapa
        main_layout.addSpacing(50)

        # 3. Etiqueta de Título para la Etapa
        label_titulo_etapa = QLabel("Etapa de lanzamiento:")
        main_layout.addSpacing(30)
        label_titulo_etapa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_titulo_etapa.setStyleSheet("font-weight: bold; font-size: 14;")
        main_layout.addWidget(label_titulo_etapa)

        # 4. Recuadro de color para la Etapa
        self.label_etapa_mision = QLabel("EN ESPERA")
        self.label_etapa_mision.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Estilo inicial
        self.label_etapa_mision.setStyleSheet(
            f"""
            QLabel {{
                background-color: {PALETTE['BACKGROUND']['MAIN']};
                color: {PALETTE['TEXT']['PRIMARY']};
                font-weight: bold;
                border: 1px solid {PALETTE['BORDER']['DEFAULT']};
                border-radius: 4px;
            }}
        """
        )
        main_layout.addSpacing(30)
        main_layout.addWidget(self.label_etapa_mision)
        # --- --- --- --- --- --- --- ---

        # Espacio flexible al final para empujar todo hacia arriba
        main_layout.addStretch(1)

    @Slot(dict)
    def update_data(self, data: dict):
        """
        Slot público para actualizar los LEDs Y la etapa de la misión.
        """

        # --- 1. Lógica de LEDs (Mapeados a los datos seriales existentes) ---
        if "carga1" in data:
            self.led_ahorro.set_active(data["carga1"])

        if "sd" in data:
            self.led_sd.set_active(data["sd"])

        if "carga2" in data:
            self.led_autogiro.set_active(data["carga2"])

        # --- 2. Lógica de Etapa de Misión (INTACTA) ---
        if "etapa" in data:
            etapa_texto = data["etapa"].upper()
            color = PALETTE["BACKGROUND"]["MAIN"]
            texto_color = PALETTE["TEXT"]["PRIMARY"]

            if etapa_texto == "LANZAMIENTO":
                color = PALETTE["STATUS"]["DANGER"]
                texto_color = "black"
            elif etapa_texto == "ASCENSO":
                color = PALETTE["STATUS"]["WARNING"]
                texto_color = "black"
            elif etapa_texto == "APOGEO":
                color = PALETTE["ACCENT"]["ACTIVE"]
                texto_color = "black"
            elif etapa_texto == "RECUPERACION":
                color = PALETTE["STATUS"]["SUCCESS"]
                texto_color = "black"
            elif etapa_texto == "EN ESPERA":
                color = PALETTE["BACKGROUND"]["MAIN"]
                texto_color = PALETTE["TEXT"]["PRIMARY"]

            # Actualizar el texto del RECUADRO
            self.label_etapa_mision.setText(f"{etapa_texto}")

            # Actualizar el estilo
            self.label_etapa_mision.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {color};
                    color: {texto_color};
                    font-weight: bold;
                    border: 1px solid {color if etapa_texto != "EN ESPERA" else PALETTE['BORDER']['DEFAULT']};
                    border-radius: 4px;
                }}
            """
            )
