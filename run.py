#!/usr/bin/env python3
"""
Script de entrada para SigmAnalytics
Uso: python run.py
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path de Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.views.dashboard import crear_dashboard
    crear_dashboard()
except ImportError as e:
    print(f"Error de importación: {e}")
    print("Asegúrate de que todas las dependencias estén instaladas.")
    print("Ejecuta: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error al ejecutar la aplicación: {e}")
    sys.exit(1)
