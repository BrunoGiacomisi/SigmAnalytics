import pandas as pd
import os
from typing import Set, Dict

# Columnas esperadas y sus posibles variaciones
EXPECTED_COLUMNS_MAP: Dict[str, Set[str]] = {
    "Ag.transportista": {
        "Ag.transportista", "Ag transportista", "Agente transportista", 
        "Codigo transportista", "Código transportista", "Transportista"
    },
    "Nombre Ag.Transportista": {
        "Nombre Ag.Transportista", "Nombre Ag Transportista", 
        "Nombre Agente Transportista", "Nombre transportista", "Transportista"
    }
}


def _normalize_column_name(col_name: str) -> str:
    """Normaliza nombres de columnas para buscar coincidencias"""
    return str(col_name).strip().lower().replace(".", "").replace("_", " ")


def _find_column_mapping(df_columns: list) -> Dict[str, str]:
    """Encuentra el mapeo entre columnas esperadas y columnas del DataFrame"""
    mapping = {}
    
    # Normalizar columnas del DataFrame
    normalized_df_cols = {_normalize_column_name(col): col for col in df_columns}
    
    for expected_col, variations in EXPECTED_COLUMNS_MAP.items():
        found = False
        for variation in variations:
            normalized_variation = _normalize_column_name(variation)
            if normalized_variation in normalized_df_cols:
                mapping[expected_col] = normalized_df_cols[normalized_variation]
                found = True
                break
        
        if not found:
            # Buscar por coincidencia parcial
            for df_col in df_columns:
                normalized_df_col = _normalize_column_name(df_col)
                if "transportista" in normalized_df_col:
                    if expected_col == "Ag.transportista" and ("ag" in normalized_df_col or "codigo" in normalized_df_col):
                        mapping[expected_col] = df_col
                        found = True
                        break
                    elif expected_col == "Nombre Ag.Transportista" and "nombre" in normalized_df_col:
                        mapping[expected_col] = df_col
                        found = True
                        break
    
    return mapping


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
        # Buscar mapeo de columnas
        column_mapping = _find_column_mapping(df.columns.tolist())
        
        # Verificar que se encontraron todas las columnas necesarias
        expected_cols = set(EXPECTED_COLUMNS_MAP.keys())
        found_cols = set(column_mapping.keys())
        
        if not expected_cols.issubset(found_cols):
            faltantes = expected_cols - found_cols
            print(f"DEBUG: Columnas disponibles en el archivo: {list(df.columns)}")
            print(f"DEBUG: Mapeo encontrado: {column_mapping}")
            raise ValueError(
                f"El archivo no contiene las columnas necesarias: {', '.join(sorted(faltantes))}"
            )
        
        # Renombrar columnas para usar nombres estándar
        df = df.rename(columns=column_mapping)

    return df

