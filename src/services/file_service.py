# Servicio para manejo de archivos y validación
import pandas as pd
from tkinter import filedialog
from typing import Optional
from src.models.data_loader import cargar_manifesto
from src.services.analytics_service import AnalyticsService


class FileService:
    """Servicio para operaciones con archivos de manifiesto"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
    
    def select_manifest_file(self) -> str:
        """Abre el diálogo de selección de archivo y devuelve la ruta"""
        return filedialog.askopenfilename(
            title="Seleccionar manifiesto",
            filetypes=[["Archivos Excel", "*.xlsx *.xls"]],
        )
    
    def validate_and_load_manifest(self, file_path: str) -> pd.DataFrame:
        """Carga y valida el manifiesto usando la función centralizada"""
        return cargar_manifesto(file_path, validar=True)
    
    def process_manifest_file(self, file_path: str, codes: list[str], 
                            df: Optional[pd.DataFrame] = None) -> tuple:
        """
        Procesa un archivo de manifiesto o un DataFrame ya cargado.
        Retorna tupla compatible con el código existente.
        """
        if df is not None:
            # Usar DataFrame ya cargado
            from src.main import procesar_df
            return procesar_df(df, codes)
        else:
            # Cargar y procesar archivo
            from src.main import procesar_archivo  
            return procesar_archivo(file_path, codes)
    
    def compute_period(self, df: pd.DataFrame) -> Optional[str]:
        """Calcula el período a partir de un DataFrame ya cargado"""
        return self.analytics_service.get_period_from_df(df)
