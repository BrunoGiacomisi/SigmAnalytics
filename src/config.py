import sys
import os

def persistent_path(relative_path):
    # Siempre calcula la ruta desde la raíz del proyecto, incluso si está congelado
    if getattr(sys, 'frozen', False):
        # Si está congelado, sube dos niveles desde el ejecutable (dist/dashboard.exe)
        base_path = os.path.dirname(os.path.dirname(sys.executable))
    else:
        # Si está en desarrollo, sube dos niveles desde este archivo
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Rutas importadas en main
ruta_manifesto = persistent_path("DatosManifiestoINGRESOS.xlsx")
ruta_db_historico = persistent_path(os.path.join("..", "data", "historico"))
ruta_grafico = persistent_path(os.path.join("outputs", "serie_temporal.png"))
ruta_grafico_promedios = persistent_path(os.path.join("outputs", "serie_promedios.png"))
ruta_boxplot = persistent_path(os.path.join("outputs", "boxplot_conteos.png"))
ruta_barplot = persistent_path(os.path.join("outputs", "barplot_representados.png"))


# Constantes de textos y UI para dashboard
TITULO_BOXPLOT = "Boxplot: Distribución de Operaciones"
TITULO_BARRAS = "Barras: Top Representados + Medianas"
TITULO_PROMEDIOS = "Serie Temporal: Promedios"
MENSAJE_ARCHIVO_INVALIDO = "El archivo no contiene las columnas necesarias: 'Ag.transportista' y 'Nombre Ag.Transportista'."
MENSAJE_PROCESAMIENTO_EXITOSO = "✅ Procesamiento exitoso"
MENSAJE_PROCESAMIENTO_ERROR = "❌ Error en el procesamiento"
MENSAJE_ARCHIVO_VALIDO = "✅ Archivo válido"
MENSAJE_ARCHIVO_INVALIDO_ICONO = "❌ Archivo inválido"
MENSAJE_ERROR_LECTURA = "❌ Error al leer archivo"
COLOR_EXITO = "#43a047"
COLOR_ERROR = "#e53935"
COLOR_TITULO = "#00587A"
TAMANO_IMAGEN = (600, 400)
TAMANO_POPUP = (900, 600)
TAMANO_POPUP_IMG = (850, 550)

# Configuración del logo de la empresa
LOGO_PATH = "src/assets/sigma_cargo_logo.png"
LOGO_SIZE = (160, 160)  # Tamaño del logo en píxeles (aumentado de 80x80 a 120x120)

# Sistema de configuración persistente
CONFIG_FILE = "config.json"

# Configuración por defecto
DEFAULT_CONFIG = {
    "theme": "light",  # "light" o "dark"
    "window_size": "1100x700",  # Tamaño de ventana por defecto
    "window_position": None,  # Posición de ventana (se guardará automáticamente)
    "logo_size": [160, 160]  # Tamaño del logo
}

# Temas disponibles
THEMES = {
    "light": {
        "bg_color": "#f4f4f4",
        "frame_color": "#dedbd7",
        "text_color": "#002B45",
        "title_color": "#00587A",  # Azul oscuro para títulos en modo claro
        "accent_color": "#00587A",
        "hover_color": "#007399",
        "success_color": "#43a047",
        "error_color": "#d32f2f",
        "stats_bg": "#f8fafc",
        "stats_border": "#b0bec5"
    },
    "dark": {
        "bg_color": "#2d2d2d",  # Fondo menos oscuro para mejor contraste
        "frame_color": "#404040",  # Frame más claro
        "text_color": "#e0e0e0",  # Texto más claro para mejor legibilidad
        "title_color": "#ffffff",  # Blanco para títulos en modo oscuro
        "accent_color": "#4a9eff",
        "hover_color": "#66b3ff",
        "success_color": "#4caf50",
        "error_color": "#f44336",
        "stats_bg": "#4a4a4a",  # Fondo de estadísticas más claro
        "stats_border": "#666666"  # Borde más claro
    }
}
