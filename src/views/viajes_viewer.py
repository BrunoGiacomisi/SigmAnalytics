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
from src.config import LOGO_PATH
from src.models.pdf_renderer import build_report_html, TEMPLATES_DIR, is_wkhtmltopdf_available

try:  # WebView para previsualizar HTML (sin depender del navegador)
    from tkinterweb import HtmlFrame  # type: ignore
except Exception:  # fallback si no está disponible
    HtmlFrame = None  # type: ignore


class ViajesViewer(ctk.CTkToplevel):
    # Ventana para visualizar y exportar viajes por representado

    def __init__(self, master, df_original: pd.DataFrame, codigos_representados: List[str], periodo: str):
        super().__init__(master)
        self.title("Viajes por Representado")
        self.geometry("900x600")
        self.resizable(True, True)

        self.df_original = df_original
        # Mapear solo los que viajaron: [(codigo, nombre), ...]
        self.items_cod_nombre = listar_representados_con_viajes(df_original, codigos_representados, periodo)
        self.periodo = periodo

        # UI: controles superiores
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(header, text="Representado:").pack(side="left", padx=(10, 5))
        display_names = [name for _, name in self.items_cod_nombre]
        default_value = display_names[0] if display_names else ""
        self.display_var = ctk.StringVar(value=default_value)
        self.codigo_por_nombre = {name: code for code, name in self.items_cod_nombre}
        self.codigo_combo = ctk.CTkComboBox(
            header,
            values=display_names,
            variable=self.display_var,
            width=320,
            command=self._on_combo_change,
        )
        self.codigo_combo.pack(side="left")

        acciones = ctk.CTkFrame(self)
        acciones.pack(fill="x", padx=10, pady=5)

        self.btn_export = ctk.CTkButton(acciones, text="Exportar a PDF", command=self._on_export)
        self.btn_export.pack(side="left", padx=10)

        self.btn_export_all = ctk.CTkButton(acciones, text="Exportar todos a PDF", command=self._on_export_all)
        self.btn_export_all.pack(side="left", padx=10)

        # Aviso proactivo si falta wkhtmltopdf
        self._wkhtml_disponible = is_wkhtmltopdf_available()
        if not self._wkhtml_disponible:
            self.btn_export.configure(state="disabled")
            self.btn_export_all.configure(state="disabled")
            aviso = ctk.CTkLabel(
                acciones,
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
            self.transient(master)
            self.attributes('-topmost', True)
            self.lift()
            self.focus_force()
            self.after(400, lambda: self.attributes('-topmost', False))
        except Exception:
            pass

        self._on_preview()

    def _render_preview(self, df: pd.DataFrame) -> None:
        # Renderiza HTML de la plantilla para previsualizar con el mismo diseño del PDF
        if df.empty:
            html = "<div style='padding:16px;font-family:Segoe UI,Arial;color:#666'>No hay viajes para el período seleccionado.</div>"
        else:
            columnas = list(df.columns)
            filas = df.to_dict(orient="records")
            # Formateo de montos sin decimales para la previsualización
            def _fmt_money(value: float) -> str:
                try:
                    return f"{float(value):,.0f}"
                except Exception:
                    return str(value)

            context = {
                "nombre": self.display_var.get() or "-",
                "codigo": self.codigo_por_nombre.get(self.display_var.get(), "-"),
                "periodo": self.periodo,
                "total_viajes": str(len(df)),
                # En preview no recalcamos el total monetario exacto, lo formatea el PDF; aquí sumamos precios
                "monto_total": _fmt_money(sum([float(str(x).replace('$','').replace(',','').replace(' ','')) if 'Precio' in columnas else 0 for x in df.get('Precio', [])])),
                "columnas": columnas,
                "filas": filas,
                "logo_url": str(LOGO_PATH),
            }
            html = build_report_html(context)

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
        df_viajes = filtrar_columnas_relevantes(df_viajes, columnas=DEFAULT_COLUMNS_ORDER)
        df_viajes_fmt = formatear_datos_para_visualizacion(df_viajes)
        return df_viajes_fmt

    def _on_preview(self) -> None:
        try:
            df = self._collect_current_df()
            self._render_preview(df)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_combo_change(self, _value: str) -> None:
        # Actualiza previsualización inmediatamente al cambiar selección
        self._on_preview()

    def _on_export(self) -> None:
        try:
            nombre_sel = self.display_var.get()
            codigo = self.codigo_por_nombre.get(nombre_sel, "")
            df = obtener_viajes_representado(self.df_original, codigo, self.periodo)
            df = filtrar_columnas_relevantes(df, columnas=DEFAULT_COLUMNS_ORDER)
            stats = calcular_estadisticas_viajes(df)
            ruta_pdf = generar_pdf_para_representado(
                self.df_original,
                codigo=codigo,
                periodo=self.periodo,
                nombre_representado=nombre_sel or None,
                precio_por_viaje=stats["precio_por_viaje"],
                columnas=DEFAULT_COLUMNS_ORDER,
                logo_path=str(LOGO_PATH),
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
                df = filtrar_columnas_relevantes(df, columnas=DEFAULT_COLUMNS_ORDER)
                stats = calcular_estadisticas_viajes(df)
                ruta_pdf = generar_pdf_para_representado(
                    self.df_original,
                    codigo=codigo,
                    periodo=self.periodo,
                    nombre_representado=nombre,
                    precio_por_viaje=stats["precio_por_viaje"],
                    columnas=DEFAULT_COLUMNS_ORDER,
                    logo_path=str(LOGO_PATH),
                )
                generados.append(str(ruta_pdf))
            if generados:
                messagebox.showinfo("Exportación", "Los archivos se exportaron con éxito.")
            else:
                messagebox.showinfo("Exportación", "No se generó ningún PDF.")
        except Exception as e:
            messagebox.showerror("Error", str(e))


def abrir_viajes_viewer(master, df_original: pd.DataFrame, codigos_representados: List[str], periodo: str) -> None:
    ViajesViewer(master, df_original=df_original, codigos_representados=codigos_representados, periodo=periodo)


