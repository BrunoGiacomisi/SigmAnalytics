import os
import sys
from src.models import db
from src.models import data_loader, analytics
from src.config import (
    RUTA_GRAFICO, RUTA_GRAFICO_PROMEDIOS, MANIFESTO_PATH,
    HISTORICO_DIR, GRAPHS_DIR
)


# -----------------------------------------------------------
# Esta función centraliza todo el procesamiento del manifiesto:
# cálculo de métricas, actualización de histórico y generación de gráficos
def _procesar_df(df, codigos: list[str]):
    # Define columnas clave
    columna_agente = "Ag.transportista"
    nombre_agente = "Nombre Ag.Transportista"
    columna_fecha = "Fecha ingreso"

    # Métricas
    mediana_rep, mediana_otros = analytics.calcular_mediana_conteo(df, columna_agente, nombre_agente, codigos)
    promedio_rep, promedio_otros = analytics.calcular_promedio_conteo(df, columna_agente, nombre_agente, codigos)
    participacion = analytics.calcular_participacion(df, columna_agente, codigos)
    viajes_representados = df[df[columna_agente].astype(str).isin(codigos)].shape[0]

    # Periodo
    periodo = db.obtener_periodo_desde_df(df, columna_fecha)
    periodo_mas_reciente = db.get_periodo_mas_reciente()

    # Preview si corresponde
    if periodo_mas_reciente is not None and periodo <= periodo_mas_reciente:
        carpeta_preview = GRAPHS_DIR / "preview"
        carpeta_preview.mkdir(exist_ok=True)
        ruta_boxplot_preview = carpeta_preview / "boxplot_conteos.png"
        ruta_barplot_preview = carpeta_preview / "barplot_representados.png"
        analytics.generar_boxplot_conteos(df, columna_agente, nombre_agente, codigos, str(ruta_boxplot_preview))
        analytics.generar_barplot_representados(df, columna_agente, nombre_agente, codigos, mediana_rep, mediana_otros, str(ruta_barplot_preview))
        return (mediana_rep, mediana_otros, promedio_rep, promedio_otros, participacion, False, viajes_representados, str(ruta_boxplot_preview), str(ruta_barplot_preview), True)

    # Carpeta por período
    carpeta_graficos = GRAPHS_DIR / f"graficos_{periodo}"
    carpeta_graficos.mkdir(exist_ok=True)
    ruta_boxplot_periodo = carpeta_graficos / "boxplot_conteos.png"
    ruta_barplot_periodo = carpeta_graficos / "barplot_representados.png"

    actualizado = analytics.actualizar_historico(
        df, columna_fecha, mediana_rep, mediana_otros, promedio_rep, promedio_otros, participacion
    )

    analytics.generar_grafico_temporal(str(RUTA_GRAFICO))
    analytics.generar_grafico_promedios_temporal(str(RUTA_GRAFICO_PROMEDIOS))

    analytics.generar_boxplot_conteos(df, columna_agente, nombre_agente, codigos, str(ruta_boxplot_periodo))
    analytics.generar_barplot_representados(df, columna_agente, nombre_agente, codigos, mediana_rep, mediana_otros, str(ruta_barplot_periodo))

    return (mediana_rep, mediana_otros, promedio_rep, promedio_otros, participacion, actualizado, viajes_representados, str(ruta_boxplot_periodo), str(ruta_barplot_periodo), False)


def procesar_archivo(
    ruta_manifesto: str,
    codigos: list[str]
) -> tuple:
    if not os.path.exists(ruta_manifesto):
        raise FileNotFoundError(f"El archivo no existe: {ruta_manifesto}")
    if not codigos:
        raise ValueError("La lista de códigos no puede estar vacía")
    df = data_loader.cargar_manifesto(ruta_manifesto)
    return _procesar_df(df, codigos)


def procesar_df(df, codigos: list[str]) -> tuple:
    if df is None or df.empty:
        raise ValueError("El DataFrame está vacío o no es válido")
    if not codigos:
        raise ValueError("La lista de códigos no puede estar vacía")
    return _procesar_df(df, codigos)


if __name__ == "__main__":
    from src.views.dashboard import crear_dashboard
    crear_dashboard()

