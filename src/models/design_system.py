# Sistema de diseño centralizado para SigmAnalytics
# Contiene todas las variables de diseño: colores, espaciado, tipografía, etc.

from typing import Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# COLORES DEL SISTEMA
# ═══════════════════════════════════════════════════════════════════════════════

# Esquema de colores único (diseño oscuro)
COLORS = {
    # Colores primarios (mantener identidad)
    "primary": "#3498db",
    "primary_hover": "#5dade2",
    "secondary": "#566573",
    "secondary_hover": "#6c7b7f",
    
    # Colores de acento
    "accent": "#e74c3c",
    "accent_hover": "#ec7063",
    "success": "#58d68d",
    "warning": "#f7dc6f",
    "info": "#5dade2",
    
    # Fondos
    "background": "#1e1e1e",
    "card_background": "#2d2d2d",
    "surface": "#252525",
    
    # Textos
    "text_primary": "#ffffff",
    "text_secondary": "#b0b0b0",
    "text_muted": "#808080",
    "text_on_primary": "#ffffff",
    
    # Bordes
    "border": "#404040",
    "border_light": "#353535",
    "border_focus": "#3498db",
    
    # Estados
    "hover": "#353535",
    "active": "#404040",
    "disabled": "#2d2d2d",
}

# ═══════════════════════════════════════════════════════════════════════════════
# ESPACIADO (Sistema basado en 8px)
# ═══════════════════════════════════════════════════════════════════════════════

SPACING = {
    "xs": 4,        # 4px
    "sm": 8,        # 8px
    "md": 16,       # 16px
    "lg": 24,       # 24px
    "xl": 32,       # 32px
    "xxl": 40,      # 40px
    "xxxl": 48,     # 48px
}

# ═══════════════════════════════════════════════════════════════════════════════
# TIPOGRAFÍA
# ═══════════════════════════════════════════════════════════════════════════════

TYPOGRAPHY = {
    # Familias de fuentes
    "font_family": "Segoe UI",
    "font_family_mono": "Consolas",
    
    # Tamaños
    "font_xs": 10,
    "font_sm": 11,
    "font_base": 12,
    "font_md": 13,
    "font_lg": 14,
    "font_xl": 16,
    "font_xxl": 18,
    "font_xxxl": 20,
    "font_title": 22,
    "font_hero": 24,
    
    # Pesos
    "font_normal": "normal",
    "font_bold": "bold",
}

# ═══════════════════════════════════════════════════════════════════════════════
# DIMENSIONES Y TAMAÑOS
# ═══════════════════════════════════════════════════════════════════════════════

DIMENSIONS = {
    # Botones
    "button_height": 40,            # Tamaño mínimo táctil
    "button_height_sm": 32,
    "button_height_lg": 48,
    "button_min_width": 80,
    
    # Contenedores
    "container_max_width": 1280,    # Ancho máximo del contenido
    "card_min_height": 120,
    "header_height": 60,
    
    # Bordes
    "border_radius": 8,
    "border_radius_sm": 4,
    "border_radius_lg": 12,
    "border_width": 1,
    
    # Sombras
    "shadow_sm": "0 1px 3px rgba(0,0,0,0.1)",
    "shadow_md": "0 4px 6px rgba(0,0,0,0.1)",
    "shadow_lg": "0 10px 25px rgba(0,0,0,0.1)",
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES HELPER PARA OBTENER VALORES
# ═══════════════════════════════════════════════════════════════════════════════

def get_color(color_name: str) -> str:
    """Obtiene un color del sistema de diseño."""
    return COLORS.get(color_name, "#000000")

def get_spacing(size: str) -> int:
    """Obtiene un valor de espaciado."""
    return SPACING.get(size, SPACING["md"])

def get_font_tuple(size: str, weight: str = "normal") -> tuple:
    """Obtiene una tupla de fuente para CustomTkinter."""
    font_size = TYPOGRAPHY.get(f"font_{size}", TYPOGRAPHY["font_base"])
    return (TYPOGRAPHY["font_family"], font_size, weight)

def get_dimension(dimension_name: str) -> Any:
    """Obtiene una dimensión del sistema."""
    return DIMENSIONS.get(dimension_name, 0)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIONES PREDEFINIDAS
# ═══════════════════════════════════════════════════════════════════════════════

# Configuración de botón primario
BUTTON_PRIMARY = {
    "height": DIMENSIONS["button_height"],
    # Hacemos el texto más protagónico en botones primarios
    "font": get_font_tuple("xl", "bold"),
    "corner_radius": DIMENSIONS["border_radius"],
}

# Configuración de botón secundario
BUTTON_SECONDARY = {
    "height": DIMENSIONS["button_height_sm"],
    "font": get_font_tuple("sm", "normal"),
    "corner_radius": DIMENSIONS["border_radius"],
}

# Configuración de tarjeta
CARD_CONFIG = {
    "corner_radius": DIMENSIONS["border_radius_lg"],
    "border_width": 0,
}

# Configuración de header
HEADER_CONFIG = {
    "height": DIMENSIONS["header_height"],
    "corner_radius": 0,
}
