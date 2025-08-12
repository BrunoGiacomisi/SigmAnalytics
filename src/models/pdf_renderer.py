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
    # Genera el HTML del reporte de viajes con diseño claro (estándar para PDFs)
    context_with_css = {**context, "css_file": "report.css"}
    return render_html("viajes_report.html", context_with_css)


def is_wkhtmltopdf_available() -> bool:
    # Retorna True si se encuentra wkhtmltopdf accesible en el sistema.
    return _has_wkhtmltopdf() is not None


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
            (
                "Falta el binario 'wkhtmltopdf'.\n"
                "1) Descárgalo e instálalo en Windows (versión 0.12.x).\n"
                "2) O define la variable de entorno WKHTMLTOPDF_BINARY/WKHTMLTOPDF_PATH apuntando al ejecutable."
            )
        )


    options = {
        "encoding": "UTF-8",
        "quiet": "",
        # márgenes similares a CSS @page
        "margin-top": "16mm",
        "margin-right": "14mm",
        "margin-bottom": "14mm",
        "margin-left": "14mm",
        "enable-local-file-access": None,
        # Header con numeración de páginas (siempre visible en PDF)
        "header-spacing": "4",
        "header-right": "Página [page] de [toPage]",
        "header-font-size": "9",
    }
    css_arg = [str(css_path)] if css_path else None
    try:
        pdfkit.from_string(
            html_content,
            str(output_pdf),
            css=css_arg,
            options=options,
            configuration=pdfkit.configuration(wkhtmltopdf=wkhtml),
        )
    except OSError as e:
        # Errores típicos cuando wkhtmltopdf no está accesible o hay problemas de permisos
        raise RuntimeError(f"Error al generar PDF con wkhtmltopdf: {e}")
    return output_pdf


