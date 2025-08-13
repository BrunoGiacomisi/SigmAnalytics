# Constantes centralizadas para la aplicación SigmAnalytics

# Columnas del DataFrame principales
class Columns:
    AGENT_CODE = "Ag.transportista"
    AGENT_NAME = "Nombre Ag.Transportista"
    DATE = "Fecha ingreso"
    PRICE = "Precio"

# Configuración de procesamiento
class Processing:
    DEFAULT_PRICE_PER_TRIP = 40.0
    DEFAULT_COLUMNS_ORDER = [
        "Fecha ingreso",
        "Nombre Ag.Transportista", 
        "Ag.transportista",
        "Precio"
    ]

# Configuración de gráficos
class Charts:
    DPI = 150
    FIGSIZE_DEFAULT = (12, 8)
    FIGSIZE_BOXPLOT = (10, 6)
    TOP_TRANSPORTISTAS = 10
    
# Configuración de UI
class UI:
    MIN_WINDOW_SIZE = (800, 600)
    DEFAULT_WINDOW_SIZE = "1100x700"
    DASHBOARD_SIZE = "1200x800"
    TABLA_DINAMICA_SIZE = "1430x890"
    
    # Tamaños de imagen
    LOGO_SIZE = (160, 160)
    IMAGE_SIZE = (600, 400)
    POPUP_SIZE = (900, 600)
    POPUP_IMG_SIZE = (850, 550)

# Mensajes de la aplicación
class Messages:
    ARCHIVO_INVALIDO = "El archivo no contiene las columnas necesarias: 'Ag.transportista' y 'Nombre Ag.Transportista'."
    PROCESAMIENTO_EXITOSO = "✅ Procesamiento exitoso"
    PROCESAMIENTO_ERROR = "❌ Error en el procesamiento"
    ARCHIVO_VALIDO = "✅ Archivo válido"
    ARCHIVO_INVALIDO_ICONO = "❌ Archivo inválido"
    ERROR_LECTURA = "❌ Error al leer archivo"

# Colores de la aplicación
class Colors:
    SUCCESS = "#43a047"
    ERROR = "#e53935"
    TITLE = "#00587A"
    
# Títulos de gráficos
class ChartTitles:
    BOXPLOT = "Boxplot: Distribución de Operaciones"
    BARRAS = "Barras: Top Representados + Medianas"
    PROMEDIOS = "Serie Temporal: Promedios"
    TEMPORAL = "Evolución Temporal de Medianas"
