#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2026 CREADOR: Ramírez León Christian Yael

import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPixmap, QQuaternion
from PySide6.QtWidgets import QApplication, QDialog, QSplashScreen

from core.serial_worker import SerialWorker
from ui.config_dialog import ConfigDialog
from ui.main_window import GroundStation
from ui.theme import PALETTE, get_stylesheet, set_dark_palette

os.environ["QT_QPA_PLATFORM"] = "xcb"
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

# --- 1. FORZAR GPU DEDICADA (PRIME OFFLOADING) ---
# Si tienes NVIDIA (Controladores propietarios):
# os.environ["__NV_PRIME_RENDER_OFFLOAD"] = "1"
# os.environ["__GLX_VENDOR_LIBRARY_NAME"] = "nvidia"

# Si tienes AMD (Controladores libres AMDGPU):
os.environ["DRI_PRIME"] = "1"

# --- 2. FORZAR ACELERACIÓN EN EL MAPA (QtWebEngine/Chromium) ---
# Chromium suele bloquear GPUs en Linux por precaución. Esto lo fuerza a usarla.
sys.argv.extend(
    ["--ignore-gpu-blocklist", "--enable-gpu-rasterization", "--enable-zero-copy"]
)

# --- 3. BACKEND DE RENDERIZADO PARA EL 3D ---
# Opcional: Si experimentas parpadeos en Wayland/Hyprland con el modelo 3D
os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"
os.environ["QSG_INFO"] = "1"  # Imprime en consola qué GPU está usando QtQuick3D

# (Aquí continúa tu código normal)
# app = QApplication(sys.argv)
# ...


