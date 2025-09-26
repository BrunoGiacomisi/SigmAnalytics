# src/services/representados_contactos.py
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.config import USER_DATA_DIR
from src.representados import CODIGOS_REPRESENTADOS

logger = logging.getLogger(__name__)

# Ruta del archivo JSON de contactos
CONTACTOS_JSON_PATH = USER_DATA_DIR / "data" / "contactos_representados.json"

def _ensure_contacts_file_exists() -> None:
    """
    Asegura que el archivo JSON de contactos exista.
    Si no existe, lo crea con todos los códigos conocidos y listas vacías.
    """
    if not CONTACTOS_JSON_PATH.exists():
        logger.info(f"Creando archivo de contactos: {CONTACTOS_JSON_PATH}")
        
        # Crear estructura base con todos los códigos conocidos
        contactos_base = {}
        for codigo in CODIGOS_REPRESENTADOS:
            contactos_base[codigo] = {
                "nombre": "",  # Se puede llenar manualmente o desde otra fuente
                "emails": [],
                "cc": [],
                "bcc": []
            }
        
        # Asegurar que el directorio padre existe
        CONTACTOS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Escribir archivo inicial
        with open(CONTACTOS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(contactos_base, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Archivo de contactos creado con {len(contactos_base)} códigos")

def _load_contacts_data() -> Dict:
    """Cargar datos de contactos desde el archivo JSON."""
    _ensure_contacts_file_exists()
    
    try:
        with open(CONTACTOS_JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error cargando contactos: {e}")
        return {}

def _save_contacts_data(data: Dict) -> None:
    """Guardar datos de contactos en el archivo JSON."""
    try:
        with open(CONTACTOS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Datos de contactos guardados correctamente")
    except Exception as e:
        logger.error(f"Error guardando contactos: {e}")
        raise

def list_codes() -> List[str]:
    """
    Retorna la lista de todos los códigos de representados conocidos.
    Esta función reemplaza el uso directo de CODIGOS_REPRESENTADOS.
    """
    contactos = _load_contacts_data()
    # Combinar códigos del JSON con los conocidos para asegurar completitud
    codigos_json = set(contactos.keys())
    codigos_conocidos = set(CODIGOS_REPRESENTADOS)
    todos_los_codigos = list(codigos_json.union(codigos_conocidos))
    return sorted(todos_los_codigos)

def get_contact_info(codigo: str) -> Optional[Dict]:
    """
    Obtiene la información de contacto para un código de representado específico.
    
    Args:
        codigo: Código del representado (ej: "888801015433")
    
    Returns:
        Diccionario con información de contacto o None si no existe
        Formato: {
            "nombre": str,
            "emails": List[str],
            "cc": List[str],
            "bcc": List[str]
        }
    """
    contactos = _load_contacts_data()
    return contactos.get(codigo)

def upsert_contact_info(codigo: str, data: Dict) -> bool:
    """
    Inserta o actualiza la información de contacto para un representado.
    
    Args:
        codigo: Código del representado
        data: Diccionario con la información de contacto
              Debe contener: nombre, emails, cc, bcc
    
    Returns:
        True si la operación fue exitosa, False en caso contrario
    """
    try:
        contactos = _load_contacts_data()
        
        # Validar estructura de datos
        required_fields = ["nombre", "emails", "cc", "bcc"]
        for field in required_fields:
            if field not in data:
                logger.error(f"Campo requerido faltante: {field}")
                return False
        
        # Validar que las listas sean realmente listas
        for field in ["emails", "cc", "bcc"]:
            if not isinstance(data[field], list):
                logger.error(f"El campo {field} debe ser una lista")
                return False
        
        # Actualizar información
        contactos[codigo] = {
            "nombre": str(data["nombre"]),
            "emails": list(data["emails"]),
            "cc": list(data["cc"]),
            "bcc": list(data["bcc"])
        }
        
        _save_contacts_data(contactos)
        logger.info(f"Información de contacto actualizada para código {codigo}")
        return True
        
    except Exception as e:
        logger.error(f"Error actualizando contacto {codigo}: {e}")
        return False

def get_codes_with_emails() -> List[Tuple[str, str]]:
    """
    Retorna lista de tuplas (codigo, nombre) para representados que tienen emails configurados.
    Útil para mostrar solo los representados que pueden recibir correos.
    """
    contactos = _load_contacts_data()
    codes_with_emails = []
    
    for codigo, info in contactos.items():
        if info.get("emails") and len(info["emails"]) > 0:
            nombre = info.get("nombre", f"Representado {codigo}")
            codes_with_emails.append((codigo, nombre))
    
    return sorted(codes_with_emails, key=lambda x: x[1])  # Ordenar por nombre

def initialize_contacts_from_existing_file() -> None:
    """
    Inicializa los contactos desde el archivo contactos_representados.json que ya existe
    en la raíz del proyecto. Esta función migra los datos existentes.
    """
    # Ruta del archivo existente en la raíz del proyecto
    existing_file = Path("contactos_representados.json")
    
    if existing_file.exists():
        logger.info("Migrando contactos desde archivo existente...")
        
        try:
            with open(existing_file, 'r', encoding='utf-8') as f:
                contactos_existentes = json.load(f)
            
            # Asegurar que el directorio destino existe
            CONTACTOS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # Copiar al nuevo directorio
            with open(CONTACTOS_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(contactos_existentes, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Contactos migrados exitosamente a {CONTACTOS_JSON_PATH}")
            
        except Exception as e:
            logger.error(f"Error migrando contactos: {e}")
            # En caso de error, crear archivo base
            _ensure_contacts_file_exists()
    else:
        # Si no existe archivo previo, crear uno nuevo
        _ensure_contacts_file_exists()

# Inicializar el sistema de contactos al importar el módulo
initialize_contacts_from_existing_file()
