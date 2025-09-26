# src/services/gmail_service.py
import base64
import logging
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config import USER_DATA_DIR

logger = logging.getLogger(__name__)

# Scopes necesarios para Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

# Rutas de autenticación
AUTH_DIR = USER_DATA_DIR / "auth"
CREDENTIALS_FILE = AUTH_DIR / "credentials.json"
TOKEN_FILE = AUTH_DIR / "token.json"


class GmailDraftService:
    """Servicio para crear borradores de Gmail con adjuntos PDF."""
    
    def __init__(self):
        self.service = None
        self._ensure_auth_directory()
    
    def _ensure_auth_directory(self):
        """Asegura que el directorio de autenticación exista."""
        AUTH_DIR.mkdir(parents=True, exist_ok=True)
    
    def _authenticate(self) -> Optional[Credentials]:
        """
        Maneja la autenticación OAuth con Google.
        
        Returns:
            Credentials object si la autenticación es exitosa, None en caso contrario
        """
        creds = None
        
        # Cargar token existente si existe
        if TOKEN_FILE.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
                logger.info("Token existente cargado")
            except Exception as e:
                logger.warning(f"Error cargando token existente: {e}")
        
        # Si no hay credenciales válidas disponibles, iniciar flujo OAuth
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Refrescando token expirado...")
                    creds.refresh(Request())
                    logger.info("Token refrescado exitosamente")
                except Exception as e:
                    logger.error(f"Error refrescando token: {e}")
                    creds = None
            
            if not creds:
                if not CREDENTIALS_FILE.exists():
                    logger.error(f"Archivo credentials.json no encontrado en {CREDENTIALS_FILE}")
                    raise FileNotFoundError(
                        f"Archivo credentials.json requerido no encontrado en {CREDENTIALS_FILE}. "
                        "Descárgalo desde Google Cloud Console y colócalo en esa ubicación."
                    )
                
                try:
                    logger.info("Iniciando flujo de autenticación OAuth...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(CREDENTIALS_FILE), SCOPES
                    )
                    # Forzar selección de cuenta
                    flow.authorization_url(prompt='select_account')
                    creds = flow.run_local_server(port=8080)
                    logger.info("Autenticación OAuth completada")
                except Exception as e:
                    logger.error(f"Error en flujo OAuth: {e}")
                    raise
            
            # Guardar credenciales para próximas ejecuciones
            if creds:
                try:
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                    logger.info(f"Token guardado en {TOKEN_FILE}")
                except Exception as e:
                    logger.warning(f"Error guardando token: {e}")
        
        return creds
    
    def _initialize_service(self) -> bool:
        """
        Inicializa el servicio de Gmail.
        
        Returns:
            True si la inicialización es exitosa, False en caso contrario
        """
        try:
            creds = self._authenticate()
            if not creds:
                return False
            
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Servicio de Gmail inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando servicio Gmail: {e}")
            return False
    
    def _create_message_with_attachments(
        self,
        to_addresses: List[str],
        cc_addresses: List[str],
        bcc_addresses: List[str],
        subject: str,
        body: str,
        attachment_paths: List[Path]
    ) -> str:
        """
        Crea un mensaje MIME con adjuntos y lo codifica en base64.
        
        Args:
            to_addresses: Lista de direcciones TO
            cc_addresses: Lista de direcciones CC
            bcc_addresses: Lista de direcciones BCC
            subject: Asunto del correo
            body: Cuerpo del correo en HTML
            attachment_paths: Lista de rutas a archivos PDF para adjuntar
        
        Returns:
            Mensaje codificado en base64 URL-safe
        """
        # Crear mensaje multipart
        message = MIMEMultipart()
        
        # Configurar headers
        if to_addresses:
            message['To'] = ', '.join(to_addresses)
        if cc_addresses:
            message['Cc'] = ', '.join(cc_addresses)
        if bcc_addresses:
            message['Bcc'] = ', '.join(bcc_addresses)
        
        message['Subject'] = subject
        
        # Agregar cuerpo del mensaje
        body_part = MIMEText(body, 'html', 'utf-8')
        message.attach(body_part)
        
        # Agregar adjuntos PDF
        for attachment_path in attachment_paths:
            if not attachment_path.exists():
                logger.warning(f"Archivo adjunto no encontrado: {attachment_path}")
                continue
            
            try:
                with open(attachment_path, 'rb') as f:
                    attachment_data = f.read()
                
                part = MIMEBase('application', 'pdf')
                part.set_payload(attachment_data)
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{attachment_path.name}"'
                )
                message.attach(part)
                logger.info(f"Adjunto agregado: {attachment_path.name}")
                
            except Exception as e:
                logger.error(f"Error adjuntando archivo {attachment_path}: {e}")
                raise
        
        # Codificar mensaje completo
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return raw_message
    
    def create_draft_with_attachments(
        self,
        to_addresses: List[str],
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None,
        subject: str = "",
        body: str = "",
        attachment_paths: Optional[List[Path]] = None
    ) -> Dict[str, Any]:
        """
        Crea un borrador de Gmail con adjuntos PDF.
        
        Args:
            to_addresses: Lista de direcciones TO (requerido)
            cc_addresses: Lista de direcciones CC (opcional)
            bcc_addresses: Lista de direcciones BCC (opcional)
            subject: Asunto del correo
            body: Cuerpo del correo en HTML
            attachment_paths: Lista de rutas a archivos PDF
        
        Returns:
            Diccionario con resultado de la operación:
            {
                "success": bool,
                "draft_id": str (si success=True),
                "message": str,
                "error": str (si success=False)
            }
        """
        # Validar parámetros
        if not to_addresses:
            return {
                "success": False,
                "error": "Se requiere al menos una dirección TO",
                "message": "Error: No se especificaron destinatarios"
            }
        
        # Valores por defecto
        cc_addresses = cc_addresses or []
        bcc_addresses = bcc_addresses or []
        attachment_paths = attachment_paths or []
        
        try:
            # Inicializar servicio si no está inicializado
            if not self.service:
                if not self._initialize_service():
                    return {
                        "success": False,
                        "error": "No se pudo inicializar el servicio Gmail",
                        "message": "Error de autenticación. Verifica tus credenciales."
                    }
            
            # Crear mensaje
            raw_message = self._create_message_with_attachments(
                to_addresses=to_addresses,
                cc_addresses=cc_addresses,
                bcc_addresses=bcc_addresses,
                subject=subject,
                body=body,
                attachment_paths=attachment_paths
            )
            
            # Crear borrador con reintentos
            draft_body = {
                'message': {
                    'raw': raw_message
                }
            }
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = self.service.users().drafts().create(
                        userId="me",
                        body=draft_body
                    ).execute()
                    
                    draft_id = result.get('id', '')
                    logger.info(f"Borrador creado exitosamente. ID: {draft_id}")
                    
                    return {
                        "success": True,
                        "draft_id": draft_id,
                        "message": f"Borrador creado exitosamente (ID: {draft_id})",
                        "attachments_count": len(attachment_paths)
                    }
                    
                except HttpError as e:
                    if e.resp.status in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                        # Error transitorio, reintentar
                        wait_time = 2 ** attempt  # Backoff exponencial
                        logger.warning(f"Error transitorio (intento {attempt + 1}/{max_retries}): {e}. Reintentando en {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Error permanente o se agotaron los reintentos
                        logger.error(f"Error HTTP creando borrador: {e}")
                        return {
                            "success": False,
                            "error": f"Error HTTP {e.resp.status}: {e}",
                            "message": f"Error creando borrador: {self._get_user_friendly_error(e)}"
                        }
                
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"Error general (intento {attempt + 1}/{max_retries}): {e}. Reintentando en {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Error creando borrador: {e}")
                        return {
                            "success": False,
                            "error": str(e),
                            "message": f"Error inesperado: {e}"
                        }
        
        except Exception as e:
            logger.error(f"Error general en create_draft_with_attachments: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Error creando borrador: {e}"
            }
    
    def _get_user_friendly_error(self, error: HttpError) -> str:
        """Convierte errores HTTP en mensajes amigables para el usuario."""
        if error.resp.status == 401:
            return "Token de autenticación inválido. Reautoriza la aplicación."
        elif error.resp.status == 403:
            return "Permisos insuficientes. Verifica los scopes de la aplicación."
        elif error.resp.status == 429:
            return "Límite de velocidad excedido. Intenta nuevamente en unos minutos."
        elif error.resp.status >= 500:
            return "Error del servidor de Google. Intenta nuevamente más tarde."
        else:
            return f"Error HTTP {error.resp.status}"
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión con Gmail.
        
        Returns:
            Diccionario con resultado de la prueba
        """
        try:
            if not self._initialize_service():
                return {
                    "success": False,
                    "message": "No se pudo inicializar el servicio Gmail"
                }
            
            # Intentar obtener perfil del usuario como prueba
            profile = self.service.users().getProfile(userId="me").execute()
            email = profile.get('emailAddress', 'Unknown')
            
            return {
                "success": True,
                "message": f"Conectado exitosamente como {email}",
                "email": email
            }
            
        except Exception as e:
            logger.error(f"Error probando conexión Gmail: {e}")
            return {
                "success": False,
                "message": f"Error de conexión: {e}"
            }
