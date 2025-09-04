import sys
from pathlib import Path
from src.constants import Colors, ChartTitles

def get_user_data_directory():
    # Obtiene la carpeta de datos del usuario de forma profesional.
    # Usa AppData/Local en Windows para mantener los datos separados del ejecutable.
    user_home = Path.home()
    
    # En Windows: C:\Users\Usuario\AppData\Local\SigmAnalytics
    # En otros sistemas: ~/.local/share/SigmAnalytics
    if sys.platform == "win32":
        app_data_dir = user_home / "AppData" / "Local" / "SigmAnalytics"
    else:
        app_data_dir = user_home / ".local" / "share" / "SigmAnalytics"
    
    # Crear estructura de carpetas si no existe
    app_data_dir.mkdir(parents=True, exist_ok=True)
    (app_data_dir / "outputs").mkdir(exist_ok=True)
    (app_data_dir / "data").mkdir(exist_ok=True)
    (app_data_dir / "data" / "historico").mkdir(exist_ok=True)
    
    return app_data_dir

def get_project_root():
    # Obtiene la raíz del proyecto (para archivos que deben estar junto al ejecutable).
    if getattr(sys, 'frozen', False):
        # Ejecutable compilado
        return Path(sys.executable).parent
    else:
        # Código fuente
        return Path(__file__).parent.parent

# Configurar directorios
USER_DATA_DIR = get_user_data_directory()
PROJECT_ROOT = get_project_root()

# Rutas de datos del usuario (se guardan en AppData)
CONFIG_FILE = USER_DATA_DIR / "config.json"
HISTORICO_DIR = USER_DATA_DIR / "data" / "historico"
GRAPHS_DIR = USER_DATA_DIR / "outputs"

# Rutas del proyecto (junto al ejecutable)
LOGO_PATH = PROJECT_ROOT / "src" / "assets" / "sigma_cargo_logo.png"
MANIFESTO_PATH = PROJECT_ROOT / "DatosManifiestoINGRESOS.xlsx"

# Rutas de gráficos específicos (nuevas rutas con nombres en mayúsculas)
RUTA_GRAFICO = GRAPHS_DIR / "serie_temporal.png"
RUTA_GRAFICO_PROMEDIOS = GRAPHS_DIR / "serie_promedios.png"
RUTA_BOXPLOT = GRAPHS_DIR / "boxplot_conteos.png"
RUTA_BARPLOT = GRAPHS_DIR / "barplot_representados.png"

# Rutas antiguas (para compatibilidad temporal)
ruta_manifesto = str(MANIFESTO_PATH)
ruta_db_historico = str(HISTORICO_DIR)
ruta_grafico = str(RUTA_GRAFICO)
ruta_grafico_promedios = str(RUTA_GRAFICO_PROMEDIOS)
ruta_boxplot = str(RUTA_BOXPLOT)
ruta_barplot = str(RUTA_BARPLOT)

# Constantes de textos y UI para dashboard (centralizadas en constants)
TITULO_BOXPLOT = ChartTitles.BOXPLOT
TITULO_BARRAS = ChartTitles.BARRAS
TITULO_PROMEDIOS = ChartTitles.PROMEDIOS
COLOR_EXITO = Colors.SUCCESS
COLOR_ERROR = Colors.ERROR
COLOR_TITULO = Colors.TITLE
TAMANO_IMAGEN = (600, 400)
TAMANO_POPUP = (900, 600)
TAMANO_POPUP_IMG = (850, 550)

# Configuración del logo de la empresa
LOGO_SIZE = (160, 160)

# Configuración por defecto de la aplicación
DEFAULT_CONFIG = {
    "window_size": "1100x700",
    "window_position": None,
    "logo_size": [160, 160],
    "data_directory": str(USER_DATA_DIR)
}

def show_data_directory_info():
    # Retorna información sobre dónde se guardan los datos para mostrar al usuario.
    return f"""
📁 Ubicación de datos de SigmAnalytics:

Configuración y datos:
{USER_DATA_DIR}

Subcarpetas:
• Configuración: {USER_DATA_DIR}
• Datos históricos: {HISTORICO_DIR}
• Gráficos generados: {GRAPHS_DIR}

NOTA: Los datos se guardan automáticamente en tu carpeta de usuario.
No necesitas crear estas carpetas manualmente.
"""
