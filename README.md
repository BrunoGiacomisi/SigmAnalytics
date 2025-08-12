# SigmAnalytics - Sistema de Análisis de Manifiestos

Sistema de análisis y visualización de datos de manifiestos para SIGMA CARGO, desarrollado en Python con interfaz gráfica moderna.

## 🚀 Características

- **Análisis de datos**: Procesamiento automático de archivos Excel de manifiestos
- **Visualización**: Generación de gráficos (boxplot, barras, series temporales)
- **Temas**: Modo claro y oscuro con persistencia de preferencias
- **Configuración**: Guardado automático de tamaño y posición de ventana
- **Base de datos**: Almacenamiento de histórico de análisis
- **Validación**: Verificación automática de archivos y periodos

## 📋 Requisitos

- Python 3.8 o superior
- Windows 10/11 (probado en Windows 10)
- Dependencias listadas en `requirements.txt`
- wkhtmltopdf 0.12.x (opcional; requerido para exportar a PDF)

## 🛠️ Instalación

1. **Clonar el repositorio:**

   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd SigmAnalytics
   ```

2. **Crear entorno virtual:**

   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

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

3. Verificación dentro de la app

- En el visualizador de viajes, la app te avisará si wkhtmltopdf no está disponible y deshabilitará los botones de exportación.

## 📊 Funcionalidades de Análisis

### Métricas calculadas:

- **Mediana y promedio** de operaciones por agente
- **Participación** de agentes representados
- **Conteo de viajes** por categoría
- **Evolución temporal** de métricas

### Gráficos generados:

- **Boxplot**: Distribución de operaciones
- **Barras**: Top representados y medianas
- **Serie temporal**: Promedios a lo largo del tiempo

## 📝 Licencia

Este proyecto es propiedad de SIGMA CARGO. Todos los derechos reservados.

## 📞 Soporte

Para soporte técnico o consultas:

- Contactar al equipo de desarrollo
- Revisar la documentación en este README
- Verificar los logs en caso de errores

---

**Versión**: 1.0.0  
**Última actualización**: Julio 2025  
**Desarrollado por**: Equipo de Desarrollo SIGMA CARGO
