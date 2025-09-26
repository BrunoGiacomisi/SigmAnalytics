# SigmAnalytics - Sistema de Análisis de Manifiestos

Sistema de calculo, análisis y visualización de datos de manifiestos para SIGMA CARGO, desarrollado en Python.

## 🚀 Características

- **Carga y visualización de datos**: Mediante un excel genera gráficos (boxplot, barras, series temporales)
- **Reportes PDF**: Generación de reportes individuales y masivos por representado
- **Envío por Gmail**: Creación automática de borradores con reportes adjuntos
- **Configuración**: Guardado automático de tamaño y posición de ventana
- **Base de datos**: Almacenamiento de histórico de análisis en SQlite
- **Validación**: Verificación automática de archivos y periodos

## 📋 Requisitos

- Python 3.8 o superior
- Windows 10/11 (probado en Windows 10)
- Dependencias listadas en `requirements.txt`
- wkhtmltopdf 0.12.x (opcional; requerido para exportar a PDF)
- Credenciales de Google Cloud (opcional; requerido para envío por Gmail)

## 📦 Ubicación de datos (Windows)

La aplicación guarda configuración, gráficos y base de datos en la carpeta de usuario (se crean automáticamente):

- Configuración: `C:\\Users\\<Usuario>\\AppData\\Local\\SigmAnalytics\\config.json`
- Histórico (SQLite): `C:\\Users\\<Usuario>\\AppData\\Local\\SigmAnalytics\\data\\historico\\historico.db`
- Contactos: `C:\\Users\\<Usuario>\\AppData\\Local\\SigmAnalytics\\data\\contactos_representados.json`
- Credenciales Gmail: `C:\\Users\\<Usuario>\\AppData\\Local\\SigmAnalytics\\auth\\`
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

## 📧 Configuración Gmail (Opcional)

Para habilitar el envío de reportes por Gmail:

1. **Crear proyecto en Google Cloud Console**:

   - Ir a [Google Cloud Console](https://console.cloud.google.com/)
   - Crear nuevo proyecto o seleccionar existente
   - Habilitar Gmail API

2. **Configurar credenciales OAuth**:

   - En "Credenciales", crear credenciales OAuth 2.0
   - Tipo de aplicación: "Aplicación de escritorio"
   - Descargar el archivo JSON de credenciales

3. **Colocar credenciales**:

   - Renombrar el archivo a `credentials.json`
   - Colocarlo en: `C:\\Users\\<Usuario>\\AppData\\Local\\SigmAnalytics\\auth\\credentials.json`

4. **Primera autorización**:
   - Al usar la función por primera vez, se abrirá el navegador para autorizar la aplicación
   - El token se guardará automáticamente para usos futuros

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

- Google APIs (gmail, auth-oauthlib) — integración con Gmail para envío automático de reportes como borradores

- PyInstaller — creación de ejecutables distribuibles de la aplicación completa
