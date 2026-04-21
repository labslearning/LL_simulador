# tasks/ai/deepseek_client.py

import os
import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings
from .constants import MODEL_NAME

# Configuración del Logger Forense
logger = logging.getLogger(__name__)

class DeepSeekClient:
    """
    CLIENTE HTTP DE GRADO INDUSTRIAL PARA DEEPSEEK (GOD-TIER ARCHITECTURE).
    Optimizado para reportes de alta densidad (Tier 1000), con Connection Pooling,
    Auto-Retries exponenciales, Telemetría Forense y Fallback de Variables de Entorno.
    """

    API_URL = "https://api.deepseek.com/chat/completions"
    
    # 🔥 AUMENTADO AL MÁXIMO PRÁCTICO: 300 segundos (5 minutos)
    # Esto permite procesar contextos masivos con múltiples tablas sin interrupciones.
    TIMEOUT_SECONDS = 300

    def __init__(self):
        """
        Inicialización del motor de red. 
        Implementa Connection Pooling y estrategias de reintento automático para máxima resiliencia.
        """
        self.session = requests.Session()
        
        # Estrategia de reintento de grado militar (Tel Aviv/Silicon Valley standard)
        # Reintenta automáticamente en caso de cuellos de botella (429) o fallos de servidor (500, 502, 503, 504)
        retries = Retry(
            total=3,
            backoff_factor=1.5, # Crece exponencialmente: 1.5s, 3s, 6s...
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_completion(self, messages_list, config=None):
        """
        Envía mensajes a DeepSeek y retorna respuesta + uso de tokens.
        """
        start_time = time.time()
        logger.info(f"🚀 FENIX_CORE: Iniciando transmisión a DeepSeek (Modelo: {MODEL_NAME})")

        # ------------------------------------------------------------------
        # 1. VALIDACIÓN DE API KEY (HÍBRIDA / OS-LEVEL BYPASS)
        # ------------------------------------------------------------------
        # Prioridad 1: Settings de Django
        # Prioridad 2: Extracción directa desde el OS (Railway Environment Variables)
        raw_api_key = getattr(settings, "DEEPSEEK_API_KEY", None) or os.environ.get("DEEPSEEK_API_KEY")
        
        if not raw_api_key:
            error_msg = "🔥 FATAL_ERROR: DEEPSEEK_API_KEY no detectada. Verifique variables de entorno en Railway."
            logger.critical(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

        # Limpieza de caracteres invisibles o saltos de línea inyectados por la nube
        api_key = raw_api_key.strip()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # ------------------------------------------------------------------
        # 2. CONFIGURACIÓN BASE + OVERRIDE
        # ------------------------------------------------------------------
        final_config = {
            "temperature": 0.7,
            # 🔥 AUMENTADO A 4000 para evitar que la respuesta se corte en reportes extensos
            "max_tokens": 4000,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }

        if isinstance(config, dict):
            final_config.update(config)

        payload = {
            "model": MODEL_NAME,
            "messages": messages_list,
            "stream": False,
            **final_config
        }

        # ------------------------------------------------------------------
        # 3. LLAMADA HTTP (USANDO CONNECTION POOLING)
        # ------------------------------------------------------------------
        try:
            logger.debug(f"📡 Payload preparado. Historial de {len(messages_list)} bloques. Transmitiendo...")
            
            response = self.session.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=self.TIMEOUT_SECONDS 
            )

            # --------------------------------------------------------------
            # 4. MANEJO DE ERRORES DE SALDO O API (TELEMETRÍA CRÍTICA)
            # --------------------------------------------------------------
            if response.status_code != 200:
                error_msg = response.text
                if "insufficient_balance" in error_msg:
                    error_msg = "Saldo insuficiente en la cuenta de DeepSeek. Por favor recarga créditos."
                
                # Reporte forense del error exacto que envía la API externa
                logger.error(f"🛑 RECHAZO DEEPSEEK [HTTP {response.status_code}]: {error_msg}")
                return {
                    "success": False,
                    "error": f"DeepSeek API Error {response.status_code}: {error_msg}"
                }

            # --------------------------------------------------------------
            # 5. PROCESAR RESPUESTA EXITOSA
            # --------------------------------------------------------------
            data = response.json()

            try:
                ai_message = data["choices"][0]["message"]["content"]
                usage_data = data.get("usage", {})
                request_id = data.get("id", "unknown_request_id")
                
                elapsed_time = round(time.time() - start_time, 2)
                total_tokens = usage_data.get("total_tokens", 0)
                logger.info(f"✅ Recepción FENIX_CORE Completada: {total_tokens} tokens procesados en {elapsed_time}s. [ReqID: {request_id}]")
                
            except (KeyError, IndexError):
                logger.error(f"🧩 CORRUPCIÓN DE DATOS: Formato JSON inesperado devuelto por DeepSeek: {data}")
                return {
                    "success": False,
                    "error": "Formato inesperado en la respuesta de DeepSeek."
                }

            return {
                "success": True,
                "content": ai_message,
                "request_id": request_id,
                "usage": {
                    "prompt_tokens": usage_data.get("prompt_tokens", 0),
                    "completion_tokens": usage_data.get("completion_tokens", 0),
                    "total_tokens": total_tokens
                }
            }

        # ------------------------------------------------------------------
        # 6. MANEJO DE EXCEPCIONES DE RED (FAIL-SAFES)
        # ------------------------------------------------------------------
        except requests.exceptions.Timeout:
            logger.warning(f"⏳ TIMEOUT CRÍTICO: DeepSeek excedió los {self.TIMEOUT_SECONDS}s permitidos.")
            return {
                "success": False, 
                "error": f"Timeout Crítico: La IA excedió los {self.TIMEOUT_SECONDS}s de procesamiento."
            }
        except requests.exceptions.ConnectionError:
            logger.critical("🔌 RUPTURA DE ENLACE: Imposible contactar a DeepSeek. Posible fallo DNS o bloqueo de red.")
            return {"success": False, "error": "Error de conexión con el proveedor IA: Verifica estado de red."}
        except Exception as e:
            logger.critical(f"💥 COLAPSO INTERNO NO MANEJADO EN DEEPSEEK CLIENT: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Error inesperado del motor: {str(e)}"}

# INSTANCIA GLOBAL (Mantiene vivo el Connection Pool)
deepseek_client = DeepSeekClient()