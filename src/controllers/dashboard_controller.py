from __future__ import annotations

from typing import Optional, Dict, Any, Tuple, List

import pandas as pd
from tkinter import filedialog

from src.models.data_loader import cargar_manifesto
from src.models import db as db_model
from src import main as main_module


def select_manifest_file() -> str:
    # Abre el diálogo de selección de archivo y devuelve la ruta (o cadena vacía si se canceló)
    return filedialog.askopenfilename(
        title="Seleccionar manifiesto",
        filetypes=[["Archivos Excel", "*.xlsx *.xls"]],
    )


def validate_and_load_manifest(file_path: str) -> pd.DataFrame:
    # Carga y valida el manifiesto usando la función centralizada
    return cargar_manifesto(file_path, validar=True)


def process_manifest(file_path: str, codigos_representados: List[str], df: Optional[pd.DataFrame] = None) -> Tuple[float, float, float, float, float, bool, int, str, str, bool]:
    # Ejecuta el procesamiento con ruta o con un DataFrame ya cargado para evitar doble IO
    if df is not None:
        return main_module.procesar_df(df, codigos_representados)
    return main_module.procesar_archivo(file_path, codigos_representados)


def compute_period(df: pd.DataFrame, fecha_columna: str = "Fecha ingreso") -> Optional[str]:
    # Intenta obtener el período (YYYY-MM) a partir de un DataFrame ya cargado
    try:
        return db_model.obtener_periodo_desde_df(df, fecha_columna)
    except Exception:
        return None


