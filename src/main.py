import os
import sys
from src.models import db
from src.models import data_loader, analytics
from src.config import (
    RUTA_GRAFICO, RUTA_GRAFICO_PROMEDIOS, MANIFESTO_PATH,
    HISTORICO_DIR, GRAPHS_DIR
)

db.crear_tabla_si_no_existe()

# -----------------------------------------------------------
# Esta función centraliza todo el procesamiento del manifiesto:
# cálculo de métricas, actualización de histórico y generación de gráficos
def procesar_archivo(
    ruta_manifesto: str,
    codigos: list[str] ) -> tuple:

    # Verificar que el archivo existe
    if not os.path.exists(ruta_manifesto):
        raise FileNotFoundError(f"El archivo no existe: {ruta_manifesto}")
    
    # Verificar que los códigos no estén vacíos
    if not codigos:
        raise ValueError("La lista de códigos no puede estar vacía")
    
    # 1. Cargar el archivo Excel
    df = data_loader.cargar_manifesto(ruta_manifesto)

    # 2. Definir nombres de columnas clave
    columna_agente = "Ag.transportista"
    nombre_agente = "Nombre Ag.Transportista"
    columna_fecha = "Fecha ingreso"

    # 3. Calcular métricas principales
    mediana_rep, mediana_otros = analytics.calcular_mediana_conteo(df, columna_agente, nombre_agente, codigos)
    promedio_rep, promedio_otros = analytics.calcular_promedio_conteo(df, columna_agente, nombre_agente, codigos)
    participacion = analytics.calcular_participacion(df, columna_agente, codigos)
    viajes_representados = df[df[columna_agente].astype(str).isin(codigos)].shape[0]

    # 4. Determinar el periodo del archivo (ej: '2025-06')
    periodo = db.obtener_periodo_desde_df(df, columna_fecha)
    periodo_mas_reciente = db.get_periodo_mas_reciente()

    # 5. Si el periodo es igual o anterior al más reciente, solo mostrar preview
    if periodo_mas_reciente is not None and periodo <= periodo_mas_reciente:
        # Carpeta temporal para preview
        carpeta_preview = GRAPHS_DIR / "preview"
        carpeta_preview.mkdir(exist_ok=True)
        ruta_boxplot_preview = carpeta_preview / "boxplot_conteos.png"
        ruta_barplot_preview = carpeta_preview / "barplot_representados.png"
        # Generar gráficos solo para mostrar
        analytics.generar_boxplot_conteos(df, columna_agente, nombre_agente, codigos, str(ruta_boxplot_preview))
        analytics.generar_barplot_representados(df, columna_agente, nombre_agente, codigos, mediana_rep, mediana_otros, str(ruta_barplot_preview))
        # Devuelve métricas, rutas de preview y flag de preview
        return (mediana_rep, mediana_otros, promedio_rep, promedio_otros, participacion, False, viajes_representados, str(ruta_boxplot_preview), str(ruta_barplot_preview), True)

    # 6. Si el periodo es nuevo, guardar en la base y generar gráficos en carpeta del periodo
    carpeta_graficos = GRAPHS_DIR / f"graficos_{periodo}"
    carpeta_graficos.mkdir(exist_ok=True)
    ruta_boxplot_periodo = carpeta_graficos / "boxplot_conteos.png"
    ruta_barplot_periodo = carpeta_graficos / "barplot_representados.png"

    # Guardar en la base de datos si corresponde
    actualizado = analytics.actualizar_historico(
        df, columna_fecha, mediana_rep, mediana_otros, promedio_rep, promedio_otros, participacion
    )

    # Generar gráficos de evolución temporal (no dependen del periodo)
    analytics.generar_grafico_temporal(str(RUTA_GRAFICO))
    analytics.generar_grafico_promedios_temporal(str(RUTA_GRAFICO_PROMEDIOS))

    # Generar gráficos del periodo
    analytics.generar_boxplot_conteos(df, columna_agente, nombre_agente, codigos, str(ruta_boxplot_periodo))
    analytics.generar_barplot_representados(df, columna_agente, nombre_agente, codigos, mediana_rep, mediana_otros, str(ruta_barplot_periodo))

    # Devuelve métricas, rutas de gráficos y flag de preview (False)
    return (mediana_rep, mediana_otros, promedio_rep, promedio_otros, participacion, actualizado, viajes_representados, str(ruta_boxplot_periodo), str(ruta_barplot_periodo), False)


if __name__ == "__main__":
    from src.views.dashboard import crear_dashboard
    crear_dashboard()

