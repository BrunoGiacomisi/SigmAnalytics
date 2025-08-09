import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from .pdf_renderer import render_html, export_pdf_from_html
from src.config import LOGO_PATH


DEFAULT_COLUMNS_ORDER: List[str] = [
    # Se elimina "Nombre Ag.Transportista" para evitar redundancia en el PDF
    "MIC/DNA",
    "Mic original",
    "Fecha ingreso",
    "Matricula",
    "Remolque/SemiRem",
    "Lugar partida",
    "Lugar destino",
    "Adu.Ing",
    "Precio",
]


def get_downloads_directory() -> Path:
    # Obtiene la carpeta de descargas del usuario de manera simple y portable.
    return Path.home() / "Downloads"


def _build_period_mask(df: pd.DataFrame, periodo: str, fecha_columna: str = "Fecha ingreso") -> pd.Series:
    # Crea una máscara booleana para filtrar por periodo ("YYYY-MM").
    fechas = pd.to_datetime(df[fecha_columna], errors="coerce")
    periodo_str = fechas.dt.strftime("%Y-%m")
    return periodo_str == periodo


def obtener_viajes_representado(
    df: pd.DataFrame,
    codigo_representado: str,
    periodo: str,
    columna_agente: str = "Ag.transportista",
    columna_fecha: str = "Fecha ingreso",
) -> pd.DataFrame:
    # Devuelve los viajes para un representado y periodo.
    df_filtrado = df.copy()
    mask_periodo = _build_period_mask(df_filtrado, periodo, fecha_columna=columna_fecha)
    mask_codigo = df_filtrado[columna_agente].astype(str) == str(codigo_representado)
    return df_filtrado[mask_periodo & mask_codigo]


def listar_representados_con_viajes(
    df: pd.DataFrame,
    codigos_representados: List[str],
    periodo: str,
    columna_agente: str = "Ag.transportista",
    columna_nombre: str = "Nombre Ag.Transportista",
    columna_fecha: str = "Fecha ingreso",
) -> List[Tuple[str, str]]:
    # Retorna una lista de (codigo, nombre) solo para los que viajaron en el período dado.
    df_local = df.copy()
    mask_periodo = _build_period_mask(df_local, periodo, fecha_columna=columna_fecha)
    mask_codigo = df_local[columna_agente].astype(str).isin([str(c) for c in codigos_representados])
    df_periodo = df_local[mask_periodo & mask_codigo]

    if df_periodo.empty:
        return []

    # Normalizar tipos y eliminar nulos
    df_periodo = df_periodo[[columna_agente, columna_nombre]].dropna()
    if df_periodo.empty:
        return []

    df_periodo[columna_agente] = df_periodo[columna_agente].astype(str)
    df_periodo[columna_nombre] = df_periodo[columna_nombre].astype(str)

    # Elegir un nombre por código (modo: más frecuente) y ordenar por nombre
    def pick_name(series: pd.Series) -> str:
        mode_vals = series.mode()
        if not mode_vals.empty:
            return str(mode_vals.iat[0])
        return str(series.iloc[0])

    name_by_code = df_periodo.groupby(columna_agente)[columna_nombre].agg(pick_name)
    items = [(code, name_by_code.loc[code]) for code in name_by_code.index]
    items.sort(key=lambda t: t[1].lower())
    return items


def filtrar_columnas_relevantes(
    df_viajes: pd.DataFrame,
    columnas: Optional[List[str]] = None,
    precio_por_viaje: float = 40.0,
) -> pd.DataFrame:
    # Mantiene solo columnas relevantes y agrega la columna Precio con el valor por viaje.
    columnas_finales = columnas or DEFAULT_COLUMNS_ORDER
    df_out = df_viajes.copy()
    df_out["Precio"] = float(precio_por_viaje)
    columnas_presentes = [c for c in columnas_finales if c in df_out.columns]
    # Asegurar que Precio esté si no venía del excel
    if "Precio" not in columnas_presentes:
        columnas_presentes.append("Precio")
    return df_out[columnas_presentes]


def calcular_estadisticas_viajes(
    df_viajes: pd.DataFrame,
    precio_por_viaje: float = 40.0,
) -> Dict[str, float]:
    # Calcula totales para el bloque seleccionado.
    cantidad = int(len(df_viajes))
    total = float(cantidad * float(precio_por_viaje))
    return {"cantidad_viajes": cantidad, "precio_por_viaje": float(precio_por_viaje), "total": total}


