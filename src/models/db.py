import sqlite3  # Módulo estándar de Python para trabajar con bases de datos SQLite
import pandas as pd  # Librería para manipulación de datos, usamos esto para leer la base a un DataFrame
from typing import Optional
import sys
import os
from src.config import HISTORICO_DIR

def persistent_path(relative_path):
    # Deprecated: mantenido por compatibilidad si algún código externo lo usa.
    base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    return os.path.abspath(os.path.join(base_path, os.path.basename(relative_path)))

# Ruta donde se guardará (o ya existe) la base de datos SQLite (en AppData del usuario)
DB_PATH = os.path.join(str(HISTORICO_DIR), 'historico.db')
os.makedirs(str(HISTORICO_DIR), exist_ok=True)

# -------------------------------------------------------------------------
# Crea la tabla 'historico' si todavía no existe en la base de datos
# -------------------------------------------------------------------------
def crear_tabla_si_no_existe() -> None:
    conexion = sqlite3.connect(DB_PATH)  # Se conecta (o crea) la base de datos
    cursor = conexion.cursor()  # Crea un cursor para ejecutar sentencias SQL

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            periodo TEXT PRIMARY KEY,                -- Ej: "2024-05"
            mediana_representados REAL,              -- Valor numérico de mediana (representados)
            mediana_otros REAL,                      -- Valor numérico de mediana (no representados)
            promedio_representados REAL,             -- Valor numérico de promedio (representados)
            promedio_otros REAL,                     -- Valor numérico de promedio (no representados)
            participacion REAL                       -- porcentaje de participación
        )
    """)  # Solo se crea si no existe ya

    conexion.commit()  # Guarda los cambios
    conexion.close()   # Cierra la conexión

# -------------------------------------------------------------------------
# Verifica si un período ya está registrado (opcionalmente permite ruta distinta)
# -------------------------------------------------------------------------
def existe_periodo(periodo: str, ruta_db: str = DB_PATH) -> bool:
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM historico WHERE periodo = ?", (periodo,))
    resultado = cursor.fetchone()[0]  # Nos devuelve el número de coincidencias
    conexion.close()
    return resultado > 0  # Devuelve True si existe, False si no

# -------------------------------------------------------------------------
# Inserta un nuevo registro al histórico, si no existe el período todavía
# -------------------------------------------------------------------------
def insertar_registro(
    periodo: str,
    mediana_rep: float,
    mediana_otros: float,
    promedio_rep: float,
    promedio_otros: float,
    participacion: float
) -> bool:
    # Inserta un nuevo registro al histórico, si no existe el período todavía.
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    # Verifica si ya hay un registro con ese mismo período
    cursor.execute("SELECT COUNT(*) FROM historico WHERE periodo = ?", (periodo,))
    existe = cursor.fetchone()[0] > 0

    if not existe:
        # Si no existe, inserta los datos
        cursor.execute("""
            INSERT INTO historico (periodo, mediana_representados, mediana_otros, promedio_representados, promedio_otros, participacion)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (periodo, mediana_rep, mediana_otros, promedio_rep, promedio_otros, participacion))
        conexion.commit()  # Aplica los cambios

    conexion.close()  # Siempre cerramos la conexión
    return not existe  # Devuelve True si se insertó, False si ya existía

# Extrae el período en formato "YYYY-MM" desde la columna de fechas
def obtener_periodo_desde_df(df: pd.DataFrame, nombre_columna_fecha: str) -> str:
    fechas_validas = pd.to_datetime(df[nombre_columna_fecha], errors='coerce').dropna()
    if fechas_validas.empty:
        raise ValueError("No se encontraron fechas válidas en la columna especificada.")
    fecha = fechas_validas.iloc[0]
    return f"{fecha.year}-{fecha.month:02d}"

# -------------------------------------------------------------------------
# Devuelve un DataFrame con todos los registros del histórico, ordenado por período
# -------------------------------------------------------------------------
def obtener_todos_los_periodos() -> pd.DataFrame:
    conexion = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM historico ORDER BY periodo", conexion)  # Carga toda la tabla a un DataFrame
    conexion.close()
    return df

# -------------------------------------------------------------------------
# Función alias (por ahora) que llama a la misma que obtener_todos_los_periodos()
# -------------------------------------------------------------------------
def obtener_historico_completo() -> pd.DataFrame:
    # Función alias que llama a obtener_todos_los_periodos().
    return obtener_todos_los_periodos()

def get_periodo_mas_reciente() -> Optional[str]:
    # Devuelve el periodo más reciente registrado en la base de datos, o None si no hay registros.
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT MAX(periodo) FROM historico")
    resultado = cursor.fetchone()
    conexion.close()
    if resultado and resultado[0]:
        return resultado[0]
    return None
