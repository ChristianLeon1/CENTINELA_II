#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2026 CREADOR: Ramírez León Christian Yael

# core/config_manager.py
import json
from pathlib import Path

# La ruta donde se guardará el archivo (en la raíz del proyecto)
CONFIG_FILE = Path(__file__).resolve().parent.parent / "config_centinela.json"

DEFAULT_CONFIG = {
    "puerto": "",
    "baudrate": 115200,
    "altitud_inicial": 2240.0,
    "offset_pitch": 0.0,
    "offset_roll": 0.0,
    "offset_yaw": 0.0,
}


def load_config():
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Mezclamos con los defaults por si falta alguna clave en el JSON
            return {**DEFAULT_CONFIG, **data}
    except Exception as e:
        print(f"Error leyendo JSON: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
    except Exception as e:
        print(f"Error guardando JSON: {e}")
