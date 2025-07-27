# Assets - Recursos del Sistema

Esta carpeta contiene los recursos gráficos y archivos estáticos del sistema SigmAnalitics.

## Logo de la Empresa

Para agregar el logo de SIGMA CARGO:

1. **Nombre del archivo**: `sigma_cargo_logo.png`
2. **Formato**: PNG (recomendado) o JPG
3. **Tamaño recomendado**: Al menos 160x160 píxeles (se redimensionará automáticamente a 80x80)
4. **Ubicación**: Coloca el archivo directamente en esta carpeta

### Configuración

El logo se configura en `src/config.py`:

- `LOGO_PATH`: Ruta al archivo del logo
- `LOGO_SIZE`: Tamaño de visualización (80x80 píxeles)

### Fallback

Si el logo no se encuentra, el sistema mostrará automáticamente un ícono de edificio (🏢) como placeholder.

## Otros Assets

En el futuro, esta carpeta puede contener:

- Iconos del sistema
- Imágenes de fondo
- Templates de reportes
- Otros recursos gráficos
