import pandas as pd
import os

# -------------------------------------------------------------
# Función que carga el archivo Excel con el manifiesto de viajes
def cargar_manifesto(ruta):
    # Verifica si el archivo existe en la ruta proporcionada
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"Archivo no encontrado en la ruta: {ruta}")
    
    # Carga directa del archivo
    df = pd.read_excel(ruta)

    return df

