import customtkinter as ctk
from typing import Dict, Any
from src.models.design_system import COLORS

class DesignManager:
    # Gestor del sistema de diseño de la aplicación.
    
    def __init__(self):
        # Configurar CustomTkinter en modo oscuro por defecto
        ctk.set_appearance_mode("dark")
    
    def get_colors(self) -> Dict[str, str]:
        # Obtiene los colores del sistema de diseño.
        return COLORS
    
    def apply_widget_design(self, widget, widget_type: str = "default"):
        # Aplica el diseño estándar a un widget según su tipo.
        colors = self.get_colors()
        
        try:
            if widget_type == "frame":
                widget.configure(
                    fg_color=colors["card_background"],
                    border_color=colors.get("border", colors["card_background"])
                )
            elif widget_type == "header_frame":
                widget.configure(
                    fg_color=colors["card_background"],
                    border_color=colors["border"]
                )
            elif widget_type == "main_container":
                widget.configure(fg_color=colors["background"])
            elif widget_type == "button_primary":
                widget.configure(
                    fg_color=colors["primary"],
                    hover_color=colors["primary_hover"],
                    text_color=colors["text_on_primary"]
                )
            elif widget_type == "button_secondary":
                widget.configure(
                    fg_color=colors["secondary"],
                    hover_color=colors["secondary_hover"],
                    text_color=colors["text_on_primary"]
                )
            elif widget_type == "label":
                widget.configure(text_color=colors["text_primary"])
            elif widget_type == "title":
                widget.configure(text_color=colors["text_primary"])
            # Agregar más tipos según sea necesario
        except Exception:
            pass  # Ignorar errores de configuración

# Instancia global del gestor de diseño
design_manager = DesignManager() 