#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2025 CREADOR: Christian Yael Ramírez León

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

# 1. EL DICCIONARIO DE LA PALETA (Cian Técnico)
PALETTE = {
    "BACKGROUND": {
        "MAIN": "#101829",  # Fondo principal
        "PANEL": "#1C2533",  # Fondo de módulos
    },
    "TEXT": {
        "PRIMARY": "#F0F0F0",  # Texto/Datos principales
        "SECONDARY": "#8A9BB1",  # Etiquetas, datos secundarios
        "DISABLED": "#4B5E78",  # Texto/Iconos deshabilitados
    },
    "ACCENT": {
        "ACTIVE": "#00E5FF",  # Cian brillante
        "HOVER": "#7DFFFF",  # Cian más claro (casi blanco)
        "PRESS": "#00B8D4",  # Cian más oscuro/saturado
    },
    "STATUS": {
        "DANGER": "#F44336",  # Rojo - Falla, No-Go
        "WARNING": "#FFEB3B",  # Amarillo - Precaución
        "SUCCESS": "#4CAF50",  # Verde - Éxito, Nominal
        "INFO": "#2196F3",  # Azul - Mensajes
    },
    "BORDER": {
        "DEFAULT": "#2A3B4D",  # Borde de los módulos
        "DIVIDER": "#1C2533",  # Divisores internos
    },
}


# 2. LA FUNCIÓN DE LA PALETA NATIVA (QPalette)
def set_dark_palette(app: QApplication):
    """
    Configura la QPalette base. Esto define los colores
    fundamentales de la aplicación.
    """
    window_color = QColor(PALETTE["BACKGROUND"]["MAIN"])
    panel_color = QColor(PALETTE["BACKGROUND"]["PANEL"])
    text_color = QColor(PALETTE["TEXT"]["PRIMARY"])
    disabled_text_color = QColor(PALETTE["TEXT"]["DISABLED"])
    placeholder_text_color = QColor(PALETTE["TEXT"]["SECONDARY"])
    highlight_color = QColor(PALETTE["ACCENT"]["ACTIVE"])
    border_color = QColor(PALETTE["BORDER"]["DEFAULT"])

    dark_palette = QPalette()

    # Configurar colores para todos los estados (Activo, Inactivo)
    groups = [QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive]
    for group in groups:
        dark_palette.setColor(group, QPalette.Window, window_color)
        dark_palette.setColor(group, QPalette.WindowText, text_color)
        dark_palette.setColor(group, QPalette.Base, panel_color)
        dark_palette.setColor(group, QPalette.AlternateBase, panel_color)
        dark_palette.setColor(group, QPalette.ToolTipBase, panel_color)
        dark_palette.setColor(group, QPalette.ToolTipText, text_color)
        dark_palette.setColor(group, QPalette.Text, text_color)
        dark_palette.setColor(group, QPalette.Button, panel_color)
        dark_palette.setColor(group, QPalette.ButtonText, text_color)
        dark_palette.setColor(group, QPalette.Highlight, highlight_color)
        dark_palette.setColor(
            group, QPalette.HighlightedText, QColor("#000000")
        )  # Texto negro sobre acento
        dark_palette.setColor(group, QPalette.PlaceholderText, placeholder_text_color)
        dark_palette.setColor(group, QPalette.Mid, border_color)

    # Configurar grupo Deshabilitado
    dark_palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.WindowText, disabled_text_color
    )
    dark_palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.Text, disabled_text_color
    )
    dark_palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ButtonText, disabled_text_color
    )
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.Base, panel_color)
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.Button, panel_color)

    app.setPalette(dark_palette)


# 3. LA HOJA DE ESTILO (QSS)
def get_stylesheet(font_family_name: str = "sans-serif") -> str:
    """
    Genera el QSS para complementar la QPalette.
    Esto añade detalles de interacción (hover, bordes, etc.)
    """

    font_family_css = f"'{font_family_name}'"
    return f"""
        QWidget {{
            font-family: {font_family_css}, sans-serif;
            font-size: 10pt;
        }}
        
        QFrame[frameShape="4"], /* HLine */
        QFrame[frameShape="5"] {{ /* VLine */
            color: {PALETTE['BORDER']['DEFAULT']};
        }}

        QToolBar, QStatusBar {{
            background-color: {PALETTE['BACKGROUND']['PANEL']};
            border: none;
        }}

        /* --- Botones --- */
        QPushButton {{
            background-color: {PALETTE['BACKGROUND']['PANEL']};
            color: {PALETTE['TEXT']['PRIMARY']};
            border: 1px solid {PALETTE['BORDER']['DEFAULT']};
            padding: 5px 10px;
            border-radius: 3px;
        }}
        QPushButton:hover {{
            background-color: {PALETTE['ACCENT']['HOVER']};
            color: #000000;
        }}
        QPushButton:pressed {{
            background-color: {PALETTE['ACCENT']['PRESS']};
            color: #000000;
        }}
        
        /* --- Entradas de texto y ComboBox --- */
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {PALETTE['BACKGROUND']['MAIN']};
            border: 1px solid {PALETTE['BORDER']['DEFAULT']};
            border-radius: 3px;
            padding: 5px;
        }}
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border-color: {PALETTE['ACCENT']['ACTIVE']};
        }}
        
        /* --- QComboBox (Menú) --- */
        QComboBox QAbstractItemView {{
            background-color: {PALETTE['BACKGROUND']['PANEL']};
            color: {PALETTE['TEXT']['PRIMARY']};
            border: 1px solid {PALETTE['BORDER']['DEFAULT']};
            selection-background-color: {PALETTE['ACCENT']['ACTIVE']};
            selection-color: #000000;
        }}
        
        /* --- QTabWidget --- */
        QTabWidget::pane {{
            border: 1px solid {PALETTE['BORDER']['DEFAULT']};
            border-top: none;
        }}
        QTabBar::tab {{
            background-color: {PALETTE['BACKGROUND']['PANEL']};
            color: {PALETTE['TEXT']['SECONDARY']};
            border: 1px solid {PALETTE['BORDER']['DEFAULT']};
            border-bottom: none;
            padding: 8px 15px;
        }}
        QTabBar::tab:hover {{
            color: {PALETTE['TEXT']['PRIMARY']};
        }}
        QTabBar::tab:selected {{
            color: {PALETTE['ACCENT']['ACTIVE']};
            background-color: {PALETTE['BACKGROUND']['MAIN']};
            border-bottom: 2px solid {PALETTE['ACCENT']['ACTIVE']};
        }}
    """
