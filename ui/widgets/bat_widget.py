#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2026 CREADOR: Ramírez León Christian Yael

import sys

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ui.theme import PALETTE


class BatteryIconWidget(QWidget):
    """Widget que dibuja el icono de batería utilizando la paleta de colores."""

    def __init__(self, parent=None, percentage=84):
        super().__init__(parent)
        self._percentage = max(0, min(100, percentage))
        self.setFixedSize(65, 120)

    def setPercentage(self, percentage):
        self._percentage = max(0, min(100, percentage))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        corner_radius = 12
        terminal_w = w * 0.3
        terminal_h = h * 0.08
        terminal_r = 4

        # Definir colores desde la paleta
        outline_color = QColor(PALETTE["TEXT"]["SECONDARY"])

        # Color dinámico basado en el nivel de batería usando la paleta STATUS/ACCENT
        if self._percentage <= 20:
            fill_color = QColor(PALETTE["STATUS"]["DANGER"])
        elif self._percentage <= 50:
            fill_color = QColor(PALETTE["STATUS"]["WARNING"])
        else:
            fill_color = QColor(PALETTE["ACCENT"]["ACTIVE"])

        # 1. Dibujar el terminal superior
        terminal_rect = QPointF((w - terminal_w) / 2, 0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(outline_color)
        painter.drawRoundedRect(
            terminal_rect.x(),
            terminal_rect.y(),
            terminal_w,
            terminal_h,
            terminal_r,
            terminal_r,
        )

        # 2. Dibujar el contorno del cuerpo
        body_y = terminal_h
        body_h = h - terminal_h
        painter.setPen(QPen(outline_color, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(0, body_y, w, body_h, corner_radius, corner_radius)

        # 3. Dibujar el relleno de la batería
        padding = 4
        fill_area_y = body_y + padding
        fill_area_h = body_h - (2 * padding)
        fill_h = (self._percentage / 100.0) * fill_area_h
        fill_y = fill_area_y + (fill_area_h - fill_h)

        painter.setPen(Qt.NoPen)
        painter.setBrush(fill_color)
        painter.drawRoundedRect(
            padding,
            fill_y,
            w - (2 * padding),
            fill_h,
            corner_radius - (padding / 2),
            corner_radius - (padding / 2),
        )


class BatteryWidget(QFrame):
    """Módulo principal del widget usando BACKGROUND.PANEL."""

    def __init__(self, parent=None, percentage=84):
        super().__init__(parent)
        self.setObjectName("BatteryWidget")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)

        # --- Parte izquierda: Icono ---
        self.battery_icon = BatteryIconWidget(self, percentage)
        main_layout.addWidget(self.battery_icon, 0, Qt.AlignCenter)

        # --- Parte derecha: Información de texto ---
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)
        info_layout.setAlignment(Qt.AlignCenter)

        # Número de porcentaje (PRIMARY)
        self.pct_num_label = QLabel(str(percentage), self)
        self.pct_num_label.setFont(QFont("Segoe UI", 48, QFont.Bold))
        self.pct_num_label.setStyleSheet(f"color: {PALETTE['TEXT']['PRIMARY']};")
        self.pct_num_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.pct_num_label)

        # Símbolo % (SECONDARY)
        self.pct_sym_label = QLabel("%", self)
        self.pct_sym_label.setFont(QFont("Segoe UI", 28, QFont.Light))
        self.pct_sym_label.setStyleSheet(
            f"color: {PALETTE['TEXT']['SECONDARY']}; margin-top: -10px;"
        )
        self.pct_sym_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.pct_sym_label)

        main_layout.addLayout(info_layout, 1)

        # Estilo de tarjeta aplicando BACKGROUND.PANEL y BORDER.DEFAULT
        self.setStyleSheet(
            f"""
            #BatteryWidget {{
                background-color: {PALETTE['BACKGROUND']['PANEL']};
                border: 2px solid {PALETTE['BORDER']['DEFAULT']};
                border-radius: 20px;
            }}
        """
        )

    def setPercentage(self, percentage):
        self.battery_icon.setPercentage(percentage)
        self.pct_num_label.setText(str(percentage))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Widget de Batería - Dark Theme")
        self.resize(450, 350)

        main_vbox = QVBoxLayout(self)

        # Centrar el widget
        battery_container = QHBoxLayout()
        battery_container.setAlignment(Qt.AlignCenter)
        self.battery_widget = BatteryWidget(self)
        battery_container.addWidget(self.battery_widget)
        main_vbox.addLayout(battery_container, 1)

        # Controles (Deslizador)
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(20, 20, 20, 20)

        # Etiqueta del control adaptada para verse en fondo oscuro
        slider_label = QLabel("Nivel de Batería:")
        slider_label.setStyleSheet(
            f"color: {PALETTE['TEXT']['SECONDARY']}; font-weight: bold;"
        )

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(84)
        self.slider.valueChanged.connect(self.battery_widget.setPercentage)

        controls_layout.addWidget(slider_label)
        controls_layout.addWidget(self.slider)

        main_vbox.addLayout(controls_layout, 0)

        # Fondo principal de la ventana usando BACKGROUND.MAIN
        self.setStyleSheet(f"background-color: {PALETTE['BACKGROUND']['MAIN']};")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
