#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from PySide6.QtCore import QObject, Qt, QUrl, Slot
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import QFrame, QVBoxLayout

from core.config_manager import load_config  # <-- Para leer el JSON
from ui.theme import PALETTE

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class PanelVisor3D(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("isPanel", True)
        self.setMinimumHeight(300)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- MOTOR QT QUICK 3D ---
        self.qml_widget = QQuickWidget()
        self.qml_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

        ruta_qml = str(BASE_DIR / "ui" / "widgets" / "visor3d.qml")
        ruta_glb = str(BASE_DIR / "models" / "CANSAT.glb")

        self.qml_widget.setSource(QUrl.fromLocalFile(ruta_qml))

        url_glb = QUrl.fromLocalFile(ruta_glb).toString()

        root = self.qml_widget.rootObject()
        if root:
            root.setProperty("modeloUrl", url_glb)
            root.modeloCargado.connect(self.activar_animacion_cierre)

            # --- APLICAMOS LOS MAPEOS DEL JSON AUTOMÁTICAMENTE ---
            self._cargar_y_aplicar_mapeos()

        main_layout.addWidget(self.qml_widget, 1)

    def _cargar_y_aplicar_mapeos(self):
        """
        Lee los mapeos, offsets y flags de inversión del JSON
        y los inyecta en el entorno QML.
        """
        root = self.qml_widget.rootObject()
        if not root:
            return

        config = load_config()

        # Inyectamos offsets
        root.setProperty("offset_pitch", config.get("offset_pitch", 0.0))
        root.setProperty("offset_roll", config.get("offset_roll", 0.0))
        root.setProperty("offset_yaw", config.get("offset_yaw", 0.0))

        # Inyectamos Mapeos (Qué eje del acelerómetro mueve qué eje del modelo)
        # Asegúrate de que en tu visor3d.qml tengas declaradas estas properties como "string"
        root.setProperty("map_pitch", config.get("map_pitch", "X"))
        root.setProperty("map_roll", config.get("map_roll", "Y"))
        root.setProperty("map_yaw", config.get("map_yaw", "Z"))

        # Inyectamos Inversiones
        # Asegúrate de que en tu visor3d.qml tengas declaradas estas properties como "bool"
        root.setProperty("invert_pitch", config.get("invert_pitch", False))
        root.setProperty("invert_roll", config.get("invert_roll", False))
        root.setProperty("invert_yaw", config.get("invert_yaw", False))

    # --- MÉTODO MEJORADO PARA LA ANIMACIÓN ---
    @Slot()
    def activar_animacion_cierre(self):
        root = self.qml_widget.rootObject()
        if not root:
            return

        print("[3D] Inspeccionando animaciones del CanSat...")
        animacion_objetivo = None

        # Recorremos todos los objetos hijos del entorno 3D
        for child in root.findChildren(QObject):
            nombre = child.objectName()

            if nombre:
                if child.property("running") is not None:
                    print(f" -> Animación detectada en GLB: '{nombre}'")
                    child.setProperty("running", False)

                    if "cierre" in nombre.lower():
                        animacion_objetivo = child

        if animacion_objetivo:
            print(
                f"[3D] ¡Iniciando animación correcta: '{animacion_objetivo.objectName()}'!"
            )
            animacion_objetivo.setProperty("running", True)
        else:
            print(
                "[3D] ADVERTENCIA: No se encontró ninguna animación que contenga 'Cierre'."
            )

    # --- ACTUALIZADO PARA CUATERNIONES ---
    @Slot(float, float, float, float)
    def update_orientation(self, q0: float, q1: float, q2: float, q3: float):
        """
        Actualiza la rotación del modelo inyectando los cuaterniones al QML.
        q0 = w (real), q1 = x, q2 = y, q3 = z (imaginarios).
        """
        root = self.qml_widget.rootObject()
        if root:
            root.setProperty("q_w", q0)
            root.setProperty("q_x", q1)
            root.setProperty("q_y", q2)
            root.setProperty("q_z", q3)

    @Slot(float)
    def update_altura(self, altitud: float):
        """
        Actualiza la posición del piso (Grid) para simular cambios de altitud.
        """
        root = self.qml_widget.rootObject()
        if root:
            root.setProperty("altura", altitud * 10)

    @Slot(float, float, float)
    def aplicar_offsets_calibracion(self, pitch: float, roll: float, yaw: float):
        """
        Permite actualizar los offsets en vivo desde la ventana de configuración.
        """
        root = self.qml_widget.rootObject()
        if root:
            root.setProperty("offset_pitch", pitch)
            root.setProperty("offset_roll", roll)
            root.setProperty("offset_yaw", yaw)
