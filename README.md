# SigmAnalytics - Sistema de Análisis de Manifiestos

Sistema de calculo, análisis y visualización de datos de manifiestos para SIGMA CARGO, desarrollado en Python.

## 🚀 Características

- **Carga y visualización de datos**: Mediante un excel genera gráficos (boxplot, barras, series temporales)
- **Configuración**: Guardado automático de tamaño y posición de ventana
- **Base de datos**: Almacenamiento de histórico de análisis en SQlite
- **Validación**: Verificación automática de archivos y periodos

## 📋 Requisitos

- Python 3.8 o superior
- Windows 10/11 (probado en Windows 10)
- Dependencias listadas en `requirements.txt`
- wkhtmltopdf 0.12.x (opcional; requerido para exportar a PDF)

## 📦 Ubicación de datos (Windows)

La aplicación guarda configuración, gráficos y base de datos en la carpeta de usuario (se crean automáticamente):

- Configuración: `C:\\Users\\<Usuario>\\AppData\\Local\\SigmAnalytics\\config.json`
- Histórico (SQLite): `C:\\Users\\<Usuario>\\AppData\\Local\\SigmAnalytics\\data\\historico\\historico.db`
- Gráficos: `C:\\Users\\<Usuario>\\AppData\\Local\\SigmAnalytics\\outputs\\`

Desde la app podés ver esta información con el botón "Datos" del dashboard.

## 🖨️ Exportar a PDF

La exportación a PDF usa wkhtmltopdf (Windows recomendado, versión 0.12.x).

1. Instalar wkhtmltopdf en Windows:

- Descargá el instalador desde la página oficial.
- Durante la instalación, asegurate de incluir el componente "wkhtmltopdf" en PATH.

2. Alternativa: variable de entorno si no está en PATH

- Definí una de estas variables apuntando al ejecutable:
  - `WKHTMLTOPDF_BINARY` o `WKHTMLTOPDF_PATH`
  - Ejemplo: `C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe`

## 📊 Funcionalidades de Análisis

### Métricas calculadas:

- **Mediana y promedio** de operaciones por agente
- **Participación** de agentes representados
- **Conteo de viajes** por categoría
- **Evolución temporal** de métricas, comparando el mercado con la empresa

### Gráficos generados:

- **Boxplot**: Distribución de operaciones
- **Barras**: Top representados y medianas
- **Serie temporal**: Promedios a lo largo del tiempo
- **Grafico de torta**: Viajes (lastre o ingreso) por transportista dentro del total

### Stack utilizado:

- Python 3 — lenguaje base y punto de entrada de la aplicación

- Pandas + NumPy + OpenPyXL — leer planillas de Excel y procesar los datos en DataFrames

- CustomTkinter — interfaz gráfica moderna sobre Tkinter (ventana principal, temas, widgets)

- Pillow — carga y manejo de imágenes (logo, íconos) dentro de la GUI

- Matplotlib + Seaborn — generación de boxplots, barras y series temporales para análisis visual

- SQLite 3 — base de datos local para guardar métricas históricas de períodos

- Jinja2 + pdfkit + wkhtmltopdf — renderizado de plantillas HTML y conversión a PDF para reportes por representado

- TkinterWeb — previsualización embebida de HTML en la interfaz antes de exportar a PDF

- PyInstaller — creación de ejecutables distribuibles de la aplicación completa
