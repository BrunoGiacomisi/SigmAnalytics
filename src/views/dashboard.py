import customtkinter as ctk  # Librería para una interfaz gráfica moderna basada en tkinter
from tkinter import filedialog, messagebox  # Utilidades para abrir archivos y mostrar mensajes emergentes
from src import main  # Se importa el módulo principal que procesa el archivo
from src.views.viajes_viewer import abrir_viajes_viewer
from src.models import db as db_model
from typing import Optional
from src.config import (
    RUTA_GRAFICO_PROMEDIOS, TITULO_BOXPLOT, TITULO_BARRAS, TITULO_PROMEDIOS,
    MENSAJE_ARCHIVO_INVALIDO, MENSAJE_PROCESAMIENTO_EXITOSO, MENSAJE_PROCESAMIENTO_ERROR,
    MENSAJE_ARCHIVO_VALIDO, MENSAJE_ARCHIVO_INVALIDO_ICONO, MENSAJE_ERROR_LECTURA,
    COLOR_EXITO, COLOR_ERROR, COLOR_TITULO, TAMANO_IMAGEN, TAMANO_POPUP, TAMANO_POPUP_IMG,
    LOGO_PATH, LOGO_SIZE, show_data_directory_info
)
from src.representados import CODIGOS_REPRESENTADOS 
from src.models.config_manager import config_manager
from src.models.theme_manager import theme_manager
from PIL import Image, ImageTk  # Para trabajar con imágenes en tkinter
import os
import pandas as pd
import sys
import threading
from src.controllers.dashboard_controller import (
    select_manifest_file,
    validate_and_load_manifest,
    process_manifest,
    compute_period,
)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Función principal que crea y lanza la interfaz gráfica
def crear_dashboard():
    # Cargar configuración guardada
    saved_theme = config_manager.get_theme()
    saved_window_size = config_manager.get_window_size()
    saved_position = config_manager.get_window_position()
    
    # Aplicar tema inicial
    theme_manager.apply_theme(saved_theme)
    
    ctk.set_appearance_mode("light" if saved_theme == "light" else "dark")
    ctk.set_default_color_theme("blue")  # Tema azul por defecto

    ventana = ctk.CTk()  # Se instancia la ventana principal
    ventana.title("SigmAnalytics")  # Título de la ventana
    # Inicializar base de datos (crear tabla si no existe)
    try:
        db_model.crear_tabla_si_no_existe()
    except Exception as e:
        print(f"Error inicializando base de datos: {e}")
    
    # Aplicar tamaño y posición guardados
    ventana.geometry(saved_window_size)
    if saved_position and saved_position.get('x') is not None:
        ventana.geometry(f"{saved_window_size}+{saved_position['x']}+{saved_position['y']}")
    
    ventana.minsize(800, 600)         # Tamaño mínimo para evitar que se rompa el layout

    # Configura la ventana para que los frames se expandan
    ventana.grid_rowconfigure(0, weight=0)  # Frame superior (título, botón, stats)
    ventana.grid_rowconfigure(1, weight=1)  # Frame de gráficos ocupa el espacio extra
    ventana.grid_columnconfigure(0, weight=1)

    # Diccionario para almacenar widgets que necesitan actualización de tema
    theme_widgets = {}

    # --- Funciones auxiliares para separar responsabilidades ---
    
    def cargar_logo_empresa(master_frame) -> ctk.CTkLabel:
        # Carga y muestra el logo de la empresa. Retorna un placeholder si no se encuentra.
        try:
            # Usar directamente LOGO_PATH que ya tiene la ruta completa correcta
            print(f"Intentando cargar logo desde: {LOGO_PATH}")
            if os.path.exists(LOGO_PATH):
                print(f"Logo encontrado, cargando...")
                logo_img = Image.open(LOGO_PATH)
                logo_img.thumbnail(LOGO_SIZE)
                logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = ctk.CTkLabel(master=master_frame, image=logo_photo, text="")
                logo_label.image = logo_photo  # Mantener referencia
                print(f"Logo cargado exitosamente")
                return logo_label
            else:
                # Logo no encontrado, mostrar placeholder más grande
                print(f"Logo no encontrado en: {LOGO_PATH}")
                return ctk.CTkLabel(master=master_frame, text="🏢", font=("Segoe UI", 60), text_color="#002B45")
        except Exception as e:
            # Error al cargar logo, mostrar placeholder más grande
            print(f"Error al cargar logo: {e}")
            return ctk.CTkLabel(master=master_frame, text="🏢", font=("Segoe UI", 60), text_color="#002B45")

    def cambiar_tema():
        # Función para cambiar entre tema claro y oscuro.
        nuevo_tema = theme_manager.toggle_theme(theme_widgets)
        # Actualizar texto del botón
        boton_tema.configure(text=f"🌙 Modo {theme_manager.get_theme_name()}")

    def mostrar_info_datos():
        # Muestra información sobre dónde se guardan los datos.
        info = show_data_directory_info()
        
        # Crear ventana de información
        info_window = ctk.CTkToplevel(ventana)
        info_window.title("📁 Ubicación de Datos - SigmAnalytics")
        info_window.geometry("600x400")
        info_window.resizable(False, False)
        
        # Centrar la ventana
        info_window.transient(ventana)
        info_window.grab_set()
        
        # Frame principal
        frame_info = ctk.CTkFrame(info_window, corner_radius=15)
        frame_info.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        titulo = ctk.CTkLabel(
            frame_info, 
            text="📁 Ubicación de Datos", 
            font=("Segoe UI", 20, "bold"),
            text_color=theme_manager.get_current_theme_colors()['accent_color']
        )
        titulo.pack(pady=(20, 10))
        
        # Información
        info_text = ctk.CTkTextbox(
            frame_info,
            width=550,
            height=250,
            font=("Segoe UI", 12),
            wrap="word"
        )
        info_text.pack(pady=10, padx=20)
        info_text.insert("1.0", info)
        info_text.configure(state="disabled")
        
        # Botón cerrar
        boton_cerrar = ctk.CTkButton(
            frame_info,
            text="✅ Entendido",
            command=info_window.destroy,
            fg_color=theme_manager.get_current_theme_colors()['accent_color'],
            hover_color=theme_manager.get_current_theme_colors()['hover_color']
        )
        boton_cerrar.pack(pady=20)

    def guardar_configuracion_ventana():
        # Guarda la configuración de la ventana cuando se cierra.
        try:
            # Obtener tamaño y posición actual
            width = ventana.winfo_width()
            height = ventana.winfo_height()
            x = ventana.winfo_x()
            y = ventana.winfo_y()
            
            # Guardar configuración
            config_manager.update_window_size(width, height)
            config_manager.update_window_position(x, y)
        except Exception as e:
            print(f"Error al guardar configuración de ventana: {e}")

    # Configurar evento de cierre de ventana
    ventana.protocol("WM_DELETE_WINDOW", lambda: [guardar_configuracion_ventana(), ventana.destroy()])

    # ───────────────────────── Frame superior (título + botón + resultados)
    frame_principal = ctk.CTkFrame(master=ventana, corner_radius=20, fg_color="#dedbd7")
    frame_principal.grid(row=0, column=0, sticky="ew", padx=30, pady=20)
    theme_widgets['frame_principal'] = frame_principal

    # Frame para el header (logo + título + botones)
    header_frame = ctk.CTkFrame(master=frame_principal, fg_color="transparent")
    header_frame.pack(pady=(10, 15), fill="x", padx=20)
    
    # Logo de la empresa
    logo_label = cargar_logo_empresa(header_frame)
    logo_label.pack(side="left", padx=(0, 15))

    # Título simplificado (sin el nombre de la empresa)
    titulo = ctk.CTkLabel(master=header_frame,
                          text="SigmAnalytics",
                          font=("Segoe UI", 22, "bold"),
                          text_color="#002B45")
    titulo.pack(side="left", pady=10)
    theme_widgets['titulo'] = titulo

    # Frame para botones (a la derecha)
    botones_frame = ctk.CTkFrame(master=header_frame, fg_color="transparent")
    botones_frame.pack(side="right", padx=(0, 10))
    
    # Botón de información de datos
    boton_info_datos = ctk.CTkButton(
        master=botones_frame,
        text="📁 Datos",
        command=mostrar_info_datos,
        width=80,
        height=32,
        font=("Segoe UI", 11),
        fg_color=theme_manager.get_current_theme_colors()['accent_color'],
        hover_color=theme_manager.get_current_theme_colors()['hover_color']
    )
    boton_info_datos.pack(side="left", padx=(0, 10))
    theme_widgets['boton_info_datos'] = boton_info_datos
    
    # Botón para cambiar tema
    boton_tema = ctk.CTkButton(
        master=botones_frame,
        text=f"🌙 Modo {theme_manager.get_theme_name()}",
        command=cambiar_tema,
        width=120,
        height=32,
        font=("Segoe UI", 11),
        fg_color=theme_manager.get_current_theme_colors()['accent_color'],
        hover_color=theme_manager.get_current_theme_colors()['hover_color']
    )
    boton_tema.pack(side="left")
    theme_widgets['boton_tema'] = boton_tema

    # Variable para mostrar el nombre del archivo seleccionado
    archivo_seleccionado = ctk.StringVar(value="Ningún archivo seleccionado")
    label_archivo = ctk.CTkLabel(master=frame_principal, textvariable=archivo_seleccionado, font=("Segoe UI", 11), text_color="#607d8b")
    label_archivo.pack(pady=(0, 10), anchor="w", padx=10)
    theme_widgets['label_archivo'] = label_archivo

    # Variable para feedback visual de validación
    feedback_icon = ctk.StringVar(value="")
    label_feedback = ctk.CTkLabel(master=frame_principal, textvariable=feedback_icon, font=("Segoe UI", 18), text_color="#43a047")
    label_feedback.pack(pady=(0, 5), anchor="w", padx=10)
    theme_widgets['label_feedback'] = label_feedback

    # Indicador de carga (spinner)
    spinner = ctk.CTkLabel(master=frame_principal, text="", font=("Segoe UI", 18), text_color="#007399")
    spinner.pack(pady=(0, 5), anchor="w", padx=10)
    theme_widgets['spinner'] = spinner

    # Estado del último archivo cargado para abrir el visualizador
    df_cargado: Optional[pd.DataFrame] = None
    periodo_cargado: Optional[str] = None

    # Panel de resumen de estadísticas como tarjeta visual
    stats_card = ctk.CTkFrame(master=frame_principal, corner_radius=15, fg_color="#f8fafc", border_width=2, border_color="#b0bec5")
    stats_card.pack(pady=(0, 15), padx=20, fill="x")
    theme_widgets['stats_card'] = stats_card

    # Cuadrícula para las estadísticas
    grid_stats = ctk.CTkFrame(master=stats_card, fg_color="transparent")
    grid_stats.pack(padx=10, pady=10, fill="x")

    # Título
    label_titulo_stats = ctk.CTkLabel(master=grid_stats, text="📊 Estadísticas del mes:", font=("Segoe UI", 14, "bold"), text_color="#222831")
    label_titulo_stats.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
    theme_widgets['label_titulo_stats'] = label_titulo_stats
    # Línea divisoria
    ctk.CTkLabel(master=grid_stats, text="", height=1, fg_color="#888", width=400).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))

    # Variables para los valores
    valor_representados = ctk.StringVar(value="")
    valor_otros = ctk.StringVar(value="")
    valor_participacion = ctk.StringVar(value="")
    valor_viajes = ctk.StringVar(value="")

    # Fila: Representados
    label_rep = ctk.CTkLabel(master=grid_stats, text="■ Representados:", font=("Segoe UI", 12, "bold"), text_color="#222831")
    label_rep.grid(row=2, column=0, sticky="w")
    theme_widgets['label_rep'] = label_rep
    valor_rep = ctk.CTkLabel(master=grid_stats, textvariable=valor_representados, font=("Segoe UI", 12), text_color="#222831")
    valor_rep.grid(row=2, column=1, sticky="w")
    theme_widgets['valor_rep'] = valor_rep
    
    # Fila: Otros
    label_otros = ctk.CTkLabel(master=grid_stats, text="■ Otros:", font=("Segoe UI", 12, "bold"), text_color="#222831")
    label_otros.grid(row=3, column=0, sticky="w")
    theme_widgets['label_otros'] = label_otros
    valor_otros_label = ctk.CTkLabel(master=grid_stats, textvariable=valor_otros, font=("Segoe UI", 12), text_color="#222831")
    valor_otros_label.grid(row=3, column=1, sticky="w")
    theme_widgets['valor_otros_label'] = valor_otros_label
    
    # Fila: Participación
    label_participacion = ctk.CTkLabel(master=grid_stats, text="● Participación:", font=("Segoe UI", 12, "bold"), text_color="#222831")
    label_participacion.grid(row=4, column=0, sticky="w")
    theme_widgets['label_participacion'] = label_participacion
    valor_participacion_label = ctk.CTkLabel(master=grid_stats, textvariable=valor_participacion, font=("Segoe UI", 12), text_color="#222831")
    valor_participacion_label.grid(row=4, column=1, sticky="w")
    theme_widgets['valor_participacion_label'] = valor_participacion_label
    
    # Fila: Viajes
    label_viajes = ctk.CTkLabel(master=grid_stats, text="🚚 Viajes de representados:", font=("Segoe UI", 12, "bold"), text_color="#222831")
    label_viajes.grid(row=5, column=0, sticky="w")
    theme_widgets['label_viajes'] = label_viajes
    valor_viajes_label = ctk.CTkLabel(master=grid_stats, textvariable=valor_viajes, font=("Segoe UI", 12), text_color="#222831")
    valor_viajes_label.grid(row=5, column=1, sticky="w")
    theme_widgets['valor_viajes_label'] = valor_viajes_label

    # Mensaje de histórico actualizado
    label_historial = ctk.CTkLabel(master=frame_principal, text="", font=("Segoe UI", 11), text_color="#607d8b")
    label_historial.pack(pady=(0, 10), anchor="w", padx=10)
    theme_widgets['label_historial'] = label_historial

    def validar_y_cargar_archivo(ruta_archivo: str) -> pd.DataFrame:
        # Centraliza validación usando el controller
        try:
            return validate_and_load_manifest(ruta_archivo)
        except ValueError:
            raise ValueError(MENSAJE_ARCHIVO_INVALIDO)

    def actualizar_panel_resultados(
        mediana_rep: float,
        mediana_otros: float,
        promedio_rep: float,
        promedio_otros: float,
        participacion: float,
        viajes_representados: int,
        actualizado: bool
    ) -> None:
        valor_representados.set(f"{mediana_rep:.2f} (mediana) | {promedio_rep:.2f} (promedio)")
        valor_otros.set(f"{mediana_otros:.2f} (mediana) | {promedio_otros:.2f} (promedio)")
        valor_participacion.set(f"{participacion:.2f}%")
        valor_viajes.set(f"{viajes_representados}")
        label_historial.configure(text="✓ Histórico actualizado." if actualizado else "ℹ Ya existía un registro para ese período.")

    # Muestra una imagen desde una ruta en el label correspondiente
    def mostrar_imagen(ruta: str, etiqueta: ctk.CTkLabel) -> None:
        if os.path.exists(ruta):
            img = Image.open(ruta)
            img.thumbnail(TAMANO_IMAGEN)
            imagen_tk = ImageTk.PhotoImage(img)
            etiqueta.configure(image=imagen_tk)
            etiqueta.image = imagen_tk  # Guarda la referencia para que no se borre
        else:
            etiqueta.configure(image="", text="Gráfico no disponible")

    # Función para mostrar imagen ampliada en popup
    def mostrar_imagen_ampliada(ruta: str) -> None:
        if os.path.exists(ruta):
            ventana_popup = ctk.CTkToplevel(ventana)
            ventana_popup.title("Vista ampliada")
            ventana_popup.geometry(f"{TAMANO_POPUP[0]}x{TAMANO_POPUP[1]}")
            ventana_popup.transient(ventana)
            ventana_popup.attributes('-topmost', True)
            ventana_popup.lift()
            ventana_popup.focus_force()
            img = Image.open(ruta)
            img.thumbnail(TAMANO_POPUP_IMG)
            imagen_tk = ImageTk.PhotoImage(img)
            etiqueta_img = ctk.CTkLabel(master=ventana_popup, image=imagen_tk, text="")
            etiqueta_img.image = imagen_tk
            etiqueta_img.pack(padx=10, pady=10)
            ventana_popup.after(500, lambda: ventana_popup.attributes('-topmost', False))
        else:
            messagebox.showerror("Error", "No se encontró la imagen para ampliar.")

    # Función que se ejecuta cuando el usuario presiona el botón
    def ejecutar_procesamiento() -> None:
        try:
            boton.configure(state='disabled')
            spinner.configure(text="⏳ Procesando...")
            ruta_archivo = select_manifest_file()
            if not ruta_archivo:
                feedback_icon.set("")
                spinner.configure(text="")
                boton.configure(state='normal')
                return
            archivo_seleccionado.set(f"Archivo: {os.path.basename(ruta_archivo)}")

            def run_proceso():
                try:
                    # 1) Validación y carga para feedback temprano
                    try:
                        df_local = validar_y_cargar_archivo(ruta_archivo)
                    except Exception:
                        def on_invalid():
                            feedback_icon.set(MENSAJE_ARCHIVO_INVALIDO_ICONO)
                            label_feedback.configure(text_color=COLOR_ERROR)
                            spinner.configure(text="")
                            boton.configure(state='normal')
                            messagebox.showerror("Error al procesar", MENSAJE_ARCHIVO_INVALIDO)
                        ventana.after(0, on_invalid)
                        return

                    # 2) Procesamiento pesado
                    resultado = process_manifest(ruta_archivo, CODIGOS_REPRESENTADOS, df=df_local)
                    mediana_rep, mediana_otros, promedio_rep, promedio_otros, participacion, actualizado, viajes_representados, ruta_boxplot_periodo, ruta_barplot_periodo, es_preview = resultado

                    # 3) Calcular periodo para el viewer
                    periodo_local = compute_period(df_local, "Fecha ingreso")

                    def on_success():
                        nonlocal df_cargado, periodo_cargado
                        df_cargado = df_local
                        periodo_cargado = periodo_local
                        feedback_icon.set(MENSAJE_PROCESAMIENTO_EXITOSO if not es_preview else "ℹ Solo vista previa: el periodo es igual o anterior al último registrado. No se guardó en la base de datos ni en la carpeta de gráficos.")
                        label_feedback.configure(text_color=(COLOR_EXITO if not es_preview else "#e67e22"))
                        actualizar_panel_resultados(mediana_rep, mediana_otros, promedio_rep, promedio_otros, participacion, viajes_representados, actualizado)
                        mostrar_imagen(ruta_boxplot_periodo, etiqueta_imagen_boxplot)
                        mostrar_imagen(ruta_barplot_periodo, etiqueta_imagen_barras)
                        mostrar_imagen(RUTA_GRAFICO_PROMEDIOS, etiqueta_imagen_promedios)
                        set_rutas_graficos_periodo(ruta_boxplot_periodo, ruta_barplot_periodo)
                        spinner.configure(text="")
                        boton.configure(state='normal')
                        if df_cargado is not None and periodo_cargado:
                            boton_viajes.configure(state='normal')
                    ventana.after(0, on_success)

                except Exception as e:
                    def on_error():
                        feedback_icon.set(MENSAJE_PROCESAMIENTO_ERROR)
                        label_feedback.configure(text_color=COLOR_ERROR)
                        spinner.configure(text="")
                        boton.configure(state='normal')
                        messagebox.showerror("Error al procesar", str(e))
                    ventana.after(0, on_error)

            threading.Thread(target=run_proceso, daemon=True).start()

        except Exception as e:
            spinner.configure(text="")
            boton.configure(state='normal')
            messagebox.showerror("Error inesperado", str(e))

    # Botón para ejecutar el procesamiento del archivo (debe ir después de definir ejecutar_procesamiento)
    boton = ctk.CTkButton(master=frame_principal,
                          text="Seleccionar archivo y procesar manifiesto",
                          command=ejecutar_procesamiento,  # Acción al hacer click
                          fg_color="#00587A",
                          hover_color="#007399",
                          font=("Segoe UI", 13, "bold"))
    boton.pack(pady=5)
    theme_widgets['boton'] = boton

    # Botón para abrir el visualizador de viajes por representado
    def abrir_visualizador() -> None:
        if df_cargado is None or not periodo_cargado:
            messagebox.showinfo("Información", "Primero cargá y procesá un manifiesto válido para poder visualizar.")
            return
        try:
            abrir_viajes_viewer(ventana, df_cargado, CODIGOS_REPRESENTADOS, periodo_cargado)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    boton_viajes = ctk.CTkButton(
        master=frame_principal,
        text="Viajes por Representado",
        command=abrir_visualizador,
        fg_color="#4a9eff",
        hover_color="#66b3ff",
        font=("Segoe UI", 12, "bold"),
        state='disabled'
    )
    boton_viajes.pack(pady=(0, 10))
    theme_widgets['boton_viajes'] = boton_viajes

    # ───────────────────────── Frame inferior (donde van las imágenes de los gráficos)
    # Frame contenedor para centrar el área de gráficos
    frame_graficos_outer = ctk.CTkFrame(master=ventana, fg_color="#f4f4f4")
    frame_graficos_outer.grid(row=1, column=0, sticky="nsew")
    frame_graficos_outer.grid_columnconfigure(0, weight=1)
    theme_widgets['frame_graficos_outer'] = frame_graficos_outer

    # Frame de gráficos con ancho máximo
    frame_graficos = ctk.CTkFrame(master=frame_graficos_outer, corner_radius=20, fg_color="#f4f4f4", width=900)
    frame_graficos.grid(row=0, column=0, pady=10)
    frame_graficos.grid_columnconfigure((0, 1, 2), weight=1)
    frame_graficos.grid_rowconfigure((0, 1, 2), weight=1)
    theme_widgets['frame_graficos'] = frame_graficos

    # Etiquetas para mostrar los gráficos cargados
    etiqueta_titulo_boxplot = ctk.CTkLabel(master=frame_graficos, text=TITULO_BOXPLOT, font=("Segoe UI", 13, "bold"), text_color=theme_manager.get_current_theme_colors()['title_color'])
    etiqueta_titulo_boxplot.grid(row=0, column=0, padx=10, pady=(0,5), sticky="nsew")
    theme_widgets['etiqueta_titulo_boxplot'] = etiqueta_titulo_boxplot
    etiqueta_imagen_boxplot = ctk.CTkLabel(master=frame_graficos, text="")
    etiqueta_imagen_boxplot.grid(row=1, column=0, padx=10, sticky="nsew")

    etiqueta_titulo_barras = ctk.CTkLabel(master=frame_graficos, text=TITULO_BARRAS, font=("Segoe UI", 13, "bold"), text_color=theme_manager.get_current_theme_colors()['title_color'])
    etiqueta_titulo_barras.grid(row=0, column=1, padx=10, pady=(0,5), sticky="nsew")
    theme_widgets['etiqueta_titulo_barras'] = etiqueta_titulo_barras
    etiqueta_imagen_barras = ctk.CTkLabel(master=frame_graficos, text="")
    etiqueta_imagen_barras.grid(row=1, column=1, padx=10, sticky="nsew")

    etiqueta_titulo_promedios = ctk.CTkLabel(master=frame_graficos, text=TITULO_PROMEDIOS, font=("Segoe UI", 13, "bold"), text_color=theme_manager.get_current_theme_colors()['title_color'])
    etiqueta_titulo_promedios.grid(row=0, column=2, padx=10, pady=(0,5), sticky="nsew")
    theme_widgets['etiqueta_titulo_promedios'] = etiqueta_titulo_promedios
    etiqueta_imagen_promedios = ctk.CTkLabel(master=frame_graficos, text="")
    etiqueta_imagen_promedios.grid(row=1, column=2, padx=10, sticky="nsew")

    # Referencias a las imágenes para evitar que el recolector de basura las elimine
    referencia_imagen_boxplot = None
    referencia_imagen_barras = None
    referencia_imagen_promedios = None

    # Variables para rutas de los gráficos del periodo actual
    ruta_boxplot_actual = None
    ruta_barplot_actual = None

    def set_rutas_graficos_periodo(ruta_boxplot, ruta_barplot):
        nonlocal ruta_boxplot_actual, ruta_barplot_actual
        ruta_boxplot_actual = ruta_boxplot
        ruta_barplot_actual = ruta_barplot

    # Botones para ampliar gráficos (comandos usan las rutas actuales)
    boton_ampliar_boxplot = ctk.CTkButton(master=frame_graficos, text="Ampliar", width=80, command=lambda: mostrar_imagen_ampliada(ruta_boxplot_actual))
    boton_ampliar_boxplot.grid(row=2, column=0, pady=(5, 10), sticky="n")
    theme_widgets['boton_ampliar_boxplot'] = boton_ampliar_boxplot
    
    boton_ampliar_barras = ctk.CTkButton(master=frame_graficos, text="Ampliar", width=80, command=lambda: mostrar_imagen_ampliada(ruta_barplot_actual))
    boton_ampliar_barras.grid(row=2, column=1, pady=(5, 10), sticky="n")
    theme_widgets['boton_ampliar_barras'] = boton_ampliar_barras
    
    boton_ampliar_promedios = ctk.CTkButton(master=frame_graficos, text="Ampliar", width=80, command=lambda: mostrar_imagen_ampliada(RUTA_GRAFICO_PROMEDIOS))
    boton_ampliar_promedios.grid(row=2, column=2, pady=(5, 10), sticky="n")
    theme_widgets['boton_ampliar_promedios'] = boton_ampliar_promedios

    # Eliminar binds de click en las imágenes

    # Aplicar tema inicial a todos los widgets
    theme_widgets['ventana'] = ventana
    theme_manager.update_widget_colors(theme_widgets)

    ventana.mainloop()  # Lanza la ventana

# Si este archivo se ejecuta directamente, se lanza la interfaz
if __name__ == "__main__":
    crear_dashboard()

