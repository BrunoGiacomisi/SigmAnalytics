import json
import os
from typing import Dict, Any
from src.config import CONFIG_FILE, DEFAULT_CONFIG

class ConfigManager:
    # Manejador de configuración persistente del sistema.
    
    def __init__(self):
        self.config_file = CONFIG_FILE
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        # Carga la configuración desde el archivo JSON.
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Asegurar que todas las claves por defecto estén presentes
                    for key, value in DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                # Si no existe el archivo, crear con configuración por defecto
                self.save_config(DEFAULT_CONFIG)
                return DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"Error al cargar configuración: {e}")
            return DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        # Guarda la configuración en el archivo JSON.
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error al guardar configuración: {e}")
            return False
    
    def get(self, key: str, default=None) -> Any:
        # Obtiene un valor de configuración.
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        # Establece un valor de configuración y lo guarda.
        self.config[key] = value
        return self.save_config(self.config)
    
    def update_window_size(self, width: int, height: int) -> bool:
        # Actualiza el tamaño de ventana guardado.
        return self.set("window_size", f"{width}x{height}")
    
    def update_window_position(self, x: int, y: int) -> bool:
        # Actualiza la posición de ventana guardada.
        return self.set("window_position", {"x": x, "y": y})
    
    def get_window_size(self) -> str:
        # Obtiene el tamaño de ventana guardado.
        return self.get("window_size", "1100x700")
    
    def get_window_position(self) -> Dict[str, int]:
        # Obtiene la posición de ventana guardada.
        return self.get("window_position", {"x": None, "y": None})
    
    # Métodos de tema eliminados - la aplicación usa diseño oscuro fijo

# Instancia global del config manager
config_manager = ConfigManager() 