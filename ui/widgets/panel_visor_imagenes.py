#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ui/widgets/panel_visor_imagenes.py

import os
from datetime import datetime

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from ui.theme import PALETTE

# ui/widgets/panel_inferior_imagenes.py


class PanelVisorImagenes(QFrame):
    def __init__(self, parent=None, esp32_ip="192.168.1.100"):
        super().__init__(parent)
        self.setProperty("isPanel", True)

        # Crear directorio de guardado si no existe
        self.save_dir = "capturas_estereoscopia"
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Controles superiores para cambiar la IP al vuelo
        top_layout = QHBoxLayout()
        self.input_ip = QLineEdit(esp32_ip)
        self.input_ip.setStyleSheet(
            f"background-color: {PALETTE['BACKGROUND']['MAIN']}; "
            f"color: {PALETTE['TEXT']['PRIMARY']}; "
            f"border: 1px solid {PALETTE['BORDER']['DEFAULT']}; padding: 5px;"
        )

        btn_conectar = QPushButton("Conectar")
        btn_conectar.setStyleSheet(
            f"background-color: {PALETTE['BACKGROUND']['MAIN']}; "
            f"color: {PALETTE['ACCENT']['ACTIVE']}; font-weight: bold; "
            f"padding: 5px; border: 1px solid {PALETTE['ACCENT']['ACTIVE']};"
        )
        btn_conectar.clicked.connect(self.actualizar_conexion)

        label_ip = QLabel("IP ESP32:")
        label_ip.setStyleSheet(f"color: {PALETTE['TEXT']['SECONDARY']};")

        top_layout.addWidget(label_ip)
        top_layout.addWidget(self.input_ip)
        top_layout.addWidget(btn_conectar)
        layout.addLayout(top_layout)

        # Webview incrustado para mostrar el stream
        self.webview = QWebEngineView()
        self.webview.setStyleSheet(
            f"background-color: {PALETTE['BACKGROUND']['MAIN']}; "
            f"border: 1px solid {PALETTE['BORDER']['DEFAULT']};"
        )
        layout.addWidget(self.webview, 1)

        # Label de estado
        self.label_estado = QLabel("Listo para conectar.")
        self.label_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_estado.setStyleSheet(
            f"color: {PALETTE['TEXT']['SECONDARY']}; font-size: 9pt;"
        )
        layout.addWidget(self.label_estado)

        # Conectar al iniciar el panel
        self.actualizar_conexion()

    def actualizar_conexion(self):
        """Actualiza la URL del webview basándose en la IP ingresada."""
        ip = self.input_ip.text().strip()
        self.web_url = f"https://{ip}"

        self.label_estado.setText(f"Cargando {self.web_url} ...")
        self.webview.setUrl(QUrl(self.web_url))

    def guardar_imagen(self):
        """
        Toma una captura del webview y la guarda.
        Puede ser invocada externamente por un botón principal o un atajo global de la UI.
        Retorna: (bool éxito, str ruta_o_mensaje)
        """
        try:
            # 1. Generar el nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = os.path.join(
                self.save_dir, f"imagen_estereoscopia_{timestamp}.jpg"
            )

            # 2. Tomar captura directa
            pixmap = self.webview.grab()

            # 3. Guardar en disco
            if pixmap.save(filename, "JPG", quality=100):
                self.label_estado.setText(
                    f"Guardado rápido: {os.path.basename(filename)}"
                )
                return True, filename
            else:
                self.label_estado.setText("Error: No se pudo guardar la captura.")
                return False, "Error interno al guardar la imagen."

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.label_estado.setText(error_msg)
            return False, error_msg
