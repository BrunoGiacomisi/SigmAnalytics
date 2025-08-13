# Servicio de análisis que separa cálculos de generación de gráficos
import pandas as pd
from typing import Dict, List, Tuple, Optional
try:
    from src.services.data_processor import DataProcessor
    from src.constants import Columns
    from src.models import db
except ImportError:
    # Fallback para imports relativos
    from .data_processor import DataProcessor
    import sys
    sys.path.append('..')
    from constants import Columns
    from models import db


class AnalyticsService:
    """Servicio que maneja los cálculos de análisis sin generar gráficos"""
    
    def __init__(self):
        self.data_processor = DataProcessor()
    
    def calculate_all_metrics(self, df: pd.DataFrame, codes: List[str]) -> Dict[str, float]:
        """
        Calcula todas las métricas de una sola vez para evitar múltiples filtrados.
        """
        return self.data_processor.calculate_grouped_stats(df, codes)
    
    def calculate_participation(self, df: pd.DataFrame, codes: List[str]) -> float:
        """Calcula el porcentaje de participación de representados"""
        stats = self.calculate_all_metrics(df, codes)
        return stats['participacion']
    
    def get_period_from_df(self, df: pd.DataFrame) -> Optional[str]:
        """Obtiene el período del DataFrame"""
        return self.data_processor.extract_period_from_df(df)
    
    def should_update_historical(self, df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
        """
        Determina si se debe actualizar el histórico.
        Retorna: (should_update, period)
        """
        period = self.get_period_from_df(df)
        if not period:
            return False, None
        
        # Verificar si el período ya existe
        period_exists = db.existe_periodo(period)
        most_recent_period = db.get_periodo_mas_reciente()
        
        # Solo actualizar si es nuevo y no es anterior al más reciente
        should_update = (not period_exists and 
                        (most_recent_period is None or period > most_recent_period))
        
        return should_update, period
    
    def update_historical_data(self, df: pd.DataFrame, codes: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Actualiza los datos históricos si corresponde.
        Retorna: (was_updated, period)
        """
        should_update, period = self.should_update_historical(df)
        
        if not should_update or not period:
            return False, period
        
        # Calcular métricas
        metrics = self.calculate_all_metrics(df, codes)
        
        # Insertar en base de datos
        try:
            db.insertar_registro(
                period,
                metrics['mediana_representados'],
                metrics['mediana_otros'], 
                metrics['promedio_representados'],
                metrics['promedio_otros'],
                metrics['participacion'] # por ahora no tiene uso en la logica de la app, 
                                         # pero se mantiene para futuras implementaciones
                
            )
            return True, period
        except Exception as e:
            print(f"Error actualizando histórico: {e}")
            return False, period
    
    def get_historical_data(self) -> pd.DataFrame:
        """Obtiene todos los datos históricos"""
        return db.obtener_historico_completo()
    
    def process_manifest_data(self, df: pd.DataFrame, codes: List[str]) -> Dict[str, any]:
        """
        Procesa los datos del manifiesto y retorna toda la información necesaria.
        """
        print(f"DEBUG: Procesando manifiesto con {len(df)} filas y {len(codes)} códigos")
        
        # Calcular métricas principales
        print("DEBUG: Calculando métricas...")
        metrics = self.calculate_all_metrics(df, codes)
        print(f"DEBUG: Métricas calculadas: {metrics}")
        
        print("DEBUG: Obteniendo período...")
        period = self.get_period_from_df(df)
        print(f"DEBUG: Período obtenido: {period}")
        
        # Determinar si actualizar histórico
        print("DEBUG: Verificando actualización histórica...")
        historical_updated, _ = self.update_historical_data(df, codes)
        print(f"DEBUG: Histórico actualizado: {historical_updated}")
        
        # Determinar si es preview (período anterior al más reciente)
        print("DEBUG: Verificando si es preview...")
        most_recent_period = db.get_periodo_mas_reciente()
        is_preview = (most_recent_period is not None and 
                     period is not None and 
                     period <= most_recent_period)
        print(f"DEBUG: Es preview: {is_preview} (período actual: {period}, más reciente: {most_recent_period})")
        
        result = {
            'metrics': metrics,
            'period': period,
            'historical_updated': historical_updated,
            'is_preview': is_preview,
            'viajes_representados': metrics['total_viajes_representados']
        }
        
        print("DEBUG: Procesamiento de manifiesto completado")
        return result
    
    def get_agents_for_period(self, df: pd.DataFrame, codes: List[str], 
                             period: str) -> List[Tuple[str, str]]:
        """Obtiene agentes que tuvieron viajes en un período específico"""
        return self.data_processor.get_agents_with_trips(df, codes, period)