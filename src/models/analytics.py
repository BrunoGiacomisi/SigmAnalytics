import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src.models import db  # módulo que maneja la base de datos
import sys
import os

def resource_path(relative_path):
    # Obtiene la ruta absoluta al recurso, compatible con PyInstaller.
    try:
        # PyInstaller crea una carpeta temporal y almacena el path en _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# -----------------------------------------------
# Calcula la mediana de operaciones por transportista para representados y no representados
def calcular_mediana_conteo(
    df: pd.DataFrame,
    columna_agente: str,
    columna_nombre_agente: str,
    codigos_representados: list[str]
) -> tuple[float, float]:

    df_representados = df[df[columna_agente].astype(str).isin(codigos_representados)]
    df_otros = df[~df[columna_agente].astype(str).isin(codigos_representados)]

    mediana_rep = df_representados.groupby(columna_nombre_agente).size().median()
    mediana_otros = df_otros.groupby(columna_nombre_agente).size().median()

    return mediana_rep, mediana_otros

# -----------------------------------------------
# Calcula el % de participación de los representados respecto al total de viajes
def calcular_participacion(
    df: pd.DataFrame,
    columna_agente: str,
    codigos_representados: list[str]
) -> float:

    total = len(df)
    cantidad_rep = df[df[columna_agente].astype(str).isin(codigos_representados)].shape[0]
    participacion = 100 * cantidad_rep / total if total > 0 else 0
    return participacion

# -----------------------------------------------
# Actualiza el histórico si el período no existe aún
def actualizar_historico(
    df: pd.DataFrame,
    nombre_columna_fecha: str,
    mediana_rep: float,
    mediana_otros: float,
    promedio_rep: float,
    promedio_otros: float,
    participacion: float
) -> bool:

    import src.models.db as db
    periodo = db.obtener_periodo_desde_df(df, nombre_columna_fecha)

    if db.existe_periodo(periodo):  # Esta función está en models/db.py
        return False

    db.insertar_registro(periodo, mediana_rep, mediana_otros, promedio_rep, promedio_otros, participacion)
    return True

# -----------------------------------------------
# Gráfico de evolución mensual de las medianas
def generar_grafico_temporal(ruta_salida):
    historico = db.obtener_historico_completo()
    if historico.empty:
        return

    historico["periodo"] = pd.to_datetime(historico["periodo"], format="%Y-%m", errors='coerce')
    historico = historico.dropna(subset=["periodo"]).sort_values("periodo")

    plt.figure(figsize=(10, 6))
    plt.plot(historico["periodo"], historico["mediana_representados"], label="Representados", marker='o')
    plt.plot(historico["periodo"], historico["mediana_otros"], label="otros", marker='o')
    plt.xlabel("Mes")
    plt.ylabel("Mediana de Operaciones")
    plt.title("Evolución de Medianas")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(ruta_salida)
    plt.close()

# -----------------------------------------------
# Boxplot de representados vs. otros
def generar_boxplot_conteos(df, columna_agente, columna_nombre_agente, codigos_representados, ruta_salida):
    df["grupo"] = df[columna_agente].astype(str).apply(
        lambda x: "Representado" if x in codigos_representados else "Otros"
    )
    conteos = df.groupby([columna_nombre_agente, "grupo"]).size().reset_index(name="conteo")

    plt.figure(figsize=(8, 6))
    ax = sns.boxplot(x="grupo", y="conteo", data=conteos, showfliers=False)
    ax.set_ylim(0, 100)
    ax.set_yticks(range(0, 101, 10))
    plt.title("Distribución de operaciones")
    plt.xlabel("Condición")
    plt.ylabel("Cantidad de viajes")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(ruta_salida)
    plt.close()

# -----------------------------------------------
# Gráfico de barras horizontales: top 20 representados + medianas
def generar_barplot_representados(df, columna_agente, columna_nombre_agente, codigos_representados, mediana_rep, mediana_otros, ruta_salida):
    df_rep = df[df[columna_agente].astype(str).isin(codigos_representados)]
    conteos = df_rep.groupby(columna_nombre_agente).size().sort_values(ascending=False)

    data = conteos[:20].reset_index()
    data.columns = ["nombre", "cantidad"]

    data = pd.concat([data, pd.DataFrame({
        "nombre": ["Mediana Mercado", "Mediana Representados"],
        "cantidad": [mediana_otros, mediana_rep]
    })], ignore_index=True)

    colores = ["gray"] * (len(data) - 2) + ["red", "blue"]

    plt.figure(figsize=(12, 6))
    plt.barh(data["nombre"], data["cantidad"], color=colores)
    plt.xlabel("Cantidad de Viajes")
    plt.ylabel("Transportista")
    plt.title("Representados + Medianas vs. Mercado")
    plt.tight_layout()
    plt.savefig(ruta_salida)
    plt.close()

# -----------------------------------------------
# Calcula el promedio de operaciones por transportista para representados y no representados
def calcular_promedio_conteo(
    df: pd.DataFrame,
    columna_agente: str,
    columna_nombre_agente: str,
    codigos_representados: list[str]
) -> tuple[float, float]:
    # Calcula el promedio de operaciones por transportista para representados y no representados.
    df_representados = df[df[columna_agente].astype(str).isin(codigos_representados)]
    df_otros = df[~df[columna_agente].astype(str).isin(codigos_representados)]

    promedio_rep = df_representados.groupby(columna_nombre_agente).size().mean()
    promedio_otros = df_otros.groupby(columna_nombre_agente).size().mean()

    return promedio_rep, promedio_otros

# -----------------------------------------------
# Gráfico de evolución mensual de los promedios
def generar_grafico_promedios_temporal(ruta_salida):
    historico = db.obtener_historico_completo()
    if historico.empty:
        return

    historico["periodo"] = pd.to_datetime(historico["periodo"], format="%Y-%m", errors='coerce')
    historico = historico.dropna(subset=["periodo"]).sort_values("periodo")

    plt.figure(figsize=(10, 6))
    plt.plot(historico["periodo"], historico["promedio_representados"], label="Representados", marker='o')
    plt.plot(historico["periodo"], historico["promedio_otros"], label="otros", marker='o')
    plt.xlabel("Mes")
    plt.ylabel("Promedio de Operaciones")
    plt.title("Evolución de Promedios")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(ruta_salida)
    plt.close()
