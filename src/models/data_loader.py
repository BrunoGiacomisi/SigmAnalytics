import pandas as pd
import os
from typing import Set

EXPECTED_COLUMNS: Set[str] = {"Ag.transportista", "Nombre Ag.Transportista"}


# -------------------------------------------------------------
# Función que carga el archivo Excel con el manifiesto de viajes y valida columnas
def cargar_manifesto(ruta: str, validar: bool = True) -> pd.DataFrame:
    # Verifica si el archivo existe en la ruta proporcionada
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"Archivo no encontrado en la ruta: {ruta}")

    # Carga del archivo y normalización mínima de nombres de columnas
    df = pd.read_excel(ruta)
    df = df.rename(columns=lambda x: str(x).strip())

    if validar:
        columnas_presentes = set(df.columns)
        if not EXPECTED_COLUMNS.issubset(columnas_presentes):
            faltantes = ", ".join(sorted(EXPECTED_COLUMNS - columnas_presentes))
            raise ValueError(
                f"El archivo no contiene las columnas necesarias. Faltan: {faltantes}"
            )

    return df

