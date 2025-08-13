# Servicio para manejo de archivos y validación
import pandas as pd
from tkinter import filedialog
from typing import Optional
from src.models.data_loader import cargar_manifesto
from src.services.analytics_service import AnalyticsService
from src.constants import FileTypes


class FileService:
    """Servicio para operaciones con archivos de manifiesto"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
    
    def select_manifest_file(self, file_type: str = FileTypes.INGRESOS) -> str:
        """Abre el diálogo de selección de archivo y devuelve la ruta"""
        title_map = {
            FileTypes.INGRESOS: "Seleccionar archivo de ingresos",
            FileTypes.LASTRES: "Seleccionar archivo de lastres"
        }
        title = title_map.get(file_type, "Seleccionar manifiesto")
        
        return filedialog.askopenfilename(
            title=title,
            filetypes=[["Archivos Excel", "*.xlsx *.xls"]],
        )
    
    def validate_and_load_manifest(self, file_path: str) -> pd.DataFrame:
        """Carga y valida el manifiesto usando la función centralizada"""
        return cargar_manifesto(file_path, validar=True)
    
    def process_manifest_file(self, file_path: str, codes: list[str], 
                            file_type: str = FileTypes.INGRESOS,
                            df: Optional[pd.DataFrame] = None) -> tuple:
        """
        Procesa un archivo de manifiesto o un DataFrame ya cargado.
        Retorna tupla compatible con el código existente.
        
        Para archivos de lastres, retorna datos especiales que no se procesan
        completamente (no se guardan en BD ni se generan KPIs).
        """
        if file_type == FileTypes.LASTRES:
            # Para lastres, solo validamos el archivo y lo devolvemos para visualización
            if df is not None:
                return (0, 0, 0, 0, 0, False, 0, "", "", True)  # Datos dummy, es_preview=True
            else:
                df_validado = self.validate_and_load_manifest(file_path)
                return (0, 0, 0, 0, 0, False, 0, "", "", True)
        else:
            # Procesamiento normal para ingresos
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
