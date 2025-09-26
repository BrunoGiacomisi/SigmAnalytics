import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, List
import pandas as pd
import threading
from pathlib import Path

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
from src.models.design_system import (
    get_color, get_spacing, get_font_tuple, get_dimension,
    BUTTON_PRIMARY, BUTTON_SECONDARY
)
from src.models.design_manager import design_manager
from src.services.gmail_service import GmailDraftService
from src.services.representados_contactos import get_contact_info

try:  # WebView para previsualizar HTML (sin depender del navegador)
    from tkinterweb import HtmlFrame  # type: ignore
except Exception:  # fallback si no está disponible
    HtmlFrame = None  # type: ignore


class ViajesViewer(ctk.CTkToplevel):
    # Ventana para visualizar y exportar viajes por representado

    def __init__(self, master, df_original: pd.DataFrame, codigos_representados: List[str], periodo: str, file_type: str = FileTypes.INGRESOS):
        super().__init__(master)
        self.title(f"Reportes de Viajes - {file_type.title()}")
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
            text="Reportes de Viajes",
            font=get_font_tuple("xl", "bold"),
            text_color=self.colors["text_primary"]
        )
        title_label.pack(pady=(get_spacing("md"), get_spacing("sm")))

        # Selector de representado
        selector_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        selector_frame.pack(fill="x", padx=get_spacing("md"), pady=(0, get_spacing("sm")))

        ctk.CTkLabel(
            selector_frame, 
            text="Previsualizar representado:",
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

        # Título para los botones de exportación
        export_title = ctk.CTkLabel(
            export_frame,
            text="Exportar a PDF",
            font=get_font_tuple("sm", "bold"),
            text_color=self.colors["text_primary"]
        )
        export_title.pack(anchor="w", pady=(0, get_spacing("xs")))

        # Frame para los botones de exportación
        export_buttons_frame = ctk.CTkFrame(export_frame, fg_color="transparent")
        export_buttons_frame.pack()

        self.btn_export = ctk.CTkButton(
            export_buttons_frame,
            text="Actual",
            command=self._on_export,
            **BUTTON_SECONDARY,
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"],
            text_color=self.colors["text_on_primary"],
            width=100
        )
        self.btn_export.pack(side="left", padx=(0, get_spacing("xs")))

        self.btn_export_all = ctk.CTkButton(
            export_buttons_frame,
            text="Todos",
            command=self._on_export_all,
            **BUTTON_SECONDARY,
            fg_color=self.colors["secondary"],
            hover_color=self.colors["secondary_hover"],
            text_color=self.colors["text_on_primary"],
            width=100
        )
        self.btn_export_all.pack(side="left")

        # Split button de envío Gmail (lado derecho)
        gmail_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        gmail_frame.pack(side="right")

        # Título para los botones de Gmail
        gmail_title = ctk.CTkLabel(
            gmail_frame,
            text="Enviar por Gmail",
            font=get_font_tuple("sm", "bold"),
            text_color=self.colors["text_primary"]
        )
        gmail_title.pack(anchor="w", pady=(0, get_spacing("xs")))

        # Frame para los botones de Gmail
        gmail_buttons_frame = ctk.CTkFrame(gmail_frame, fg_color="transparent")
        gmail_buttons_frame.pack()

        self.btn_send_current = ctk.CTkButton(
            gmail_buttons_frame,
            text="Actual",
            command=self._on_send_current_gmail,
            **BUTTON_SECONDARY,
            fg_color="#27ae60",  # Verde para Gmail
            hover_color="#229954",
            text_color="white",
            width=100
        )
        self.btn_send_current.pack(side="left", padx=(0, get_spacing("xs")))

        self.btn_send_all = ctk.CTkButton(
            gmail_buttons_frame,
            text="Todos",
            command=self._on_send_all_gmail,
            **BUTTON_SECONDARY,
            fg_color="#e67e22",  # Naranja para envío masivo
            hover_color="#d35400",
            text_color="white",
            width=100
        )
        self.btn_send_all.pack(side="left")

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
            # Usar precio correcto según el tipo de archivo
            precio = (
                Processing.LASTRES_PRICE_PER_TRIP
                if self.file_type == FileTypes.LASTRES
                else Processing.DEFAULT_PRICE_PER_TRIP
            )
            stats = calcular_estadisticas_viajes(df, precio_por_viaje=precio)
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
            precio = (
                Processing.LASTRES_PRICE_PER_TRIP
                if self.file_type == FileTypes.LASTRES
                else Processing.DEFAULT_PRICE_PER_TRIP
            )
            stats = calcular_estadisticas_viajes(df, precio_por_viaje=precio)
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

    def _on_send_current_gmail(self) -> None:
        """Envía el reporte actual por Gmail como borrador."""
        try:
            nombre_sel = self.display_var.get()
            codigo = self.codigo_por_nombre.get(nombre_sel, "")
            
            if not codigo:
                messagebox.showerror("Error", "No se pudo obtener el código del representado seleccionado")
                return
            
            # Ejecutar en hilo de fondo para no bloquear la UI
            thread = threading.Thread(
                target=self._send_gmail_background,
                args=(codigo, nombre_sel, False),
                daemon=True
            )
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error iniciando envío: {e}")

    def _on_send_all_gmail(self) -> None:
        """Envía todos los reportes por Gmail como borradores."""
        try:
            if not self.items_cod_nombre:
                messagebox.showinfo("Envío Gmail", "No hay representados con viajes en este período.")
                return
            
            # Ejecutar en hilo de fondo para no bloquear la UI
            thread = threading.Thread(
                target=self._send_gmail_background,
                args=(None, None, True),
                daemon=True
            )
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error iniciando envío masivo: {e}")

    def _send_gmail_background(self, codigo: Optional[str], nombre: Optional[str], send_all: bool) -> None:
        """
        Maneja el envío por Gmail en segundo plano.
        
        Args:
            codigo: Código del representado (solo para envío individual)
            nombre: Nombre del representado (solo para envío individual)
            send_all: Si True, envía a todos los representados
        """
        try:
            gmail_service = GmailDraftService()
            
            if send_all:
                # Envío masivo
                resultados = []
                representados_sin_email = []
                
                for cod, nom in self.items_cod_nombre:
                    resultado = self._create_gmail_draft_for_representado(gmail_service, cod, nom)
                    if resultado["success"]:
                        resultados.append(resultado)
                    else:
                        if "sin correo" in resultado["message"].lower():
                            representados_sin_email.append(nom)
                        else:
                            # Error real, mostrar inmediatamente
                            self.after(0, lambda msg=resultado["message"]: messagebox.showerror("Error Gmail", msg))
                            return
                
                # Mostrar resumen
                mensaje_resumen = f"Borradores creados: {len(resultados)}"
                if representados_sin_email:
                    mensaje_resumen += f"\nRepresentados sin correo: {len(representados_sin_email)}"
                    mensaje_resumen += f"\n({', '.join(representados_sin_email[:3])}" + ("..." if len(representados_sin_email) > 3 else "") + ")"
                
                self.after(0, lambda: messagebox.showinfo("Envío Gmail - Resumen", mensaje_resumen))
                
            else:
                # Envío individual
                resultado = self._create_gmail_draft_for_representado(gmail_service, codigo, nombre)
                self.after(0, lambda: messagebox.showinfo("Envío Gmail", resultado["message"]))
                
        except Exception as e:
            error_msg = f"Error en envío Gmail: {e}"
            self.after(0, lambda: messagebox.showerror("Error Gmail", error_msg))

    def _create_gmail_draft_for_representado(self, gmail_service: GmailDraftService, codigo: str, nombre: str) -> dict:
        """
        Crea un borrador de Gmail para un representado específico.
        
        Args:
            gmail_service: Instancia del servicio Gmail
            codigo: Código del representado
            nombre: Nombre del representado
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            # Obtener información de contacto
            contact_info = get_contact_info(codigo)
            if not contact_info or not contact_info.get("emails"):
                # Crear borrador sin destinatarios para que el usuario los complete
                contact_info = {
                    "emails": [],
                    "cc": ["mariel@sigmacargo.com.uy", "martin@sigmacargo.com.uy"],
                    "bcc": []
                }
                mensaje_contacto = f"Representado {nombre} sin correo configurado. Borrador creado sin destinatarios."
            else:
                mensaje_contacto = f"Borrador creado para {nombre}"
            
            # Generar PDF si no existe
            df = obtener_viajes_representado(self.df_original, codigo, self.periodo)
            if df.empty:
                return {
                    "success": False,
                    "message": f"No hay viajes para {nombre} en el período {self.periodo}"
                }
            
            # Usar columnas y precio según el tipo de archivo
            if self.file_type == FileTypes.LASTRES:
                columnas = Processing.LASTRES_COLUMNS_ORDER
                precio = Processing.LASTRES_PRICE_PER_TRIP
            else:
                columnas = DEFAULT_COLUMNS_ORDER  
                precio = Processing.DEFAULT_PRICE_PER_TRIP
                
            df = filtrar_columnas_relevantes(df, columnas=columnas, precio_por_viaje=precio)
            stats = calcular_estadisticas_viajes(df, precio_por_viaje=precio)
            
            # Generar PDF
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
            
            # Construir asunto y cuerpo del correo
            total_viajes = len(df)
            monto_total = stats.get("total", 0)
            
            asunto = f"Resumen de Viajes - {nombre} - {self.periodo}"
            
            cuerpo_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h2 style="color: #00587A; margin: 0;">Sigma Cargo</h2>
                        <p style="color: #666; margin: 5px 0;">Resumen de Viajes</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <h3 style="color: #00587A; margin-top: 0;">Estimado/a {nombre}</h3>
                        <p>Adjuntamos el resumen detallado de viajes correspondiente al período <strong>{self.periodo}</strong>.</p>
                        
                        <div style="background: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Código:</strong></td>
                                    <td style="padding: 8px 0; border-bottom: 1px solid #eee; text-align: right;">{codigo}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Total de viajes:</strong></td>
                                    <td style="padding: 8px 0; border-bottom: 1px solid #eee; text-align: right;">{total_viajes}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0;"><strong>Monto total:</strong></td>
                                    <td style="padding: 8px 0; text-align: right; color: #00587A; font-weight: bold;">$ {monto_total:,.0f}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <p>Para cualquier consulta o aclaración, no dude en contactarnos.</p>
                    </div>
                    
                    <div style="text-align: center; color: #666; font-size: 14px; border-top: 1px solid #eee; padding-top: 15px;">
                        <p><strong>Sigma Cargo</strong><br>
                        Email: mariel@sigmacargo.com.uy | martin@sigmacargo.com.uy</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Crear borrador
            resultado = gmail_service.create_draft_with_attachments(
                to_addresses=contact_info["emails"],
                cc_addresses=contact_info.get("cc", []),
                bcc_addresses=contact_info.get("bcc", []),
                subject=asunto,
                body=cuerpo_html,
                attachment_paths=[Path(ruta_pdf)]
            )
            
            if resultado["success"]:
                return {
                    "success": True,
                    "message": mensaje_contacto + f" (ID: {resultado.get('draft_id', 'N/A')})"
                }
            else:
                return {
                    "success": False,
                    "message": f"Error creando borrador para {nombre}: {resultado['message']}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error procesando {nombre}: {e}"
            }



def abrir_viajes_viewer(master, df_original: pd.DataFrame, codigos_representados: List[str], periodo: str, file_type: str = FileTypes.INGRESOS) -> None:
    ViajesViewer(master, df_original=df_original, codigos_representados=codigos_representados, periodo=periodo, file_type=file_type)


