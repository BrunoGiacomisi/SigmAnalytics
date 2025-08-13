import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, List
import pandas as pd

from src.models.viajes_representado import (
    DEFAULT_COLUMNS_ORDER,
    generar_pdf_para_representado,
    obtener_viajes_representado,
    filtrar_columnas_relevantes,
    formatear_datos_para_visualizacion,
    calcular_estadisticas_viajes,
    listar_representados_con_viajes,
)
from src.constants import FileTypes, Processing
from src.config import LOGO_PATH
from src.models.pdf_renderer import build_report_html, TEMPLATES_DIR, is_wkhtmltopdf_available
from src.views.tabla_dinamica_viewer import abrir_tabla_dinamica_viewer
from src.models.design_system import (
    get_color, get_spacing, get_font_tuple, get_dimension,
    BUTTON_PRIMARY, BUTTON_SECONDARY
)
from src.models.design_manager import design_manager

try:  # WebView para previsualizar HTML (sin depender del navegador)
    from tkinterweb import HtmlFrame  # type: ignore
except Exception:  # fallback si no está disponible
    HtmlFrame = None  # type: ignore


class ViajesViewer(ctk.CTkToplevel):
    # Ventana para visualizar y exportar viajes por representado

    def __init__(self, master, df_original: pd.DataFrame, codigos_representados: List[str], periodo: str, file_type: str = FileTypes.INGRESOS):
        super().__init__(master)
        self.title(f"Viajes por Representado - {file_type.title()}")
        self.geometry("1200x800")  # Tamaño más grande para mejor experiencia
        self.resizable(True, True)

        self.df_original = df_original
        # Mapear solo los que viajaron: [(codigo, nombre), ...]
        self.items_cod_nombre = listar_representados_con_viajes(df_original, codigos_representados, periodo)
        self.periodo = periodo
        self.file_type = file_type

        # Obtener colores del sistema de diseño
        self.colors = design_manager.get_colors()
        
        # Variables para estadísticas que se mostrarán en KPIs
        self.stats_vars = {
            'total_viajes': ctk.StringVar(value="0"),
            'monto_total': ctk.StringVar(value="$ 0"),
            'codigo_actual': ctk.StringVar(value="-"),
            'representado_actual': ctk.StringVar(value="")
        }

        self._crear_ui()
        self._actualizar_preview()

    def _crear_ui(self):
        # ═══════════════════════════════════════════════════════════════════════════════
        # HEADER CON CONTROLES Y KPIS
        # ═══════════════════════════════════════════════════════════════════════════════
        
        header_frame = ctk.CTkFrame(
            self,
            fg_color=self.colors["card_background"],
            corner_radius=get_dimension("border_radius")
        )
        header_frame.pack(fill="x", padx=get_spacing("md"), pady=(get_spacing("md"), get_spacing("sm")))

        # Título de la sección
        title_label = ctk.CTkLabel(
            header_frame,
            text="📋 Viajes por Representado",
            font=get_font_tuple("xl", "bold"),
            text_color=self.colors["text_primary"]
        )
        title_label.pack(pady=(get_spacing("md"), get_spacing("sm")))

        # Selector de representado
        selector_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        selector_frame.pack(fill="x", padx=get_spacing("md"), pady=(0, get_spacing("sm")))

        ctk.CTkLabel(
            selector_frame, 
            text="Representado:",
            font=get_font_tuple("base", "bold"),
            text_color=self.colors["text_primary"]
        ).pack(side="left", padx=(0, get_spacing("sm")))

        # ComboBox para seleccionar representado
        display_names = [name for _, name in self.items_cod_nombre]
        default_value = display_names[0] if display_names else ""
        self.display_var = ctk.StringVar(value=default_value)
        self.codigo_por_nombre = {name: code for code, name in self.items_cod_nombre}
        self.codigo_combo = ctk.CTkComboBox(
            selector_frame,
            values=display_names,
            variable=self.display_var,
            width=320,
            command=self._on_combo_change,
            font=get_font_tuple("base"),
            fg_color=self.colors["card_background"],
            border_color=self.colors["border"]
        )
        self.codigo_combo.pack(side="left")

        # ═══════════════════════════════════════════════════════════════════════════════
        # BARRA DE KPIs (RESUMEN DE TOTALES)
        # ═══════════════════════════════════════════════════════════════════════════════
        
        kpi_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=get_spacing("md"), pady=(get_spacing("md"), get_spacing("md")))
        kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Crear KPIs individuales
        self._crear_kpi_card(kpi_frame, "🚚 Total Viajes", self.stats_vars['total_viajes'], 0, 0)
        self._crear_kpi_card(kpi_frame, "💰 Monto Total", self.stats_vars['monto_total'], 0, 1)
        self._crear_kpi_card(kpi_frame, "🏷️ Código", self.stats_vars['codigo_actual'], 0, 2)
        self._crear_kpi_card(kpi_frame, "👤 Representado", self.stats_vars['representado_actual'], 0, 3)

        # ═══════════════════════════════════════════════════════════════════════════════
        # BARRA DE ACCIONES CON SPLIT BUTTON
        # ═══════════════════════════════════════════════════════════════════════════════
        
        acciones_frame = ctk.CTkFrame(
            self,
            fg_color=self.colors["card_background"],
            corner_radius=get_dimension("border_radius")
        )
        acciones_frame.pack(fill="x", padx=get_spacing("md"), pady=(0, get_spacing("sm")))

        # Frame interno para botones
        buttons_frame = ctk.CTkFrame(acciones_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=get_spacing("md"), pady=get_spacing("sm"))

        # Split button de exportación (lado izquierdo)
        export_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        export_frame.pack(side="left")

        self.btn_export = ctk.CTkButton(
            export_frame,
            text="📄 Exportar PDF",
            command=self._on_export,
            **BUTTON_SECONDARY,
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"],
            text_color=self.colors["text_on_primary"],
            width=140
        )
        self.btn_export.pack(side="left", padx=(0, get_spacing("xs")))

        self.btn_export_all = ctk.CTkButton(
            export_frame,
            text="📁 Todos PDF",
            command=self._on_export_all,
            **BUTTON_SECONDARY,
            fg_color=self.colors["secondary"],
            hover_color=self.colors["secondary_hover"],
            text_color=self.colors["text_on_primary"],
            width=120
        )
        self.btn_export_all.pack(side="left")

        # Botón tabla dinámica (lado derecho)
        self.btn_tabla_dinamica = ctk.CTkButton(
            buttons_frame,
            text="📊 TABLA DINAMICA",
            command=self._on_tabla_dinamica,
            **BUTTON_SECONDARY,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            text_color=self.colors["text_on_primary"],
            width=160
        )
        self.btn_tabla_dinamica.pack(side="right")

        # Aviso proactivo si falta wkhtmltopdf
        self._wkhtml_disponible = is_wkhtmltopdf_available()
        if not self._wkhtml_disponible:
            self.btn_export.configure(state="disabled")
            self.btn_export_all.configure(state="disabled")
            aviso = ctk.CTkLabel(
                acciones_frame,
                text=(
                    "⚠ wkhtmltopdf no está disponible. Instalalo o setea WKHTMLTOPDF_BINARY/WKHTMLTOPDF_PATH "
                    "para habilitar la exportación a PDF."
                ),
                text_color="#e67e22",
            )
            aviso.pack(side="left", padx=10)

        # Tabla (usaremos un Text simple renderizado por ahora para no introducir dependencias adicionales)
        body = ctk.CTkFrame(self)
        body.pack(fill="both", expand=True, padx=10, pady=10)

        # Vista previa HTML usando HtmlFrame si está disponible; si no, usa Text como respaldo
        if HtmlFrame is not None:
            self.preview_html = HtmlFrame(body, messages_enabled=False)
            self.preview_html.pack(fill="both", expand=True)
            self.preview_text = None
        else:
            self.preview_html = None
            self.preview_text = ctk.CTkTextbox(body, wrap="none")
            self.preview_text.pack(fill="both", expand=True)

        # Traer ventana al frente y enfocar
        try:
            self.transient(self.master)
            self.attributes('-topmost', True)
            self.lift()
            self.focus_force()
            self.after(400, lambda: self.attributes('-topmost', False))
        except Exception:
            pass

        self._actualizar_preview()

    def _crear_kpi_card(self, parent, title: str, value_var: ctk.StringVar, row: int, col: int):
        """Crear una tarjeta KPI individual"""
        card = ctk.CTkFrame(
            master=parent,
            corner_radius=get_dimension("border_radius"),
            fg_color=self.colors["surface"],
            border_width=1,
            border_color=self.colors["border_light"],
            height=80
        )
        card.grid(row=row, column=col, sticky="ew", padx=get_spacing("xs"), pady=0)
        card.grid_propagate(False)
        
        # Título de la métrica
        title_label = ctk.CTkLabel(
            master=card,
            text=title,
            font=get_font_tuple("xs", "bold"),
            text_color=self.colors["text_secondary"],
            anchor="w"
        )
        title_label.pack(fill="x", padx=get_spacing("sm"), pady=(get_spacing("sm"), 0))
        
        # Valor de la métrica
        value_label = ctk.CTkLabel(
            master=card,
            textvariable=value_var,
            font=get_font_tuple("md", "bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        value_label.pack(fill="x", padx=get_spacing("sm"), pady=(0, get_spacing("sm")))
        
        return card

    def _actualizar_preview(self):
        """Actualizar KPIs y vista previa de tabla"""
        try:
            df = self._collect_current_df()
            self._actualizar_kpis(df)
            self._render_preview(df)
        except Exception as e:
            print(f"Error actualizando preview: {e}")

    def _actualizar_kpis(self, df: pd.DataFrame):
        """Actualizar los valores de los KPIs"""
        if df.empty:
            self.stats_vars['total_viajes'].set("0")
            self.stats_vars['monto_total'].set("$ 0")
            self.stats_vars['codigo_actual'].set("-")
            self.stats_vars['representado_actual'].set("Sin selección")
        else:
            # Calcular estadísticas
            total_viajes = len(df)
            stats = calcular_estadisticas_viajes(df)
            # Keys válidas según calcular_estadisticas_viajes
            monto_total = stats.get("total", 0)
            
            # Formatear valores con separador de miles
            def format_currency(value):
                return f"$ {value:,.0f}".replace(",", ".")
            
            # Obtener código del representado actual
            representado_actual = self.display_var.get() or "Sin selección"
            codigo_actual = self.codigo_por_nombre.get(representado_actual, "-")
            
            # Actualizar variables
            self.stats_vars['total_viajes'].set(f"{total_viajes:,} viajes".replace(",", "."))
            self.stats_vars['monto_total'].set(format_currency(monto_total))
            self.stats_vars['codigo_actual'].set(codigo_actual)
            self.stats_vars['representado_actual'].set(representado_actual)

    def _render_preview(self, df: pd.DataFrame) -> None:
        # Renderiza HTML optimizado para preview con mejor formato
        if df.empty:
            html = "<div style='padding:16px;font-family:Segoe UI,Arial;color:#666'>No hay viajes para el período seleccionado.</div>"
        else:
            # Calcular estadísticas
            total_viajes = len(df)
            stats = calcular_estadisticas_viajes(df)
            monto_total = stats.get("total", 0)
            representado_actual = self.display_var.get() or "-"
            codigo_actual = self.codigo_por_nombre.get(representado_actual, "-")
            
            # Crear HTML optimizado para preview
            html = f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 16px; background: #fff;">
                <!-- Header con título -->
                <div style="border-bottom: 2px solid #00587A; margin-bottom: 16px; padding-bottom: 8px;">
                    <h2 style="margin: 0; color: #00587A; font-size: 18px;">{representado_actual}</h2>
                </div>
                
                <!-- Resumen ejecutivo en formato limpio -->
                <div style="background: #f8f9fa; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                        <tr>
                            <td style="padding: 4px 8px; font-weight: 600; color: #666; width: 25%;">Total</td>
                            <td style="padding: 4px 8px; color: #333;"><strong>{total_viajes}</strong> viajes</td>
                            <td style="padding: 4px 8px; font-weight: 600; color: #666; width: 25%;">Código</td>
                            <td style="padding: 4px 8px; color: #333;"><strong>{codigo_actual}</strong></td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 8px; font-weight: 600; color: #666;">Monto total</td>
                            <td style="padding: 4px 8px; color: #00587A; font-weight: 700;">$ {monto_total:,.0f}</td>
                            <td style="padding: 4px 8px; font-weight: 600; color: #666;">Período</td>
                            <td style="padding: 4px 8px; color: #333;"><strong>{self.periodo}</strong></td>
                        </tr>
                    </table>
                </div>
                
                <!-- Tabla de viajes -->
                <div style="margin-top: 20px;">
                    <h3 style="margin: 0 0 12px 0; color: #00587A; font-size: 16px;">Detalle de viajes</h3>
                    <div style="overflow-x: auto; max-height: 400px; border: 1px solid #ddd; border-radius: 6px;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">"""
            
            # Crear headers dinámicamente basados en las columnas del DataFrame
            headers_html = "<tr>"
            for col in df.columns:
                headers_html += (
                    "<th style=\"padding:8px; text-align:left; font-weight:600; "
                    "border-right:1px solid rgba(0,0,0,0.05); "
                    "background:#3498db; color:#fff; "
                    "position:sticky; top:0; z-index:1;\">"
                    f"{col}</th>"
                )
            headers_html += "</tr>"
            
            html += headers_html + "<tbody>"
            
            # Crear filas de datos
            for i, (_, row) in enumerate(df.iterrows()):
                bg_color = "#f8f9fa" if i % 2 == 0 else "white"
                html += f"<tr style='background: {bg_color}; border-bottom: 1px solid #eee;'>"
                for col in df.columns:
                    value = row[col] if pd.notna(row[col]) else "-"
                    html += f"<td style='padding: 6px 8px; border-right: 1px solid #eee;'>{value}</td>"
                html += "</tr>"
            
            html += """
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            """

        if self.preview_html is not None:
            try:
                # tkinterweb API: load_html supports base_url para resolver <link href="report.css">
                self.preview_html.load_html(html, base_url=str(TEMPLATES_DIR))
            except Exception:
                # Fallback mínimo
                self.preview_html.load_html("<pre style='padding:12px;font-family:monospace'>No se pudo renderizar HTML</pre>")
        else:
            # Fallback texto simple
            self.preview_text.configure(state="normal")
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", "Vista previa HTML no disponible. Instala tkinterweb para ver el formato.")
            self.preview_text.configure(state="disabled")

    def _collect_current_df(self) -> pd.DataFrame:
        # Traducir selección visible (nombre) a código 8888
        nombre_sel = self.display_var.get()
        codigo = self.codigo_por_nombre.get(nombre_sel, "")
        df_viajes = obtener_viajes_representado(self.df_original, codigo, self.periodo)
        
        # Usar columnas y precio según el tipo de archivo
        if self.file_type == FileTypes.LASTRES:
            columnas = Processing.LASTRES_COLUMNS_ORDER
            precio = Processing.LASTRES_PRICE_PER_TRIP
        else:
            columnas = DEFAULT_COLUMNS_ORDER  
            precio = Processing.DEFAULT_PRICE_PER_TRIP
            
        df_viajes = filtrar_columnas_relevantes(df_viajes, columnas=columnas, precio_por_viaje=precio)
        df_viajes_fmt = formatear_datos_para_visualizacion(df_viajes)
        return df_viajes_fmt

    def _on_combo_change(self, _value: str) -> None:
        # Actualiza previsualización inmediatamente al cambiar selección
        self._actualizar_preview()

    def _on_export(self) -> None:
        try:
            nombre_sel = self.display_var.get()
            codigo = self.codigo_por_nombre.get(nombre_sel, "")
            df = obtener_viajes_representado(self.df_original, codigo, self.periodo)
            
            # Usar columnas y precio según el tipo de archivo
            if self.file_type == FileTypes.LASTRES:
                columnas = Processing.LASTRES_COLUMNS_ORDER
                precio = Processing.LASTRES_PRICE_PER_TRIP
            else:
                columnas = DEFAULT_COLUMNS_ORDER  
                precio = Processing.DEFAULT_PRICE_PER_TRIP
                
            df = filtrar_columnas_relevantes(df, columnas=columnas, precio_por_viaje=precio)
            stats = calcular_estadisticas_viajes(df, precio_por_viaje=precio)
            ruta_pdf = generar_pdf_para_representado(
                self.df_original,
                codigo=codigo,
                periodo=self.periodo,
                nombre_representado=nombre_sel or None,
                precio_por_viaje=stats["precio_por_viaje"],
                columnas=columnas,
                logo_path=str(LOGO_PATH),
                file_type=self.file_type
            )
            messagebox.showinfo("Exportación", "PDF generado en la carpeta descargas")
        except Exception as e:
            message = str(e)
            if "wkhtmltopdf" in message.lower():
                message += "\n\nSugerencia: instalá wkhtmltopdf (0.12.x) o configurá WKHTMLTOPDF_BINARY/WKHTMLTOPDF_PATH."
            messagebox.showerror("Error", message)

    def _on_export_all(self) -> None:
        try:
            if not self.items_cod_nombre:
                messagebox.showinfo("Exportación", "No hay representados con viajes en este período.")
                return
            generados = []
            for codigo, nombre in self.items_cod_nombre:
                df = obtener_viajes_representado(self.df_original, codigo, self.periodo)
                if df.empty:
                    continue
                
                # Usar columnas y precio según el tipo de archivo
                if self.file_type == FileTypes.LASTRES:
                    columnas = Processing.LASTRES_COLUMNS_ORDER
                    precio = Processing.LASTRES_PRICE_PER_TRIP
                else:
                    columnas = DEFAULT_COLUMNS_ORDER  
                    precio = Processing.DEFAULT_PRICE_PER_TRIP
                    
                df = filtrar_columnas_relevantes(df, columnas=columnas, precio_por_viaje=precio)
                stats = calcular_estadisticas_viajes(df, precio_por_viaje=precio)
                ruta_pdf = generar_pdf_para_representado(
                    self.df_original,
                    codigo=codigo,
                    periodo=self.periodo,
                    nombre_representado=nombre,
                    precio_por_viaje=stats["precio_por_viaje"],
                    columnas=columnas,
                    logo_path=str(LOGO_PATH),
                    file_type=self.file_type
                )
                generados.append(str(ruta_pdf))
            if generados:
                messagebox.showinfo("Exportación", "Los archivos se exportaron con éxito.")
            else:
                messagebox.showinfo("Exportación", "No se generó ningún PDF.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_tabla_dinamica(self) -> None:
        try:
            # Obtener los códigos de representados desde los items
            codigos_representados = [codigo for codigo, _ in self.items_cod_nombre]
            abrir_tabla_dinamica_viewer(self, self.df_original, codigos_representados, self.periodo, self.file_type)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir tabla dinámica: {str(e)}")


def abrir_viajes_viewer(master, df_original: pd.DataFrame, codigos_representados: List[str], periodo: str, file_type: str = FileTypes.INGRESOS) -> None:
    ViajesViewer(master, df_original=df_original, codigos_representados=codigos_representados, periodo=periodo, file_type=file_type)


