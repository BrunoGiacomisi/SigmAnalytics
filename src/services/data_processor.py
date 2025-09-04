# Servicio centralizado para procesamiento de datos
import pandas as pd
import re
from typing import List, Tuple, Dict, Any, Optional
from src.constants import Columns, Processing


class DataProcessor:
    """Centraliza toda la lógica de filtrado y procesamiento de DataFrames"""
    
    # Utilidades comunes
    @staticmethod
    def _prepare_df_with_clean_dates(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """
        Retorna una copia del DataFrame con la columna de fecha convertida a datetime
        y sin filas inválidas para esa columna. Esta función encapsula la lógica
        repetida de conversión y limpieza para minimizar coste y errores.
        """
        df_copy = df.copy()
        df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors='coerce')
        df_copy = df_copy.dropna(subset=[date_column])
        return df_copy

    @staticmethod
    def normalize_code(code: str) -> str:
        """Normaliza un código eliminando caracteres no numéricos"""
        return re.sub(r"\D", "", str(code))
    
    @staticmethod
    def normalize_code_series(series: pd.Series) -> pd.Series:
        """Normaliza una serie de códigos"""
        return series.astype(str).apply(DataProcessor.normalize_code)
    
    @staticmethod
    def normalize_codes_list(codes: List[str]) -> List[str]:
        """Normaliza una lista de códigos"""
        return [DataProcessor.normalize_code(code) for code in codes]
    
    @classmethod
    def filter_by_codes(cls, df: pd.DataFrame, codes: List[str], 
                       code_column: str = Columns.AGENT_CODE) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Filtra un DataFrame por códigos de representados.
        Retorna: (df_representados, df_otros)
        """
        # Normalizar códigos de búsqueda
        normalized_search_codes = cls.normalize_codes_list(codes)
        
        # Normalizar códigos del DataFrame
        normalized_df_codes = cls.normalize_code_series(df[code_column])
        
        # Crear máscaras
        mask_representados = normalized_df_codes.isin(normalized_search_codes)
        
        df_representados = df[mask_representados].copy()
        df_otros = df[~mask_representados].copy()
        
        return df_representados, df_otros
    
    @classmethod
    def filter_by_period(cls, df: pd.DataFrame, period: str, 
                        date_column: str = Columns.DATE) -> pd.DataFrame:
        """
        Filtra un DataFrame por período (YYYY-MM).
        """
        try:
            df_copy = cls._prepare_df_with_clean_dates(df, date_column)
            
            # Crear máscara de período
            period_mask = df_copy[date_column].dt.strftime('%Y-%m') == period
            
            return df_copy[period_mask].copy()
        except Exception:
            return pd.DataFrame()
    
    @classmethod
    def filter_by_codes_and_period(cls, df: pd.DataFrame, codes: List[str], period: str,
                                  code_column: str = Columns.AGENT_CODE,
                                  date_column: str = Columns.DATE) -> pd.DataFrame:
        """
        Filtra por códigos Y período en una sola operación eficiente.
        """
        # Preparar dataframe con fechas limpias
        df_copy = cls._prepare_df_with_clean_dates(df, date_column)
        
        # Normalizar sobre el mismo df_copy para evitar desalineaciones
        df_copy[code_column] = cls.normalize_code_series(df_copy[code_column])
        normalized_search_codes = cls.normalize_codes_list(codes)
        
        # Máscaras combinadas (mismo DF base)
        period_mask = df_copy[date_column].dt.strftime('%Y-%m') == period
        code_mask = df_copy[code_column].isin(normalized_search_codes)
        
        return df_copy[period_mask & code_mask].copy()
    
    @classmethod
    def calculate_grouped_stats(cls, df: pd.DataFrame, codes: List[str],
                               group_column: str = Columns.AGENT_NAME,
                               code_column: str = Columns.AGENT_CODE) -> Dict[str, float]:
        """
        Calcula estadísticas agrupadas para representados vs otros.
        Retorna diccionario con medianas y promedios.
        """
        df_representados, df_otros = cls.filter_by_codes(df, codes, code_column)
        
        # Agrupar y contar por nombre de agente
        counts_rep = df_representados.groupby(group_column).size()
        counts_otros = df_otros.groupby(group_column).size()
        
        return {
            'mediana_representados': counts_rep.median() if not counts_rep.empty else 0.0,
            'mediana_otros': counts_otros.median() if not counts_otros.empty else 0.0,
            'promedio_representados': counts_rep.mean() if not counts_rep.empty else 0.0,
            'promedio_otros': counts_otros.mean() if not counts_otros.empty else 0.0,
            'total_viajes_representados': len(df_representados),
            'total_viajes_otros': len(df_otros),
            'participacion': (len(df_representados) / len(df)) * 100 if len(df) > 0 else 0.0
        }
    
    @classmethod
    def get_agents_with_trips(cls, df: pd.DataFrame, codes: List[str], period: str,
                             code_column: str = Columns.AGENT_CODE,
                             name_column: str = Columns.AGENT_NAME,
                             date_column: str = Columns.DATE) -> List[Tuple[str, str]]:
        """
        Obtiene lista de (código, nombre) de agentes que tuvieron viajes en el período.
        """
        # Filtrar por período y códigos
        df_filtered = cls.filter_by_codes_and_period(df, codes, period, code_column, date_column)
        
        if df_filtered.empty:
            return []
        
        # Limpiar datos
        df_clean = df_filtered[[code_column, name_column]].dropna()
        if df_clean.empty:
            return []
        
        df_clean[code_column] = df_clean[code_column].astype(str)
        df_clean[name_column] = df_clean[name_column].astype(str)
        
        # Seleccionar nombre más frecuente por código
        def pick_most_frequent_name(series: pd.Series) -> str:
            mode_vals = series.mode()
            return str(mode_vals.iat[0]) if not mode_vals.empty else str(series.iloc[0])
        
        name_by_code = df_clean.groupby(code_column)[name_column].agg(pick_most_frequent_name)
        
        # Crear lista ordenada por nombre
        items = [(code, name_by_code.loc[code]) for code in name_by_code.index]
        items.sort(key=lambda t: t[1].lower())
        
        return items
    
    @classmethod
    def add_price_column(cls, df: pd.DataFrame, 
                        price_per_trip: float = Processing.DEFAULT_PRICE_PER_TRIP) -> pd.DataFrame:
        """
        Agrega columna de precio calculado por viaje.
        """
        df_copy = df.copy()
        df_copy[Columns.PRICE] = price_per_trip
        return df_copy
    
    @classmethod
    def extract_period_from_df(cls, df: pd.DataFrame, 
                              date_column: str = Columns.DATE) -> Optional[str]:
        """
        Extrae el período (YYYY-MM) más frecuente del DataFrame.
        """
        try:
            df_copy = cls._prepare_df_with_clean_dates(df, date_column)
            
            if df_copy.empty:
                return None
            
            # Obtener períodos y encontrar el más frecuente
            periods = df_copy[date_column].dt.strftime('%Y-%m')
            most_frequent_period = periods.mode()
            
            return most_frequent_period.iloc[0] if not most_frequent_period.empty else None
        except Exception:
            return None
