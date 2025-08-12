import customtkinter as ctk
from tkinter import messagebox, ttk
from typing import Optional, List
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as mpatches

from src.models.viajes_representado import (
    generar_tabla_dinamica_resumen,
    calcular_totales_tabla_dinamica,
    ordenar_tabla_dinamica,
)
from src.config import LOGO_PATH
from src.models.design_manager import design_manager
from src.models.design_system import get_color, get_spacing, get_font_tuple


class TablaDinamicaViewer(ctk.CTkToplevel):
    # Ventana para visualizar la tabla dinámica de resumen de transportes

    def __init__(self, master, df_original: pd.DataFrame, codigos_representados: List[str], periodo: str):
        super().__init__(master)
        self.title("Tabla Dinámica - Resumen de Transportes")
        self.geometry("1430x890")
        self.resizable(True, True)

        self.df_original = df_original
        self.codigos_representados = codigos_representados
        self.periodo = periodo
        self.orden_actual = "alfabetico"
        
        # Obtener colores del sistema de diseño
        self.colors = design_manager.get_colors()

        # Generar datos de la tabla dinámica
        self.df_resumen = generar_tabla_dinamica_resumen(df_original, periodo, codigos_representados)
        self.df_resumen = ordenar_tabla_dinamica(self.df_resumen, self.orden_actual)
        self.totales = calcular_totales_tabla_dinamica(self.df_resumen)

        self._crear_ui()

        # Traer ventana al frente y enfocar
        try:
            self.transient(master)
            self.attributes('-topmost', True)
            self.lift()
            self.focus_force()
            self.after(400, lambda: self.attributes('-topmost', False))
        except Exception:
            pass

    def _crear_ui(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header con título y período
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))

        # Título
        title_label = ctk.CTkLabel(
            header_frame, 
            text="INGRESOS", 
            font=("Segoe UI", 18, "bold"),
            text_color="#3498db"
        )
        title_label.pack(pady=10)

        # Período
        periodo_label = ctk.CTkLabel(
            header_frame,
            text=f"Período: {self.periodo}",
            font=("Segoe UI", 12),
            text_color="#7f8c8d"
        )
        periodo_label.pack(pady=(0, 10))

        # Frame para controles de ordenamiento
        controles_frame = ctk.CTkFrame(main_frame)
        controles_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(controles_frame, text="Ordenar por:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(10, 5))

        # Botones de ordenamiento
        self.btn_orden_alfabetico = ctk.CTkButton(
            controles_frame,
            text="Alfabético",
            command=lambda: self._cambiar_orden("alfabetico"),
            width=100,
            height=30,
            fg_color="#3498db" if self.orden_actual == "alfabetico" else "#95a5a6",
            hover_color="#2980b9" if self.orden_actual == "alfabetico" else "#7f8c8d"
        )
        self.btn_orden_alfabetico.pack(side="left", padx=5)

        self.btn_orden_cantidad = ctk.CTkButton(
            controles_frame,
            text="Cantidad de Viajes",
            command=lambda: self._cambiar_orden("cantidad_viajes"),
            width=120,
            height=30,
            fg_color="#3498db" if self.orden_actual == "cantidad_viajes" else "#95a5a6",
            hover_color="#2980b9" if self.orden_actual == "cantidad_viajes" else "#7f8c8d"
        )
        self.btn_orden_cantidad.pack(side="left", padx=5)

        # Título del gráfico (más claro y en la misma navegación)
        chart_title_label = ctk.CTkLabel(
            controles_frame,
            text="Distribución de Ingresos por Transportista",
            font=("Segoe UI", 12, "bold"),
            text_color="#3498db"
        )
        chart_title_label.pack(side="right", padx=(20, 191))

        # Frame para tabla y gráfico (lado a lado)
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True)
        content_frame.grid_columnconfigure(0, weight=2)  # Tabla ocupa más espacio
        content_frame.grid_columnconfigure(1, weight=1)  # Gráfico ocupa menos espacio

        # Frame para la tabla
        table_frame = ctk.CTkFrame(content_frame)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Crear Treeview para la tabla
        self._crear_tabla(table_frame)

        # Frame para el gráfico
        chart_frame = ctk.CTkFrame(content_frame)
        chart_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # Crear pie chart
        self._crear_pie_chart(chart_frame)

        # Frame para totales
        totales_frame = ctk.CTkFrame(main_frame)
        totales_frame.pack(fill="x", pady=(10, 0))

        # Mostrar totales
        self._mostrar_totales(totales_frame)

    def _crear_tabla(self, parent):
        # Crear Treeview con scrollbars
        tree_frame = ctk.CTkFrame(parent)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Configurar columnas
        columns = ("Nombre Ag. Transportista", "Suma de PRECIO", "Cantidad de Viajes")
        
        # Crear Treeview
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configurar encabezados
        self.tree.heading("Nombre Ag. Transportista", text="Nombre Ag. Transportista")
        self.tree.heading("Suma de PRECIO", text="Suma de PRECIO")
        self.tree.heading("Cantidad de Viajes", text="Cantidad de Viajes")
        
        # Configurar anchos de columna
        self.tree.column("Nombre Ag. Transportista", width=400, anchor="w")
        self.tree.column("Suma de PRECIO", width=150, anchor="e")
        self.tree.column("Cantidad de Viajes", width=150, anchor="center")
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Insertar datos
        self._cargar_datos_tabla()

    def _cargar_datos_tabla(self):
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insertar datos
        for _, row in self.df_resumen.iterrows():
            nombre = row["Nombre Ag. Transportista"]
            precio = f"$ {row['Suma de PRECIO']:,.0f}".replace(",", ".")
            cantidad = str(int(row["Cantidad de Viajes"]))
            
            self.tree.insert("", "end", values=(nombre, precio, cantidad))
        
        # Insertar fila de totales
        total_precio = f"$ {self.totales['total_precio']:,.0f}".replace(",", ".")
        total_cantidad = str(int(self.totales['total_viajes']))
        
        self.tree.insert("", "end", values=("Total general", total_precio, total_cantidad), tags=("total",))

    def _crear_pie_chart(self, parent):
        # Crear el pie chart
        if self.df_resumen.empty:
            # Si no hay datos, mostrar mensaje
            no_data_label = ctk.CTkLabel(
                parent,
                text="No hay datos para mostrar",
                font=("Segoe UI", 12),
                text_color="#7f8c8d"
            )
            no_data_label.pack(expand=True)
            return

        # Configurar el estilo de matplotlib
        plt.style.use('default')
        plt.rcParams['font.family'] = 'Segoe UI'
        plt.rcParams['font.size'] = 10

        # Crear figura y eje
        fig, ax = plt.subplots(figsize=(6, 6))
        fig.patch.set_facecolor('#f0f0f0')  # Color de fondo del gráfico
        ax.set_facecolor('#f0f0f0')

        # Generar datos para el gráfico SIEMPRE ordenados por "Cantidad de Viajes"
        # Esto asegura que el gráfico no cambie con el filtro de la tabla
        df_chart_base = generar_tabla_dinamica_resumen(
            self.df_original, self.periodo, self.codigos_representados
        )
        df_chart_sorted = ordenar_tabla_dinamica(df_chart_base, "cantidad_viajes")

        # Tomar todos los datos para el gráfico
        df_chart = df_chart_sorted.copy()
        
        # Preparar etiquetas y porcentajes: mostrar solo los 5 nombres principales
        labels = []
        autopct_values = []
        
        # Calcular porcentajes totales
        total_precio = df_chart['Suma de PRECIO'].sum()
        
        # Obtener los 5 transportistas con mayor porcentaje (por posición, no por porcentaje único)
        top_5_indices = df_chart.head(5).index
        
        for i, row in df_chart.iterrows():
            porcentaje = (row['Suma de PRECIO'] / total_precio) * 100
            
            if i in top_5_indices:  # Si está en los primeros 5 por posición, mostrar nombre y porcentaje
                labels.append(row['Nombre Ag. Transportista'])
                autopct_values.append(f'{porcentaje:.1f}%')
            else:  # El resto sin nombre y sin porcentaje
                labels.append("")
                autopct_values.append("")

        # Colores para el pie chart
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', 
                 '#1abc9c', '#e67e22', '#34495e', '#95a5a6']

        # Crear el pie chart
        wedges, texts, autotexts = ax.pie(
            df_chart['Suma de PRECIO'],
            labels=labels,
            autopct='%1.1f%%',  # Mostrar todos los porcentajes primero
            colors=colors[:len(df_chart)],
            startangle=90,
            textprops={'fontsize': 7, 'fontweight': 'bold'},  # Letra más pequeña
            pctdistance=0.85
        )

        # Configurar el texto de porcentaje: ocultar los que no son top 5
        for i, autotext in enumerate(autotexts):
            if i < 5:  # Los primeros 5 mantienen su porcentaje
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            else:  # Los demás ocultan su porcentaje
                autotext.set_text("")

        # Ajustar layout
        plt.tight_layout()

        # Crear canvas y agregar al frame
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Guardar referencia para evitar que se destruya
        self.chart_canvas = canvas
        self.chart_fig = fig

    def _actualizar_pie_chart(self):
        # Actualizar el pie chart cuando cambie el orden
        if hasattr(self, 'chart_canvas'):
            # Obtener el frame padre antes de destruir el canvas
            chart_frame = self.chart_canvas.get_tk_widget().master
            self.chart_canvas.get_tk_widget().destroy()
            
            # Limpiar el frame
            for widget in chart_frame.winfo_children():
                widget.destroy()
            
            # Recrear el pie chart
            self._crear_pie_chart(chart_frame)

    def _mostrar_totales(self, parent):
        # Frame para totales
        totales_info = ctk.CTkFrame(parent)
        totales_info.pack(fill="x", padx=10, pady=10)
        
        # Información de totales
        total_precio = f"$ {self.totales['total_precio']:,.0f}".replace(",", ".")
        total_cantidad = str(int(self.totales['total_viajes']))
        
        totales_text = f"Total General: {total_precio} | Total Viajes: {total_cantidad}"
        
        totales_label = ctk.CTkLabel(
            totales_info,
            text=totales_text,
            font=("Segoe UI", 14, "bold"),
            text_color="#27ae60"
        )
        totales_label.pack(pady=10)

    def _cambiar_orden(self, nuevo_orden: str) -> None:
        # Cambiar el orden de la tabla
        self.orden_actual = nuevo_orden
        self.df_resumen = ordenar_tabla_dinamica(self.df_resumen, nuevo_orden)
        
        # Actualizar colores de botones
        self._actualizar_colores_botones()
        
        # Recargar la tabla
        self._cargar_datos_tabla()
        
        # Actualizar el pie chart
        self._actualizar_pie_chart()

    def _actualizar_colores_botones(self) -> None:
        # Actualizar colores de los botones según el orden actual
        colores_activo = {"fg_color": "#3498db", "hover_color": "#2980b9"}
        colores_inactivo = {"fg_color": "#95a5a6", "hover_color": "#7f8c8d"}
        
        self.btn_orden_alfabetico.configure(
            **colores_activo if self.orden_actual == "alfabetico" else colores_inactivo
        )
        self.btn_orden_cantidad.configure(
            **colores_activo if self.orden_actual == "cantidad_viajes" else colores_inactivo
        )


def abrir_tabla_dinamica_viewer(master, df_original: pd.DataFrame, codigos_representados: List[str], periodo: str) -> None:
    TablaDinamicaViewer(master, df_original=df_original, codigos_representados=codigos_representados, periodo=periodo)