def formatear_datos_para_visualizacion(df_viajes: pd.DataFrame) -> pd.DataFrame:
    # Aplica formato amigable a fechas y números.
    df_out = df_viajes.copy()
    if "Fecha ingreso" in df_out.columns:
        df_out["Fecha ingreso"] = pd.to_datetime(df_out["Fecha ingreso"], errors="coerce").dt.strftime("%d-%m-%Y")
    if "Precio" in df_out.columns:
        df_out["Precio"] = df_out["Precio"].map(lambda x: f"$ {x:,.2f}")
    return df_out


def _draw_header(ax, metadata: Dict[str, str], logo_path: Optional[str] = None) -> None:
    # Dibuja un encabezado con el NOMBRE como título visible y metadatos debajo.
    ax.axis("off")

    # Título principal: Nombre del transportista
    nombre = metadata.get('nombre', '-')
    ax.text(0.02, 0.97, str(nombre), fontsize=18, fontweight="bold", va="top")

    # Línea divisoria sutil
    ax.hlines(0.925, xmin=0.02, xmax=0.98, colors="#666666", linewidth=0.5, transform=ax.transAxes)

    # Metadatos en lista con mayor separación para evitar solapado
    lines = [
        f"Código: {metadata.get('codigo','-')}",
        f"Período: {metadata.get('periodo','-')}",
        f"Total de viajes: {metadata.get('total_viajes','0')}",
        f"Monto total: $ {float(metadata.get('monto_total', 0)):.2f} ({metadata.get('total_viajes','0')} × $ {float(metadata.get('precio_por_viaje', 0)):.2f})",
    ]

    y = 0.89
    for line in lines:
        ax.text(0.03, y, f"• {line}", fontsize=11, va="top")
        y -= 0.055


def exportar_pdf_viajes(
    df_viajes_formateado: pd.DataFrame,
    metadata: Dict[str, str],
    output_pdf_path: Path,
    logo_path: Optional[str] = None,
) -> Path:
    # Genera PDF a partir de HTML+CSS para obtener un layout prolijo y paginado.
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    columnas = list(df_viajes_formateado.columns)
    filas = df_viajes_formateado.to_dict(orient="records")

    context = {
        "nombre": metadata.get("nombre", "-"),
        "codigo": metadata.get("codigo", "-"),
        "periodo": metadata.get("periodo", "-"),
        "total_viajes": metadata.get("total_viajes", "0"),
        "monto_total": f"{float(metadata.get('monto_total', 0)):.2f}",
        "columnas": columnas,
        "filas": filas,
        "logo_url": str(LOGO_PATH) if (logo_path or LOGO_PATH) else None,
    }

    html = render_html("viajes_report.html", context)
    css_path = Path(__file__).parent.parent / "templates" / "report.css"
    return export_pdf_from_html(html, css_path, output_pdf_path)


def generar_pdf_para_representado(
    df_original: pd.DataFrame,
    codigo: str,
    periodo: str,
    nombre_representado: Optional[str],
    precio_por_viaje: float = 40.0,
    columnas: Optional[List[str]] = None,
    logo_path: Optional[str] = None,
    downloads_dir: Optional[Path] = None,
) -> Path:
    # Genera el PDF para un representado específico y retorna la ruta.
    df_viajes = obtener_viajes_representado(df_original, codigo, periodo)
    df_viajes = filtrar_columnas_relevantes(df_viajes, columnas=columnas, precio_por_viaje=precio_por_viaje)
    stats = calcular_estadisticas_viajes(df_viajes, precio_por_viaje=precio_por_viaje)
    df_viajes_fmt = formatear_datos_para_visualizacion(df_viajes)

    downloads = downloads_dir or get_downloads_directory()

    # Normaliza nombre y periodo para el nombre del archivo
    def _sanitize(text: str) -> str:
        invalid = "\\/:*?\"<>|"
        out = ''.join(ch for ch in text if ch not in invalid)
        out = out.replace(' ', '_')
        return out

    nombre_comp = _sanitize(nombre_representado or codigo)
    # periodo esperado como YYYY-MM → YYYY_MM
    if '-' in periodo:
        anio, mes = periodo.split('-')[:2]
    elif '_' in periodo:
        anio, mes = periodo.split('_')[:2]
    else:
        anio, mes = periodo[:4], periodo[5:7] if len(periodo) >= 7 else ('', '')
    periodo_comp = f"{anio}_{mes}"

    file_name = f"Ingresos_{nombre_comp}_{periodo_comp}.pdf"
    output_pdf_path = downloads / file_name

    metadata = {
        "codigo": codigo,
        "nombre": nombre_representado or "-",
        "periodo": periodo,
        "total_viajes": str(stats["cantidad_viajes"]),
        "precio_por_viaje": str(stats["precio_por_viaje"]),
        "monto_total": str(stats["total"]),
    }

    return exportar_pdf_viajes(df_viajes_fmt, metadata, output_pdf_path, logo_path=logo_path)


