# Servicio separado para generación de gráficos
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List
from pathlib import Path
import sys
import os

from src.services.data_processor import DataProcessor
from src.constants import Columns, Charts, ChartTitles
from src.models import db


class ChartService:
    """Servicio dedicado exclusivamente a la generación de gráficos"""
    
    def __init__(self):
        self.data_processor = DataProcessor()
        self._setup_matplotlib()
        print("DEBUG: ChartService inicializado")
    
    def _setup_matplotlib(self):
        """Configuración común de matplotlib"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Backend sin GUI para evitar problemas
            plt.style.use('default')
            plt.rcParams.update({
                'figure.facecolor': 'white',
                'axes.facecolor': 'white',
                'font.size': 10,
                'axes.titlesize': 12,
                'axes.labelsize': 10,
                'xtick.labelsize': 9,
                'ytick.labelsize': 9,
                'legend.fontsize': 9
            })
            print("DEBUG: Matplotlib configurado correctamente")
        except Exception as e:
            print(f"DEBUG: Error configurando matplotlib: {e}")
    
    def _save_chart(self, output_path: str, dpi: int = Charts.DPI):
        """Método común para guardar gráficos"""
        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        plt.close()
    
    def generate_boxplot(self, df: pd.DataFrame, codes: List[str], 
                        output_path: str) -> None:
        """
        Genera boxplot de distribución de operaciones.
        """
        df_representados, df_otros = self.data_processor.filter_by_codes(df, codes)
        
        # Preparar datos para boxplot
        if df_representados.empty and df_otros.empty:
            # Crear gráfico vacío con mensaje
            fig, ax = plt.subplots(figsize=Charts.FIGSIZE_BOXPLOT)
            ax.text(0.5, 0.5, 'No hay datos para mostrar', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title(ChartTitles.BOXPLOT)
            self._save_chart(output_path)
            return
        
        # Contar operaciones por agente
        data_to_plot = []
        labels = []
        
        if not df_representados.empty:
            counts_rep = df_representados.groupby(Columns.AGENT_NAME).size()
            data_to_plot.append(counts_rep.values)
            labels.append("Representados")
        
        if not df_otros.empty:
            counts_otros = df_otros.groupby(Columns.AGENT_NAME).size()
            data_to_plot.append(counts_otros.values)
            labels.append("Mercado")
        
        # Crear boxplot
        fig, ax = plt.subplots(figsize=Charts.FIGSIZE_BOXPLOT)
        
        box_plot = ax.boxplot(data_to_plot, labels=labels, patch_artist=True)
        
        # Colores personalizados
        colors = ['#4a9eff', '#ff6b6b']
        for patch, color in zip(box_plot['boxes'], colors[:len(box_plot['boxes'])]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # Calcular y mostrar estadísticas
        if len(data_to_plot) >= 2:
            median_rep = pd.Series(data_to_plot[0]).median()
            median_otros = pd.Series(data_to_plot[1]).median()
            avg_rep = pd.Series(data_to_plot[0]).mean()
            avg_otros = pd.Series(data_to_plot[1]).mean()
            
            # Agregar texto con estadísticas
            stats_text = f"Representados - Med: {median_rep:.1f}, Prom: {avg_rep:.1f}\n"
            stats_text += f"Mercado - Med: {median_otros:.1f}, Prom: {avg_otros:.1f}"
            
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', fontsize=9,
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        ax.set_title(ChartTitles.BOXPLOT, fontsize=14, fontweight='bold')
        ax.set_ylabel('Número de Operaciones')
        ax.grid(True, alpha=0.3)
        
        # Remover spines superiores y derechos
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        self._save_chart(output_path)
    
    def generate_barplot(self, df: pd.DataFrame, codes: List[str], 
                        median_rep: float, median_otros: float,
                        output_path: str) -> None:
        """
        Genera gráfico de barras horizontales con top transportistas.
        """
        df_representados, df_otros = self.data_processor.filter_by_codes(df, codes)
        
        if df_representados.empty:
            # Crear gráfico vacío
            fig, ax = plt.subplots(figsize=Charts.FIGSIZE_DEFAULT)
            ax.text(0.5, 0.5, 'No hay datos de representados para mostrar', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title(ChartTitles.BARRAS)
            self._save_chart(output_path)
            return
        
        # Contar operaciones por transportista
        counts = df_representados.groupby(Columns.AGENT_NAME).size().sort_values(ascending=True)
        
        # Tomar solo los top N
        top_counts = counts.tail(Charts.TOP_TRANSPORTISTAS)
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=Charts.FIGSIZE_DEFAULT)
        
        # Barras horizontales
        bars = ax.barh(range(len(top_counts)), top_counts.values, 
                      color='#4a9eff', alpha=0.8, edgecolor='white', linewidth=1)
        
        # Etiquetas en las barras
        for i, (bar, value) in enumerate(zip(bars, top_counts.values)):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                   f'{value}', va='center', fontsize=9, fontweight='bold')
        
        # Líneas de referencia para medianas
        ax.axvline(x=median_rep, color='red', linestyle='--', alpha=0.7, 
                  label=f'Mediana Representados: {median_rep:.1f}')
        ax.axvline(x=median_otros, color='orange', linestyle='--', alpha=0.7,
                  label=f'Mediana Mercado: {median_otros:.1f}')
        
        # Configuración del gráfico
        ax.set_yticks(range(len(top_counts)))
        ax.set_yticklabels(top_counts.index, fontsize=8)
        ax.set_xlabel('Número de Operaciones')
        ax.set_title(ChartTitles.BARRAS, fontsize=14, fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(axis='x', alpha=0.3)
        
        # Remover spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Invertir eje Y para mostrar el mayor arriba
        ax.invert_yaxis()
        
        self._save_chart(output_path)
    
    def generate_temporal_chart(self, output_path: str) -> None:
        """
        Genera gráfico de evolución temporal de medianas.
        """
        historico = db.obtener_historico_completo()
        
        if historico.empty:
            fig, ax = plt.subplots(figsize=Charts.FIGSIZE_DEFAULT)
            ax.text(0.5, 0.5, 'No hay datos históricos disponibles', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title(ChartTitles.TEMPORAL)
            self._save_chart(output_path)
            return
        
        # Preparar datos
        historico['fecha'] = pd.to_datetime(historico['periodo'] + '-01')
        historico = historico.sort_values('fecha')
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=Charts.FIGSIZE_DEFAULT)
        
        # Líneas
        ax.plot(historico['fecha'], historico['mediana_representados'], 
               marker='o', linestyle='-', linewidth=2, markersize=6,
               color='#4a9eff', label='Representados')
        ax.plot(historico['fecha'], historico['mediana_otros'], 
               marker='s', linestyle='-', linewidth=2, markersize=6,
               color='#ff6b6b', label='Mercado')
        
        # Configuración
        ax.set_title(ChartTitles.TEMPORAL, fontsize=14, fontweight='bold')
        ax.set_xlabel('Período')
        ax.set_ylabel('Mediana de Operaciones')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Formato de fechas en eje X
        fig.autofmt_xdate()
        
        # Remover spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        self._save_chart(output_path)
    
    def generate_averages_temporal_chart(self, output_path: str) -> None:
        """
        Genera gráfico de evolución temporal de promedios.
        """
        historico = db.obtener_historico_completo()
        
        if historico.empty:
            fig, ax = plt.subplots(figsize=Charts.FIGSIZE_DEFAULT)
            ax.text(0.5, 0.5, 'No hay datos históricos disponibles', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title(ChartTitles.PROMEDIOS)
            self._save_chart(output_path)
            return
        
        # Preparar datos
        historico['fecha'] = pd.to_datetime(historico['periodo'] + '-01')
        historico = historico.sort_values('fecha')
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=Charts.FIGSIZE_DEFAULT)
        
        # Líneas con diferentes estilos
        ax.plot(historico['fecha'], historico['promedio_representados'], 
               marker='o', linestyle='-', linewidth=2, markersize=6,
               color='#2e7d32', label='Promedio Representados')
        ax.plot(historico['fecha'], historico['promedio_otros'], 
               marker='s', linestyle='--', linewidth=2, markersize=6,
               color='#d32f2f', label='Promedio Mercado')
        
        # Configuración
        ax.set_title(ChartTitles.PROMEDIOS, fontsize=14, fontweight='bold')
        ax.set_xlabel('Período')
        ax.set_ylabel('Promedio de Operaciones')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Formato de fechas
        fig.autofmt_xdate()
        
        # Remover spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        self._save_chart(output_path)
    
    def generate_all_charts(self, df: pd.DataFrame, codes: List[str], 
                          metrics: dict, output_dir: Path, 
                          period: str, is_preview: bool = False) -> dict:
        """
        Genera todos los gráficos y retorna las rutas.
        """
        print(f"DEBUG: Iniciando generación de gráficos. Preview: {is_preview}, Período: {period}")
        
        try:
            # Determinar carpeta de salida
            if is_preview:
                chart_dir = output_dir / "preview"
            else:
                chart_dir = output_dir / f"graficos_{period}"
            
            chart_dir.mkdir(exist_ok=True)
            print(f"DEBUG: Carpeta de gráficos creada: {chart_dir}")
            
            # Rutas de gráficos
            paths = {
                'boxplot': str(chart_dir / "boxplot_conteos.png"),
                'barplot': str(chart_dir / "barplot_representados.png"),
                'temporal': str(output_dir / "serie_temporal.png"),
                'averages': str(output_dir / "serie_promedios.png")
            }
            
            # Generar gráficos con timeouts y manejo de errores
            print("DEBUG: Generando boxplot...")
            try:
                self.generate_boxplot(df, codes, paths['boxplot'])
                print("DEBUG: Boxplot generado exitosamente")
            except Exception as e:
                print(f"DEBUG: Error generando boxplot: {e}")
                
            print("DEBUG: Generando barplot...")
            try:
                self.generate_barplot(df, codes, 
                                    metrics['mediana_representados'], 
                                    metrics['mediana_otros'], 
                                    paths['barplot'])
                print("DEBUG: Barplot generado exitosamente")
            except Exception as e:
                print(f"DEBUG: Error generando barplot: {e}")
            
            # Gráficos temporales solo si no es preview
            if not is_preview:
                print("DEBUG: Generando gráficos temporales...")
                try:
                    self.generate_temporal_chart(paths['temporal'])
                    print("DEBUG: Gráfico temporal generado")
                except Exception as e:
                    print(f"DEBUG: Error generando gráfico temporal: {e}")
                    
                try:
                    self.generate_averages_temporal_chart(paths['averages'])
                    print("DEBUG: Gráfico de promedios generado")
                except Exception as e:
                    print(f"DEBUG: Error generando gráfico de promedios: {e}")
            
            print("DEBUG: Generación de gráficos completada")
            return paths
            
        except Exception as e:
            print(f"DEBUG: Error general en generate_all_charts: {e}")
            import traceback
            traceback.print_exc()
            return paths
