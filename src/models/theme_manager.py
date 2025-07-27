import customtkinter as ctk
from typing import Dict, Any
from src.config import THEMES
from src.models.config_manager import config_manager

class ThemeManager:
    """Manejador de temas del sistema."""
    
    def __init__(self):
        self.current_theme = config_manager.get_theme()
        self.themes = THEMES
    
    def get_current_theme_colors(self) -> Dict[str, str]:
        """Obtiene los colores del tema actual."""
        return self.themes.get(self.current_theme, self.themes["light"])
    
    def apply_theme(self, theme: str, widgets: Dict[str, Any] = None) -> bool:
        """Aplica un tema al sistema."""
        if theme not in self.themes:
            return False
        
        self.current_theme = theme
        config_manager.set_theme(theme)
        
        # Aplicar tema a CustomTkinter
        if theme == "dark":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
        
        # Si se proporcionan widgets, actualizar sus colores
        if widgets:
            self.update_widget_colors(widgets)
        
        return True
    
    def update_widget_colors(self, widgets: Dict[str, Any]) -> None:
        """Actualiza los colores de los widgets según el tema actual."""
        colors = self.get_current_theme_colors()
        
        # Actualizar colores de widgets específicos
        if 'ventana' in widgets:
            widgets['ventana'].configure(fg_color=colors['bg_color'])
        
        if 'frame_principal' in widgets:
            widgets['frame_principal'].configure(fg_color=colors['frame_color'])
        
        if 'titulo' in widgets:
            widgets['titulo'].configure(text_color=colors['text_color'])
        
        if 'boton' in widgets:
            widgets['boton'].configure(
                fg_color=colors['accent_color'],
                hover_color=colors['hover_color']
            )
        
        if 'boton_tema' in widgets:
            widgets['boton_tema'].configure(
                fg_color=colors['accent_color'],
                hover_color=colors['hover_color']
            )
        
        # Actualizar botones "Ampliar"
        for key, widget in widgets.items():
            if 'boton_ampliar' in key.lower() and hasattr(widget, 'configure'):
                try:
                    widget.configure(
                        fg_color=colors['accent_color'],
                        hover_color=colors['hover_color']
                    )
                except:
                    pass
        
        if 'stats_card' in widgets:
            widgets['stats_card'].configure(
                fg_color=colors['stats_bg'],
                border_color=colors['stats_border']
            )
        
        if 'frame_graficos' in widgets:
            widgets['frame_graficos'].configure(fg_color=colors['bg_color'])
        
        # Actualizar colores de texto en labels específicos si están disponibles
        for key, widget in widgets.items():
            if 'label' in key.lower() and hasattr(widget, 'configure'):
                try:
                    widget.configure(text_color=colors['text_color'])
                except:
                    pass  # Ignorar widgets que no soporten text_color
        
        # Actualizar títulos de gráficos específicamente
        for key, widget in widgets.items():
            if 'etiqueta_titulo_' in key.lower() and hasattr(widget, 'configure'):
                try:
                    widget.configure(text_color=colors['title_color'])
                except:
                    pass
    
    def toggle_theme(self, widgets: Dict[str, Any] = None) -> str:
        """Cambia entre tema claro y oscuro."""
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(new_theme, widgets)
        return new_theme
    
    def get_theme_name(self) -> str:
        """Obtiene el nombre del tema actual."""
        return "Oscuro" if self.current_theme == "dark" else "Claro"

# Instancia global del theme manager
theme_manager = ThemeManager() 