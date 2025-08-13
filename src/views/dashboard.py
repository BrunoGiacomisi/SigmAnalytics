import customtkinter as ctk  # Librería para una interfaz gráfica moderna basada en tkinter
from tkinter import messagebox  # Utilidades para mostrar mensajes emergentes
from src.views.viajes_viewer import abrir_viajes_viewer
from src.models import db as db_model
from typing import Optional
from src.config import (
    RUTA_GRAFICO_PROMEDIOS, LOGO_PATH, LOGO_SIZE, TAMANO_IMAGEN, TAMANO_POPUP, TAMANO_POPUP_IMG, show_data_directory_info,
    TITULO_BOXPLOT, TITULO_BARRAS, TITULO_PROMEDIOS
)
from src.constants import (
    Messages, Colors, UI
)
from src.representados import CODIGOS_REPRESENTADOS 
from src.models.config_manager import config_manager
from src.models.design_manager import design_manager
from src.models.design_system import (
    get_spacing, get_font_tuple, get_dimension,
    BUTTON_PRIMARY, BUTTON_SECONDARY
)
from PIL import Image, ImageTk  # Para trabajar con imágenes en tkinter
import os
import pandas as pd
import threading
from src.services import FileService

# Función principal que crea y lanza la interfaz gráfica
def crear_dashboard():
    # Cargar configuración guardada
    saved_window_size = config_manager.get_window_size()
    saved_position = config_manager.get_window_position()
    
    # El design_manager ya configura modo oscuro automáticamente
    
    ctk.set_appearance_mode("dark")
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
    
    ventana.minsize(*UI.MIN_WINDOW_SIZE)  # Usar constante

    # Configurar la ventana para la nueva estructura
    ventana.grid_rowconfigure(1, weight=1)  # Solo el contenido principal se expande
    ventana.grid_columnconfigure(0, weight=1)

    # Diccionario para almacenar widgets que necesitan actualización de tema
    # Diccionario de widgets simplificado (modo oscuro fijo)
    theme_widgets = {}

    # Obtener colores del sistema de diseño (siempre modo oscuro)
    colors = design_manager.get_colors()

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

    # Función cambiar_tema eliminada - modo oscuro fijo

    def aplicar_diseno_widgets():
        # Aplicar diseño estándar a los widgets principales
        
        # Header
        design_manager.apply_widget_design(header_frame, "header_frame")
        design_manager.apply_widget_design(main_container, "main_container")
        
        # Botones
        design_manager.apply_widget_design(boton, "button_primary")
        design_manager.apply_widget_design(boton_info_datos, "button_secondary")
        design_manager.apply_widget_design(boton_viajes, "button_secondary")
        
        # Labels y títulos
        design_manager.apply_widget_design(titulo, "title")
        design_manager.apply_widget_design(kpi_section_title, "title")
        design_manager.apply_widget_design(charts_section_title, "title")
        
        # KPIs y charts
        if 'kpi_cards' in theme_widgets:
            for card in theme_widgets['kpi_cards']:
                card.configure(
                    fg_color=colors["card_background"],
                    border_color=colors["border"]
                )
        
        if 'chart_cards' in theme_widgets:
            for card in theme_widgets['chart_cards']:
                card.configure(
                    fg_color=colors["card_background"],
                    border_color=colors["border"]
                )

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
            text_color=colors['accent']
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
            fg_color=colors['accent'],
            hover_color=colors['accent_hover']
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

    # ═══════════════════════════════════════════════════════════════════════════════
    # BARRA SUPERIOR FIJA
    # ═══════════════════════════════════════════════════════════════════════════════
    
    header_frame = ctk.CTkFrame(
        master=ventana, 
        height=get_dimension("header_height"),
        corner_radius=0,
        fg_color=colors["card_background"],
        border_width=1,
        border_color=colors["border"]
    )
    header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
    header_frame.grid_propagate(False)  # Mantener altura fija
    theme_widgets['header_frame'] = header_frame

    # Contenedor interno para centrar contenido del header
    header_content = ctk.CTkFrame(master=header_frame, fg_color="transparent")
    header_content.pack(fill="both", expand=True, padx=get_spacing("lg"), pady=get_spacing("sm"))
    
    # Logo y título (lado izquierdo)
    left_section = ctk.CTkFrame(master=header_content, fg_color="transparent")
    left_section.pack(side="left", fill="y")
    
    # Logo de la empresa
    logo_label = cargar_logo_empresa(left_section)
    logo_label.pack(side="left", padx=(0, get_spacing("md")))

    # Título de la aplicación
    titulo = ctk.CTkLabel(
        master=left_section,
        text="SigmAnalytics",
        font=get_font_tuple("title", "bold"),
        text_color=colors["text_primary"]
    )
    titulo.pack(side="left", pady=0)
    theme_widgets['titulo'] = titulo

    # Sección central - Botón principal
    center_section = ctk.CTkFrame(master=header_content, fg_color="transparent")
    center_section.pack(side="left", fill="both", expand=True, padx=get_spacing("xl"))
    
    # El botón principal se agregará después de definir ejecutar_procesamiento()
    # Por ahora creamos un placeholder
    boton_principal_placeholder = None
    
    # Sección derecha - Botones secundarios
    right_section = ctk.CTkFrame(master=header_content, fg_color="transparent")
    right_section.pack(side="right", fill="y")
    
    # Botón de información de datos (secundario)
    boton_info_datos = ctk.CTkButton(
        master=right_section,
        text="📁 Datos",
        command=mostrar_info_datos,
        width=get_dimension("button_min_width"),
        **BUTTON_SECONDARY,
        fg_color=colors["secondary"],
        hover_color=colors["secondary_hover"],
        text_color=colors["text_on_primary"]
    )
    boton_info_datos.pack(side="left", padx=(0, get_spacing("sm")))
    theme_widgets['boton_info_datos'] = boton_info_datos

    # ═══════════════════════════════════════════════════════════════════════════════
    # CONTENIDO PRINCIPAL SCROLLABLE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Contenedor principal con ancho máximo centrado
    main_container = ctk.CTkScrollableFrame(
        master=ventana, 
        fg_color=colors["background"],
        corner_radius=0
    )
    main_container.grid(row=1, column=0, sticky="nsew")
    theme_widgets['main_container'] = main_container

    # Frame contenedor con ancho máximo
    content_wrapper = ctk.CTkFrame(master=main_container, fg_color="transparent")
    content_wrapper.pack(fill="x", pady=get_spacing("lg"))
    
    # Frame de contenido con ancho máximo centrado
    content_frame = ctk.CTkFrame(
        master=content_wrapper, 
        fg_color="transparent",
        width=get_dimension("container_max_width")
    )
    content_frame.pack(anchor="center", padx=get_spacing("lg"))

    # ═══════════════════════════════════════════════════════════════════════════════
    # VARIABLES DE ESTADO Y FEEDBACK
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Variables para mostrar estado del archivo y feedback
    archivo_seleccionado = ctk.StringVar(value="")
    feedback_icon = ctk.StringVar(value="")
    
    # Estado del último archivo cargado para abrir el visualizador
    df_cargado: Optional[pd.DataFrame] = None
    periodo_cargado: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════════════════════
    # SECCIÓN DE FEEDBACK Y STATUS (EN EL HEADER)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Status del archivo en el centro del header (debajo del botón principal)
    status_frame = ctk.CTkFrame(master=center_section, fg_color="transparent")
    status_frame.pack(side="bottom", fill="x", pady=(get_spacing("xs"), 0))
    
    # Label para archivo seleccionado
    label_archivo = ctk.CTkLabel(
        master=status_frame, 
        textvariable=archivo_seleccionado, 
        font=get_font_tuple("sm"),
        text_color=colors["text_secondary"]
    )
    label_archivo.pack()
    theme_widgets['label_archivo'] = label_archivo

    # Label para feedback
    label_feedback = ctk.CTkLabel(
        master=status_frame, 
        textvariable=feedback_icon, 
        font=get_font_tuple("sm"),
        text_color=colors["success"]
    )
    label_feedback.pack()
    theme_widgets['label_feedback'] = label_feedback

    # Indicador de carga (spinner)
    spinner = ctk.CTkLabel(
        master=status_frame, 
        text="", 
        font=get_font_tuple("sm"),
        text_color=colors["info"]
    )
    spinner.pack()
    theme_widgets['spinner'] = spinner

    # ═══════════════════════════════════════════════════════════════════════════════
    # SECCIÓN DE KPIs (ESTADÍSTICAS DEL MES)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Título de la sección
    kpi_section_title = ctk.CTkLabel(
        master=content_frame,
        text="📊 Estadísticas del mes",
        font=get_font_tuple("xl", "bold"),
        text_color=colors["text_primary"],
        anchor="w"
    )
    kpi_section_title.pack(fill="x", pady=(0, get_spacing("md")))
    theme_widgets['kpi_section_title'] = kpi_section_title

    # Contenedor de KPIs en 2 columnas
    kpi_container = ctk.CTkFrame(master=content_frame, fg_color="transparent")
    kpi_container.pack(fill="x", pady=(0, get_spacing("xl")))
    kpi_container.grid_columnconfigure((0, 1), weight=1)

    # Variables para los valores
    valor_representados = ctk.StringVar(value="")
    valor_otros = ctk.StringVar(value="")
    valor_participacion = ctk.StringVar(value="")
    valor_viajes = ctk.StringVar(value="")

    # Función para crear tarjeta KPI
    def crear_kpi_card(parent, title: str, value_var: ctk.StringVar, row: int, col: int):
        card = ctk.CTkFrame(
            master=parent,
            corner_radius=get_dimension("border_radius_lg"),
            fg_color=colors["card_background"],
            border_width=1,
            border_color=colors["border"]
        )
        card.grid(row=row, column=col, sticky="ew", padx=get_spacing("sm"), pady=get_spacing("sm"))
        
        # Título de la métrica
        title_label = ctk.CTkLabel(
            master=card,
            text=title,
            font=get_font_tuple("sm", "bold"),
            text_color=colors["text_secondary"],
            anchor="w"
        )
        title_label.pack(fill="x", padx=get_spacing("md"), pady=(get_spacing("md"), get_spacing("xs")))
        
        # Valor de la métrica
        value_label = ctk.CTkLabel(
            master=card,
            textvariable=value_var,
            font=get_font_tuple("lg", "bold"),
            text_color=colors["text_primary"],
            anchor="w"
        )
        value_label.pack(fill="x", padx=get_spacing("md"), pady=(0, get_spacing("md")))
        
        return card, title_label, value_label

    # Crear tarjetas KPI
    kpi_cards = {}
    
    # Fila 1
    card_rep, title_rep, valor_rep = crear_kpi_card(kpi_container, "💰 Representados", valor_representados, 0, 0)
    card_otros, title_otros, valor_otros_label = crear_kpi_card(kpi_container, "🏢 Otros", valor_otros, 0, 1)
    
    # Fila 2  
    card_part, title_part, valor_participacion_label = crear_kpi_card(kpi_container, "📈 Participación", valor_participacion, 1, 0)
    card_viajes, title_viajes, valor_viajes_label = crear_kpi_card(kpi_container, "🚚 Viajes", valor_viajes, 1, 1)

    # Guardar referencias para el tema
    theme_widgets.update({
        'kpi_cards': [card_rep, card_otros, card_part, card_viajes],
        'kpi_titles': [title_rep, title_otros, title_part, title_viajes],
        'kpi_values': [valor_rep, valor_otros_label, valor_participacion_label, valor_viajes_label]
    })

    # Mensaje de histórico (debajo de los KPIs)
    label_historial = ctk.CTkLabel(
        master=content_frame, 
        text="", 
        font=get_font_tuple("sm"),
        text_color=colors["text_secondary"],
        anchor="w"
    )
    label_historial.pack(fill="x", pady=(get_spacing("sm"), get_spacing("lg")))
    theme_widgets['label_historial'] = label_historial

    def validar_y_cargar_archivo(ruta_archivo: str) -> pd.DataFrame:
        # Usar FileService para validación
        try:
            file_service = FileService()
            return file_service.validate_and_load_manifest(ruta_archivo)
        except ValueError:
            raise ValueError(Messages.ARCHIVO_INVALIDO)

    def actualizar_panel_resultados(
        mediana_rep: float,
        mediana_otros: float,
        promedio_rep: float,
        promedio_otros: float,
        participacion: float,
        viajes_representados: int,
        actualizado: bool
    ) -> None:
        # Función helper para formatear números con separador de miles
        def format_number(num: float) -> str:
            if num == int(num):  # Si es entero, no mostrar decimales
                return f"{int(num):,}".replace(",", ".")
            else:  # Si tiene decimales, mostrar máximo 2
                return f"{num:.2f}".replace(".", ",").replace(",", ".", 1)
        
        # Formatear valores monetarios con separador de miles
        mediana_rep_fmt = format_number(mediana_rep)
        promedio_rep_fmt = format_number(promedio_rep)
        mediana_otros_fmt = format_number(mediana_otros)
        promedio_otros_fmt = format_number(promedio_otros)
        
        # Actualizar KPIs con formato mejorado
        valor_representados.set(f"{mediana_rep_fmt} (mediana) | {promedio_rep_fmt} (promedio)")
        valor_otros.set(f"{mediana_otros_fmt} (mediana) | {promedio_otros_fmt} (promedio)")
        valor_participacion.set(f"{participacion:.1f}%")  # Solo 1 decimal para porcentajes
        valor_viajes.set(f"{viajes_representados:,} viajes".replace(",", "."))  # Agregar "viajes" y separador
        
        # Mensaje de histórico más claro
        if actualizado:
            label_historial.configure(text="✅ Histórico actualizado correctamente")
        else:
            label_historial.configure(text="ℹ️ Período ya existente en el histórico")

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
            
            # Usar FileService
            file_service = FileService()
            ruta_archivo = file_service.select_manifest_file()
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
                            feedback_icon.set(Messages.ARCHIVO_INVALIDO_ICONO)
                            label_feedback.configure(text_color=Colors.ERROR)
                            spinner.configure(text="")
                            boton.configure(state='normal')
                            messagebox.showerror("Error al procesar", Messages.ARCHIVO_INVALIDO)
                        ventana.after(0, on_invalid)
                        return

                    # 2) Procesamiento pesado
                    resultado = file_service.process_manifest_file(ruta_archivo, CODIGOS_REPRESENTADOS, df=df_local)
                    mediana_rep, mediana_otros, promedio_rep, promedio_otros, participacion, actualizado, viajes_representados, ruta_boxplot_periodo, ruta_barplot_periodo, es_preview = resultado

                    # 3) Calcular periodo para el viewer
                    periodo_local = file_service.compute_period(df_local)

                    def on_success():
                        nonlocal df_cargado, periodo_cargado
                        df_cargado = df_local
                        periodo_cargado = periodo_local
                        feedback_icon.set(Messages.PROCESAMIENTO_EXITOSO if not es_preview else "ℹ Solo vista previa: el periodo es igual o anterior al último registrado. No se guardó en la base de datos ni en la carpeta de gráficos.")
                        label_feedback.configure(text_color=(Colors.SUCCESS if not es_preview else "#e67e22"))
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
                        feedback_icon.set(Messages.PROCESAMIENTO_ERROR)
                        label_feedback.configure(text_color=Colors.ERROR)
                        spinner.configure(text="")
                        boton.configure(state='normal')
                        messagebox.showerror("Error al procesar", str(e))
                    ventana.after(0, on_error)

            threading.Thread(target=run_proceso, daemon=True).start()

        except Exception as e:
            spinner.configure(text="")
            boton.configure(state='normal')
            messagebox.showerror("Error inesperado", str(e))

    # Agregar el botón principal al header ahora que ejecutar_procesamiento está definido
    boton = ctk.CTkButton(
        master=center_section,
        text="Seleccionar archivo y procesar manifiesto",
        command=ejecutar_procesamiento,
        **BUTTON_PRIMARY,
        fg_color=colors["primary"],
        hover_color=colors["primary_hover"],
        text_color=colors["text_on_primary"],
        width=320  # Ancho fijo para el botón principal
    )
    boton.pack(anchor="center", pady=get_spacing("sm"))
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

    # Botón "Viajes por Representado" también en el header (lado derecho)
    boton_viajes = ctk.CTkButton(
        master=right_section,
        text="Viajes por Representado",
        command=abrir_visualizador,
        **BUTTON_SECONDARY,
        fg_color=colors["info"],
        hover_color=colors["primary_hover"],
        text_color=colors["text_on_primary"],
        state='disabled',
        width=160
    )
    boton_viajes.pack(side="left", padx=(get_spacing("sm"), 0))
    theme_widgets['boton_viajes'] = boton_viajes

    # ═══════════════════════════════════════════════════════════════════════════════
    # SECCIÓN DE GRÁFICOS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Título de la sección
    charts_section_title = ctk.CTkLabel(
        master=content_frame,
        text="📈 Análisis Gráfico",
        font=get_font_tuple("xl", "bold"),
        text_color=colors["text_primary"],
        anchor="w"
    )
    charts_section_title.pack(fill="x", pady=(0, get_spacing("md")))
    theme_widgets['charts_section_title'] = charts_section_title

    # Contenedor de gráficos en 3 columnas
    frame_graficos = ctk.CTkFrame(master=content_frame, fg_color="transparent")
    frame_graficos.pack(fill="x", pady=(0, get_spacing("xl")))
    frame_graficos.grid_columnconfigure((0, 1, 2), weight=1)
    theme_widgets['frame_graficos'] = frame_graficos

    # Función para crear tarjeta de gráfico uniforme
    def crear_chart_card(parent, title: str, col: int):
        # Tarjeta contenedora
        card = ctk.CTkFrame(
            master=parent,
            corner_radius=get_dimension("border_radius_lg"),
            fg_color=colors["card_background"],
            border_width=1,
            border_color=colors["border"],
            height=300  # Altura uniforme
        )
        card.grid(row=0, column=col, sticky="nsew", padx=get_spacing("sm"), pady=get_spacing("sm"))
        card.grid_propagate(False)  # Mantener altura fija
        
        # Header de la tarjeta
        header = ctk.CTkFrame(master=card, fg_color="transparent", height=40)
        header.pack(fill="x", padx=get_spacing("md"), pady=(get_spacing("md"), 0))
        header.pack_propagate(False)
        
        # Título del gráfico
        title_label = ctk.CTkLabel(
            master=header,
            text=title,
            font=get_font_tuple("md", "bold"),
            text_color=colors["text_primary"],
            anchor="w"
        )
        title_label.pack(side="left", fill="both", expand=True)
        
        # Botón "Ampliar" en la esquina superior derecha
        ampliar_btn = ctk.CTkButton(
            master=header,
            text="🔍 Ampliar",
            width=80,
            height=28,
            font=get_font_tuple("xs"),
            fg_color=colors["secondary"],
            hover_color=colors["secondary_hover"],
            text_color=colors["text_on_primary"]
        )
        ampliar_btn.pack(side="right")
        
        # Área del gráfico
        chart_area = ctk.CTkLabel(
            master=card,
            text="",
            fg_color="transparent"
        )
        chart_area.pack(fill="both", expand=True, padx=get_spacing("md"), pady=(get_spacing("sm"), get_spacing("md")))
        
        return card, title_label, ampliar_btn, chart_area

    # Crear tarjetas de gráficos
    card_boxplot, titulo_boxplot, btn_boxplot, etiqueta_imagen_boxplot = crear_chart_card(frame_graficos, TITULO_BOXPLOT, 0)
    card_barras, titulo_barras, btn_barras, etiqueta_imagen_barras = crear_chart_card(frame_graficos, TITULO_BARRAS, 1)
    card_promedios, titulo_promedios, btn_promedios, etiqueta_imagen_promedios = crear_chart_card(frame_graficos, TITULO_PROMEDIOS, 2)

    # Guardar referencias para el tema
    theme_widgets.update({
        'chart_cards': [card_boxplot, card_barras, card_promedios],
        'chart_titles': [titulo_boxplot, titulo_barras, titulo_promedios],
        'chart_buttons': [btn_boxplot, btn_barras, btn_promedios]
    })

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

    # Conectar los botones de ampliar con las funciones existentes
    btn_boxplot.configure(command=lambda: mostrar_imagen_ampliada(ruta_boxplot_actual))
    btn_barras.configure(command=lambda: mostrar_imagen_ampliada(ruta_barplot_actual))
    btn_promedios.configure(command=lambda: mostrar_imagen_ampliada(RUTA_GRAFICO_PROMEDIOS))

    # Eliminar binds de click en las imágenes

    # Aplicar tema inicial a todos los widgets
    # Aplicar estilos iniciales (modo oscuro fijo)
    theme_widgets['ventana'] = ventana

    ventana.mainloop()  # Lanza la ventana

# Si este archivo se ejecuta directamente, se lanza la interfaz
if __name__ == "__main__":
    crear_dashboard()

