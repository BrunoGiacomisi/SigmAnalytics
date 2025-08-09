from pathlib import Path
import os
from typing import Dict, Any, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
import pdfkit
import shutil
import tempfile


TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def render_html(template_name: str, context: Dict[str, Any]) -> str:
    # Renderiza una plantilla HTML con Jinja2 usando el contexto provisto.
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_name)
    return template.render(**context)


def build_report_html(context: Dict[str, Any]) -> str:
    # Atajo específico para armar el HTML del reporte de viajes
    return render_html("viajes_report.html", context)


def _has_wkhtmltopdf() -> Optional[str]:
    # Devuelve ruta del ejecutable de wkhtmltopdf si existe en PATH o ubicaciones comunes de Windows.
    # 1) PATH
    exe = shutil.which("wkhtmltopdf")
    if exe:
        return exe
    # 2) Variable de entorno explícita
    env_path = os.environ.get("WKHTMLTOPDF_BINARY") or os.environ.get("WKHTMLTOPDF_PATH")
    if env_path and Path(env_path).exists():
        return env_path
    # 3) Rutas típicas en Windows (soporta localización de nombre de carpeta)
    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\\Program Files")) / "wkhtmltopdf" / "bin" / "wkhtmltopdf.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)")) / "wkhtmltopdf" / "bin" / "wkhtmltopdf.exe",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    # 4) Búsqueda amplia (último recurso)
    for base in filter(None, [
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        r"C:\\Program Files",
        r"C:\\Program Files (x86)",
    ]):
        base_path = Path(base)
        if base_path.exists():
            try:
                for found in base_path.rglob("wkhtmltopdf.exe"):
                    return str(found)
            except Exception:
                pass
    return None


def export_pdf_from_html(html_content: str, css_path: Optional[Path], output_pdf: Path) -> Path:
    # Convierte HTML+CSS a PDF usando wkhtmltopdf (opción predeterminada y recomendada en Windows).
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    wkhtml = _has_wkhtmltopdf()
    if not wkhtml:
        raise RuntimeError(
            "No se encontró wkhtmltopdf. Instálalo o configura WKHTMLTOPDF_BINARY apuntando al ejecutable."
        )
    # Encabezado condicional: se muestra 'Página X de Y' solo si hay más de una página.
    # wkhtmltopdf no permite condición directa, pero un truco común es pintar el header
    # y usar CSS para ocultarlo cuando es '1 de 1'. Sin soporte de variables en CSS
    # de wkhtmltopdf, optamos por SIEMPRE mostrar el header en PDF y ocultarlo en la
    # previsualización HTML. Como compromiso práctico, lo dejamos visible en PDF.
    # Usar header-right con tokens nativos de wkhtmltopdf (más fiable en Windows)
    options = {
        "encoding": "UTF-8",
        "quiet": "",
        # márgenes similares a CSS @page
        "margin-top": "18mm",
        "margin-right": "16mm",
        "margin-bottom": "16mm",
        "margin-left": "16mm",
        "enable-local-file-access": None,
        # Header con numeración de páginas (siempre visible en PDF)
        "header-spacing": "4",
        "header-right": "Página [page] de [toPage]",
        "header-font-size": "9",
    }
    css_arg = [str(css_path)] if css_path else None
    pdfkit.from_string(
        html_content,
        str(output_pdf),
        css=css_arg,
        options=options,
        configuration=pdfkit.configuration(wkhtmltopdf=wkhtml),
    )
    return output_pdf


