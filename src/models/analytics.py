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
# Boxplot mejorado de representados vs. otros
def generar_boxplot_conteos(df, columna_agente, columna_nombre_agente, codigos_representados, ruta_salida):
    df = df.copy()  # Evitar modificar el DataFrame original
    df["grupo"] = df[columna_agente].astype(str).apply(
        lambda x: "Representados" if x in codigos_representados else "Mercado"
    )
    conteos = df.groupby([columna_nombre_agente, "grupo"]).size().reset_index(name="conteo")

    # Configurar figura con mejor tamaño
    plt.figure(figsize=(10, 6))
    plt.style.use('default')
    
    # Crear boxplot con colores personalizados
    ax = sns.boxplot(x="grupo", y="conteo", data=conteos, showfliers=False,
                     palette={"Representados": "#3498db", "Mercado": "#95a5a6"})
    
    # Personalizar límites y ticks del eje Y
    max_conteo = conteos["conteo"].max()
    ax.set_ylim(0, min(100, max_conteo * 1.1))
    
    # Personalizar título y etiquetas
    ax.set_title("Distribución de Operaciones por Transportista", 
                fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel("Grupo", fontsize=12, fontweight='bold')
    ax.set_ylabel("Cantidad de Viajes", fontsize=12, fontweight='bold')
    
    # Mejorar diseño
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Agregar estadísticas en el gráfico
    for i, grupo in enumerate(["Representados", "Mercado"]):
        data_grupo = conteos[conteos["grupo"] == grupo]["conteo"]
        if not data_grupo.empty:
            mediana = data_grupo.median()
            promedio = data_grupo.mean()
            
            # Agregar texto con estadísticas
            ax.text(i, ax.get_ylim()[1] * 0.9, 
                   f'Mediana: {mediana:.1f}\nPromedio: {promedio:.1f}',
                   ha='center', va='top', fontsize=9, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150, bbox_inches='tight')
    plt.close()

# -----------------------------------------------
# Gráfico de barras horizontales mejorado: top 15 representados + medianas
def generar_barplot_representados(df, columna_agente, columna_nombre_agente, codigos_representados, mediana_rep, mediana_otros, ruta_salida):
    df_rep = df[df[columna_agente].astype(str).isin(codigos_representados)]
    conteos = df_rep.groupby(columna_nombre_agente).size().sort_values(ascending=False)

    # Tomar top 15 para mejor legibilidad
    data = conteos[:15].reset_index()
    data.columns = ["nombre", "cantidad"]

    # Agregar medianas como referencia
    data = pd.concat([data, pd.DataFrame({
        "nombre": ["── Mediana Mercado ──", "── Mediana Representados ──"],
        "cantidad": [mediana_otros, mediana_rep]
    })], ignore_index=True)

    # Colores mejorados: azul para representados, rojo/verde para medianas
    colores = ["#3498db"] * len(conteos[:15]) + ["#e74c3c", "#27ae60"]

    # Configurar figura con mejor tamaño
    plt.figure(figsize=(12, 8))
    plt.style.use('default')
    
    # Crear barras horizontales
    bars = plt.barh(data["nombre"], data["cantidad"], color=colores, alpha=0.8, edgecolor='white', linewidth=0.5)
    
    # Agregar etiquetas de valor al final de cada barra
    for i, (bar, value) in enumerate(zip(bars, data["cantidad"])):
        plt.text(bar.get_width() + max(data["cantidad"]) * 0.01, bar.get_y() + bar.get_height()/2, 
                f'{int(value)}', ha='left', va='center', fontweight='bold', fontsize=9)
    
    # Personalizar ejes y título
    plt.xlabel("Cantidad de Viajes", fontsize=12, fontweight='bold')
    plt.ylabel("Transportista", fontsize=12, fontweight='bold')
    plt.title("Top Transportistas Representados vs. Medianas del Mercado", 
              fontsize=14, fontweight='bold', pad=20)
    
    # Mejorar diseño
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_color('#cccccc')
    plt.gca().spines['bottom'].set_color('#cccccc')
    plt.grid(axis='x', alpha=0.3, linestyle='--')
    
    # Invertir orden para que el mayor esté arriba
    plt.gca().invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150, bbox_inches='tight')
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
# Gráfico mejorado de evolución mensual de los promedios
def generar_grafico_promedios_temporal(ruta_salida):
    historico = db.obtener_historico_completo()
    if historico.empty:
        # Crear gráfico vacío con mensaje
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, 'No hay datos históricos disponibles', 
                ha='center', va='center', fontsize=14, transform=plt.gca().transAxes)
        plt.title("Evolución Mensual de Promedios", fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(ruta_salida, dpi=150, bbox_inches='tight')
        plt.close()
        return

    historico["periodo"] = pd.to_datetime(historico["periodo"], format="%Y-%m", errors='coerce')
    historico = historico.dropna(subset=["periodo"]).sort_values("periodo")

    # Configurar figura con mejor tamaño
    plt.figure(figsize=(12, 6))
    plt.style.use('default')
    
    # Crear líneas con mejor estilo
    plt.plot(historico["periodo"], historico["promedio_representados"], 
             label="Representados", marker='o', linewidth=2.5, 
             color="#3498db", markersize=6, markerfacecolor='white', 
             markeredgewidth=2, markeredgecolor="#3498db")
    
    plt.plot(historico["periodo"], historico["promedio_otros"], 
             label="Mercado", marker='s', linewidth=2.5, 
             color="#95a5a6", markersize=6, markerfacecolor='white', 
             markeredgewidth=2, markeredgecolor="#95a5a6")
    
    # Personalizar título y etiquetas
    plt.title("Evolución Mensual de Promedios de Operaciones", 
              fontsize=14, fontweight='bold', pad=20)
    plt.xlabel("Período", fontsize=12, fontweight='bold')
    plt.ylabel("Promedio de Operaciones", fontsize=12, fontweight='bold')
    
    # Mejorar leyenda
    plt.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
    
    # Mejorar diseño
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    ax.grid(alpha=0.3, linestyle='--')
    
    # Formatear fechas en el eje X
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150, bbox_inches='tight')
    plt.close()
