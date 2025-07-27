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

## 🎯 Uso

### Ejecutar la aplicación:

```bash
python -m src.main
```

### Funcionalidades principales:

1. **Procesar manifiesto**: Selecciona un archivo Excel para analizar
2. **Cambiar tema**: Usa el botón "Modo Claro/Oscuro" en la esquina superior derecha
3. **Ver gráficos**: Los gráficos se generan automáticamente y se pueden ampliar
4. **Configuración**: El sistema recuerda tus preferencias automáticamente

## 📁 Estructura del Proyecto

```
SigmAnalytics/
├── src/
│   ├── main.py              # Punto de entrada principal
│   ├── config.py            # Configuraciones y constantes
│   ├── models/
│   │   ├── db.py            # Base de datos
│   │   ├── analytics.py     # Lógica de análisis
│   │   ├── data_loader.py   # Carga de datos
│   │   ├── config_manager.py # Gestión de configuración
│   │   └── theme_manager.py # Gestión de temas
│   ├── views/
│   │   └── dashboard.py     # Interfaz gráfica
│   ├── controllers/         # Lógica de control
│   ├── assets/              # Recursos (logos, imágenes)
│   └── data/                # Datos y base de datos
├── outputs/                 # Gráficos generados
├── venv/                    # Entorno virtual
├── config.json              # Configuración del usuario
├── .gitignore              # Archivos a ignorar en Git
└── README.md               # Este archivo
```

## 🔧 Configuración

### Archivos de configuración:

- `config.json`: Preferencias del usuario (tema, tamaño de ventana, etc.)
- `src/config.py`: Configuraciones del sistema y temas

### Personalización:

- **Logo**: Coloca `sigma_cargo_logo.png` en `src/assets/`
- **Temas**: Modifica los colores en `src/config.py`
- **Base de datos**: Ubicada en `src/data/historico`

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

## 🔒 Seguridad

### Archivos sensibles excluidos:

- `config.json` (preferencias personales)
- `outputs/` (gráficos generados)
- `*.exe` (ejecutables compilados)
- `venv/` (entorno virtual)

### Buenas prácticas implementadas:

- Separación de datos y código
- Validación de archivos de entrada
- Manejo de errores robusto
- Configuración persistente segura

## 🚀 Desarrollo

### Comandos útiles:

```bash
# Activar entorno virtual
venv\Scripts\activate

# Ejecutar en modo desarrollo
python -m src.main

# Compilar ejecutable
pyinstaller --onefile --windowed src/main.py
```

### Estructura de commits recomendada:

```bash
git add .
git commit -m "feat: nueva funcionalidad"
git commit -m "fix: corrección de bug"
git commit -m "refactor: mejora de código"
```

## 📝 Licencia

Este proyecto es propiedad de SIGMA CARGO. Todos los derechos reservados.

## 🤝 Contribución

Para contribuir al proyecto:

1. Crear una rama para tu feature
2. Implementar los cambios
3. Crear un pull request
4. Esperar revisión y aprobación

## 📞 Soporte

Para soporte técnico o consultas:

- Contactar al equipo de desarrollo
- Revisar la documentación en este README
- Verificar los logs en caso de errores

---

**Versión**: 1.0.0  
**Última actualización**: Julio 2025  
**Desarrollado por**: Equipo de Desarrollo SIGMA CARGO