def main():
    app = QApplication(sys.argv)
    BASE_DIR = Path(__file__).resolve().parent

    # ==========================================================
    # FASE 1: PANTALLA DE CARGA INICIAL (SPLASH SCREEN)
    # ==========================================================
    splash_pix = QPixmap(500, 300)
    splash_pix.fill(QColor("#101829"))

    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()
    splash.showMessage(
        "Iniciando subsistemas y cargando componentes...\nCENTINELA I",
        Qt.AlignBottom | Qt.AlignCenter,
        Qt.white,
    )

    app.processEvents()

    # Carga de recursos pesados del sistema (Estilos y Fuentes)
    app.setStyle("Fusion")
    font_path = BASE_DIR / "Gotham-Book.otf"
    font_id = QFontDatabase.addApplicationFont(str(font_path))

    if font_id == -1:
        print(f"Aviso: No se pudo cargar '{font_path}'. Usando fuente por defecto.")
        family_name = "sans-serif"
    else:
        family_name = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(family_name, 10))
        print(f"Fuente '{family_name}' cargada correctamente.")

    set_dark_palette(app)
    app.setStyleSheet(get_stylesheet(family_name))

    # ==========================================================
    # INSTANCIACIÓN DE CORE (Hilos y Lógica Serial)
    # ==========================================================
    serial_thread = QThread()
    serial_worker = SerialWorker()
    serial_worker.moveToThread(serial_thread)
    serial_thread.started.connect(serial_worker.init_worker)
    # serial_thread.start()

    # ==========================================================
    # FASE 2: VENTANA DE CONFIGURACIÓN Y PRE-FLIGHT CHECK
    # ==========================================================
    dialogo = ConfigDialog()

    # ruta_qml = str(BASE_DIR / "ui" / "widgets" / "visor3d.qml")
    ruta_glb = QUrl.fromLocalFile(str(BASE_DIR / "models" / "CANSAT.glb")).toString()
    # dialogo.preview_3d.setSource(QUrl.fromLocalFile(ruta_qml))

    # --- PUENTE SEGURO (DIALOG BRIDGE) ---
    class DialogBridge(QObject):
        req_connect = Signal(str, int)
        req_disconnect = Signal()

        @Slot(float, float, float, float)
        def update_3d(self, q0, q1, q2, q3):
            if dialogo.preview_3d.rootObject():
                dialogo.preview_3d.rootObject().setProperty(
                    "rotation", QQuaternion(q0, q1, q2, q3)
                )

        @Slot(str, str)
        def update_status(self, msg, cat):
            # 1. Siempre actualiza el monitor del diálogo
            dialogo.update_monitor(f"[{cat.upper()}]: {msg}")

            # 2. Si la ventana principal ya existe, actualiza su Toolbar
            if bridge.main_window and hasattr(
                bridge.main_window, "on_connection_status"
            ):
                bridge.main_window.on_connection_status(f"[{cat.upper()}]: {msg}", cat)

    bridge = DialogBridge()
    bridge.main_window = None

    # 1. Conexiones UI -> Worker (Forzando la cola para evitar Segfault)
    bridge.req_connect.connect(serial_worker.start_connection, Qt.QueuedConnection)
    bridge.req_disconnect.connect(serial_worker.stop_connection, Qt.QueuedConnection)

    dialogo.btn_test.clicked.connect(
        lambda: bridge.req_connect.emit(
            dialogo.cb_port.currentText(), int(dialogo.cb_baud.currentText())
        )
    )

    # 2. Conexiones Worker -> UI (Hacia los Slots seguros del Bridge y el Diálogo)
    serial_worker.visor_3d_updated.connect(bridge.update_3d)
    serial_worker.status_update.connect(bridge.update_status)

    # ¡NUEVO! Conexión directa y limpia de los puertos al diálogo

    serial_worker.port_list_updated.connect(dialogo.actualizar_lista_puertos)
    serial_thread.start()
    splash.finish(dialogo)

    # Lanzamos el diálogo; si es cancelado (X o Cancelar), salimos limpiamente
    if dialogo.exec() != QDialog.Accepted:
        bridge.req_disconnect.emit()
        serial_thread.quit()
        serial_thread.wait(500)
        sys.exit(0)

    configuracion = dialogo.config_data

    # Desconexión limpia de las señales temporales de la Fase 2
    try:
        serial_worker.visor_3d_updated.disconnect(bridge.update_3d)
        serial_worker.status_update.disconnect(bridge.update_status)
        serial_worker.port_list_updated.disconnect(dialogo.actualizar_lista_puertos)
        dialogo.btn_test.clicked.disconnect()
    except Exception:
        pass

    # ==========================================================
    # FASE 3: INICIALIZACIÓN DE LA ESTACIÓN TERRENA (MAIN WINDOW)
    # ==========================================================
    window = GroundStation()
    bridge.main_window = window

    # Inyectamos los offsets de calibración aprobados en pre-vuelo
    if hasattr(window, "panel_visor_3d"):
        window.panel_visor_3d.aplicar_offsets_calibracion(
            configuracion.get("offset_pitch", 0.0),
            configuracion.get("offset_roll", 0.0),
            configuracion.get("offset_yaw", 0.0),
        )

    # --- SEÑALES WORKER -> UI ---
    # serial_worker.status_update.connect(window.on_connection_status)
    serial_worker.cinematica_updated.connect(window.on_cinematica_updated)
    serial_worker.visor_3d_updated.connect(window.on_visor_3d_updated)
    serial_worker.gps_data_updated.connect(window.on_gps_data_updated)
    serial_worker.altimetro_data_updated.connect(window.on_altimetro_data_updated)
    serial_worker.graficas_data_updated.connect(window.on_graficas_data_updated)
    serial_worker.calidad_aire_updated.connect(window.on_calidad_aire_updated)
    serial_worker.baterias_data_updated.connect(window.on_baterias_data_updated)
    serial_worker.paquetes_data_updated.connect(window.on_paquetes_data_updated)
    serial_worker.estados_data_updated.connect(window.on_estados_data_updated)

    # --- SEÑALES UI -> WORKER (Forzando la cola) ---
    window.actualizar_puertos_solicitado.connect(
        serial_worker.check_available_ports, Qt.QueuedConnection
    )
    window.conexion_solicitada.connect(
        serial_worker.start_connection, Qt.QueuedConnection
    )
    window.desconexion_solicitada.connect(
        serial_worker.stop_connection, Qt.QueuedConnection
    )
    window.comando_solicitado.connect(
        serial_worker.send_command_sequence, Qt.QueuedConnection
    )
    window.simulacion_solicitada.connect(
        serial_worker.run_simulation, Qt.QueuedConnection
    )

    # ==========================================================
    # DISPARO AUTOMÁTICO DE MISIÓN / SIMULACIÓN
    # ==========================================================
    if configuracion.get("is_simulation", False):
        archivo_sim = configuracion.get(
            "archivo_simulacion", "telemetria_esfm_ordenada.csv"
        )
        print(
            "[SISTEMA] Modo Simulación activo. Esperando 10 segundos para iniciar flujo de datos..."
        )
        QTimer.singleShot(10000, lambda: window.simulacion_solicitada.emit(archivo_sim))
    else:
        if configuracion.get("puerto"):
            QTimer.singleShot(
                1000,
                lambda: window.conexion_solicitada.emit(
                    configuracion["puerto"], int(configuracion["baudrate"])
                ),
            )

    # --- CIERRE SEGURO DEL SISTEMA (Botón X) ---
    app.aboutToQuit.connect(window.desconexion_solicitada.emit)
    app.aboutToQuit.connect(serial_thread.quit)
    app.aboutToQuit.connect(lambda: serial_thread.wait(1000))

    serial_thread.finished.connect(serial_worker.deleteLater)
    serial_thread.finished.connect(serial_thread.deleteLater)

    window.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
