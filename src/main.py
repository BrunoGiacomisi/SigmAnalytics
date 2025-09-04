import os
import sys
from pathlib import Path

# Imports con manejo de errores
try:
    from src.models import data_loader
    from src.services import AnalyticsService, ChartService
    from src.constants import Columns
    from src.config import GRAPHS_DIR
except ImportError as e:
    print(f"Error de importación en main.py: {e}")
    # Fallback para desarrollo
    sys.path.append(os.path.dirname(__file__))
    from models import data_loader
    from services import AnalyticsService, ChartService
    from constants import Columns
    from config import GRAPHS_DIR


# -----------------------------------------------------------
# Función refactorizada que usa los nuevos servicios
def _procesar_df(df, codigos: list[str]):
    print("DEBUG: Iniciando _procesar_df")
    
    # Inicializar servicios
    print("DEBUG: Inicializando servicios...")
    analytics_service = AnalyticsService()
    chart_service = ChartService()
    
    # Procesar datos usando el servicio de análisis
    print("DEBUG: Procesando datos con AnalyticsService...")
    result = analytics_service.process_manifest_data(df, codigos)
    
    # Extraer datos del resultado
    print("DEBUG: Extrayendo datos del resultado...")
    metrics = result['metrics']
    period = result['period']
    historical_updated = result['historical_updated']
    is_preview = result['is_preview']
    viajes_representados = result['viajes_representados']
    
    # Generar gráficos
    print("DEBUG: Generando gráficos con ChartService...")
    chart_paths = chart_service.generate_all_charts(
        df, codigos, metrics, Path(GRAPHS_DIR), period, is_preview
    )
    
    print("DEBUG: _procesar_df completado exitosamente")
    
    # Retornar en el formato esperado (compatibilidad con código existente)
    return (
        metrics['mediana_representados'],
        metrics['mediana_otros'], 
        metrics['promedio_representados'],
        metrics['promedio_otros'],
        metrics['participacion'],
        historical_updated,
        viajes_representados,
        chart_paths['boxplot'],
        chart_paths['barplot'],
        is_preview
    )


def procesar_archivo(
    ruta_manifesto: str,
    codigos: list[str]
) -> tuple:
    if not os.path.exists(ruta_manifesto):
        raise FileNotFoundError(f"El archivo no existe: {ruta_manifesto}")
    if not codigos:
        raise ValueError("La lista de códigos no puede estar vacía")
    df = data_loader.cargar_manifesto(ruta_manifesto)
    return _procesar_df(df, codigos)


def procesar_df(df, codigos: list[str]) -> tuple:
    if df is None or df.empty:
        raise ValueError("El DataFrame está vacío o no es válido")
    if not codigos:
        raise ValueError("La lista de códigos no puede estar vacía")
    return _procesar_df(df, codigos)


if __name__ == "__main__":
    from src.views.dashboard import crear_dashboard
    crear_dashboard()

# Para ejecutar el archivo: 
# primero: venv\Scripts\activate
# segundo: python main.py