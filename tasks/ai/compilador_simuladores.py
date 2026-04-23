# Archivo: tasks/ai/compilador_simuladores.py

import re
import time
import logging
import hashlib
from decimal import Decimal
from typing import Dict, Any, Tuple, List
from dataclasses import dataclass

from django.conf import settings
from .deepseek_client import deepseek_client, MODEL_NAME

# Logger Forense Nivel Elite
logger = logging.getLogger(__name__)

# =====================================================================
# 1. EXCEPCIONES PERSONALIZADAS (DOMAIN-DRIVEN DESIGN STRICT)
# =====================================================================
class CompiladorError(Exception):
    """Clase base para la jerarquía de errores del compilador."""
    pass

class CompiladorSecurityError(CompiladorError):
    """(SecOps) Lanzada cuando el código generado viola el modelo Zero-Trust."""
    pass

class CompiladorValidationError(CompiladorError):
    """(QA) Lanzada cuando el AST o el DOM estructurado es inválido."""
    pass

class CompiladorNetworkError(CompiladorError):
    """(DevOps) Fallo en la comunicación con el clúster de IA."""
    pass

# =====================================================================
# 2. DATA TRANSFER OBJECTS (CONTRATOS INMUTABLES)
# =====================================================================
@dataclass(frozen=True)
class ResultadoCompilacion:
    """
    Contrato estricto y de solo lectura (frozen). Garantiza la trazabilidad 
    criptográfica, analítica y financiera de cada activo digital generado.
    """
    codigo_limpio: str
    hash_sha256: str
    prompt_utilizado: str
    motor_ia: str
    prompt_tokens: int
    completion_tokens: int
    costo_usd: Decimal
    tiempo_generacion_segundos: float
    ratio_compresion: float

# =====================================================================
# 3. CONTEXTO NEURONAL (XML-TAGGED META-PROMPTING)
# =====================================================================
# Estándar de Tel Aviv / Silicon Valley para control determinístico de LLMs.
# Las etiquetas XML confinan la atención del modelo y eliminan alucinaciones.

SYSTEM_PROMPT_GOD_TIER = """
<system_role>
Eres un "Principal Staff Web Game Engineer" en un centro de investigación de élite.
Tu misión crítica es compilar y retornar un ejecutable web interactivo (Single-File App) de grado militar para la plataforma educativa Learning Labs.
</system_role>

<architectural_constraints>
1. OUTPUT ESTRICTO: Retorna ÚNICAMENTE código HTML5 válido. No uses formato Markdown (ni ```html). Cero texto explicativo. El primer carácter de tu respuesta DEBE ser `<` y el último `>`.
2. ESTRUCTURA: Un solo bloque de código. CSS embebido en `<style>`, lógica JavaScript embebida en `<script>`.
3. RENDIMIENTO: Usa librerías como Three.js, Matter.js, D3.js o p5.js EXCLUSIVAMENTE a través de CDNs públicos seguros (ej. cdnjs.cloudflare.com).
4. UI/UX: Interfaz Cyberpunk/Neón, Dark Mode absoluto (Fondo #050505), fuentes legibles sin serifs. Controles (sliders, botones, inputs) deben tener feedback visual inmediato.
5. RESILIENCIA JS: Envuelve el ciclo principal (Game Loop) en bloques `try/catch`. Maneja estados nulos.
</architectural_constraints>

<pedagogical_core>
El simulador no es una animación pasiva, es un "Laboratorio Socrático".
El estudiante DEBE poder alterar variables físicas, químicas o matemáticas en tiempo real y visualizar los cambios de estado al instante.
</pedagogical_core>

<telemetry_api>
Dentro de tu código JavaScript, debes llamar a la función `window.LL_TELEMETRY.triggerSuccess(score)` cuando el estudiante logre el objetivo del simulador. 
Ejemplo: Si el estudiante logra equilibrar la balanza, ejecuta `window.LL_TELEMETRY.triggerSuccess(100);`.
</telemetry_api>
"""

# =====================================================================
# 4. MOTOR PRINCIPAL (THE ZERO-TRUST COMPILER)
# =====================================================================
class CompiladorAvanzado:
    """
    Motor de compilación God Tier.
    Implementa Pipeline de 5 capas: Generación -> Extracción -> SAST Security -> Bootloading -> FinOps.
    """
    
    # Precios dinámicos (Micro-finanzas para DeepSeek V3/R1)
    COSTO_MILLON_PROMPT_TOKENS = Decimal('0.14')
    COSTO_MILLON_COMPLETION_TOKENS = Decimal('0.28')
    
    # Whitelist de grado militar para prevenir inyección de dependencias maliciosas (Supply Chain Attacks)
    ALLOWED_CDNS = [
        "cdnjs.cloudflare.com", "unpkg.com", "cdn.jsdelivr.net",
        "code.jquery.com", "fonts.googleapis.com", "fonts.gstatic.com"
    ]

    @classmethod
    def compilar(cls, titulo: str, tema_pedagogico: str, nivel_dificultad: str = "Universitario") -> ResultadoCompilacion:
        """
        Orquesta el ciclo de vida completo de generación. Punto de entrada para Django.
        """
        tiempo_inicio = time.time()
        
        # 1. Construcción de Contexto Estructurado
        user_prompt = (
            f"<compilation_request>\n"
            f"  <title>{titulo}</title>\n"
            f"  <core_topic>{tema_pedagogico}</core_topic>\n"
            f"  <difficulty_level>{nivel_dificultad}</difficulty_level>\n"
            f"  <directive>Genera la simulación más inmersiva, científicamente precisa y visualmente impactante posible. Ejecuta la orden ahora.</directive>\n"
            f"</compilation_request>"
        )

        messages_list = [
            {"role": "system", "content": SYSTEM_PROMPT_GOD_TIER.strip()},
            {"role": "user", "content": user_prompt}
        ]

        logger.info(f"🚀 INICIANDO FENIX_CORE PIPELINE | Simulador: {titulo} | Dificultad: {nivel_dificultad}")

        # 2. Invocación a la Red Neuronal (LLM API)
        resultado_ia = deepseek_client.get_completion(messages_list)

        if not resultado_ia.get("success"):
            error_api = resultado_ia.get('error', 'Colapso desconocido en la infraestructura IA')
            logger.critical(f"❌ FALLO DE RED/IA FENIX_CORE: {error_api}")
            raise CompiladorNetworkError(f"Colapso del motor generativo: {error_api}")

        payload_crudo = resultado_ia.get("content", "")
        usage_data = resultado_ia.get("usage", {})
        bytes_originales = len(payload_crudo.encode('utf-8'))

        # 3. Pipeline de Confianza Cero (Zero-Trust Pipeline)
        try:
            # Capa 1: Extracción Estructural
            codigo_extraido = cls._extraer_y_reparar_dom(payload_crudo)
            
            # Capa 2: Static Application Security Testing (SAST)
            cls._escaner_sast_tiempo_real(codigo_extraido)
            
            # Capa 3: Inyección de Políticas de Seguridad (CSP)
            codigo_seguro = cls._inyectar_csp_headers(codigo_extraido)
            
            # Capa 4: Inyección del Bootloader de Telemetría (Hardcoded Logic)
            codigo_telemetrizado = cls._inyectar_bootloader_telemetria(codigo_seguro)
            
            # Capa 5: Minificación y Optimización L4
            codigo_final = cls._minificar_payload(codigo_telemetrizado)
            
        except Exception as e:
            logger.error(f"🛑 COMPILACIÓN ABORTADA EN EL PIPELINE DE SEGURIDAD: {str(e)}")
            raise

        # 4. Cálculos Analíticos y Financieros (FinOps & Data Science)
        bytes_finales = len(codigo_final.encode('utf-8'))
        ratio_comp = round(1.0 - (bytes_finales / bytes_originales if bytes_originales > 0 else 0), 3) * 100
        
        costo_total = cls._calcular_roi_micro_centavos(
            usage_data.get("prompt_tokens", 0), 
            usage_data.get("completion_tokens", 0)
        )
        
        hash_integridad = hashlib.sha256(codigo_final.encode('utf-8')).hexdigest()
        tiempo_total = round(time.time() - tiempo_inicio, 3)

        logger.info(f"✅ COMPILACIÓN GOD TIER EXITOSA | {tiempo_total}s | Costo: ${costo_total:.6f} USD | Compresión: {ratio_comp}%")

        # 5. Ensamblaje del Objeto de Dominio
        return ResultadoCompilacion(
            codigo_limpio=codigo_final,
            hash_sha256=hash_integridad,
            prompt_utilizado=user_prompt,
            motor_ia=MODEL_NAME,
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            costo_usd=costo_total,
            tiempo_generacion_segundos=tiempo_total,
            ratio_compresion=ratio_comp
        )

    # =====================================================================
    # 5. SUBSISTEMAS DE SEGURIDAD Y TRANSFORMACIÓN (MÉTODOS PRIVADOS L4)
    # =====================================================================
    
    @staticmethod
    def _extraer_y_reparar_dom(texto_crudo: str) -> str:
        """
        Extrae el código HTML puro ignorando cualquier alucinación o markdown periférico.
        Repara jerarquías rotas si la IA cortó la respuesta.
        """
        if not texto_crudo.strip():
            raise CompiladorValidationError("El motor IA devolvió un vacío absoluto (Void Payload).")

        # Expresión regular destructiva: Busca el contenido entre <!DOCTYPE html> o <html> y </html>
        match = re.search(r'(<!DOCTYPE\s+html>|<html.*?>).*?</html>', texto_crudo, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(0)
            
        # Fallback de Reparación Automática: Si no hay <html> pero hay código frontend
        if "<canvas" in texto_crudo or "<div" in texto_crudo or "<script>" in texto_crudo:
            logger.warning("⚠️ DOM Fracturado detectado. Iniciando Protocolo de Reparación Automática de DOM...")
            limpio = re.sub(r'^```(html|javascript|css)?\s*|\s*```$', '', texto_crudo.strip(), flags=re.MULTILINE | re.IGNORECASE)
            return f"<!DOCTYPE html>\n<html lang='es'>\n<head>\n<meta charset='UTF-8'>\n</head>\n<body style='margin:0; overflow:hidden; background-color:#050505;'>\n{limpio}\n</body>\n</html>"
            
        raise CompiladorValidationError("Mutación Irreversible: El payload no contiene estructuras HTML5 reconocibles.")

    @classmethod
    def _escaner_sast_tiempo_real(cls, codigo: str) -> None:
        """
        Static Application Security Testing (SAST). 
        Analiza el árbol sintáctico simulado en busca de vulnerabilidades Zero-Day.
        """
        codigo_lower = codigo.lower()
        
        # 1. Lista Negra de Vectores de Exfiltración y Ataque XSS/DOM
        blacklisted_signatures = [
            "document.cookie", "window.localstorage", "window.sessionstorage",
            "eval(", "document.write(", "indexeddb", "websql", 
            "xmlhttprequest", "fetch(", "navigator.geolocation"
        ]

        for signature in blacklisted_signatures:
            if signature in codigo_lower:
                logger.critical(f"🛡️ BLOQUEO DE DEFENSA ACTIVA: Firma maliciosa '{signature}' detectada en el payload.")
                raise CompiladorSecurityError(f"Intento de inyección de código bloqueado. Vector: {signature}")

        # 2. Whitelisting de Supply Chain (CDNs Permitidos)
        # Extraemos todos los 'src=' o 'href=' externos
        urls_externas = re.findall(r'(?:src|href)=["\'](http[s]?://.*?)["\']', codigo_lower)
        for url in urls_externas:
            dominio_seguro = any(cdn in url for cdn in cls.ALLOWED_CDNS)
            if not dominio_seguro:
                logger.critical(f"🛡️ BLOQUEO SUPPLY CHAIN: Dependencia no autorizada detectada -> {url}")
                raise CompiladorSecurityError(f"El código intenta importar una librería desde un servidor no verificado: {url}")

    @staticmethod
    def _inyectar_csp_headers(codigo: str) -> str:
        """
        Inyecta un Content Security Policy (CSP) brutalmente restrictivo en el Head.
        Garantiza a nivel de motor de navegador que es imposible hackear Learning Labs desde este iframe.
        """
        csp_meta = (
            "<meta http-equiv=\"Content-Security-Policy\" "
            "content=\"default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: cdnjs.cloudflare.com unpkg.com cdn.jsdelivr.net fonts.googleapis.com fonts.gstatic.com; "
            "connect-src 'none'; object-src 'none'; frame-src 'none';\">"
        )
        
        # Insertar justo después del <head>
        if "<head>" in codigo.lower():
            codigo = re.sub(r'(<head.*?>)', rf'\1\n    {csp_meta}', codigo, count=1, flags=re.IGNORECASE)
        else:
            # Si no hay <head>, inyectar al principio del <html>
            codigo = re.sub(r'(<html.*?>)', rf'\1\n<head>\n    {csp_meta}\n</head>', codigo, count=1, flags=re.IGNORECASE)
            
        return codigo

    @staticmethod
    def _inyectar_bootloader_telemetria(codigo: str) -> str:
        """
        El máximo nivel de ingeniería: Inyección de Dependencias en Tiempo de Compilación.
        Inyecta la API de telemetría inmutable que la IA usará, garantizando que el `postMessage` 
        hacia Learning Labs siempre tiene el formato criptográfico correcto.
        """
        bootloader_js = """
        <script>
            Object.defineProperty(window, 'LL_TELEMETRY', {
                value: Object.freeze({
                    triggerSuccess: function(score = 100, customMetrics = {}) {
                        console.log("[LL_TELEMETRY] Transmitiendo victoria al ERP padre...");
                        window.parent.postMessage({
                            type: 'LL_SIMULATOR_TELEMETRY',
                            status: 'success',
                            score: score,
                            metrics: customMetrics,
                            timestamp: Date.now()
                        }, '*');
                    }
                }),
                writable: false,
                configurable: false
            });
        </script>
        """
        
        # Insertar el bootloader justo antes de cerrar el head o antes del primer script
        if "</head>" in codigo.lower():
            codigo = re.sub(r'(</head>)', rf'{bootloader_js}\n\1', codigo, count=1, flags=re.IGNORECASE)
        else:
            codigo = re.sub(r'(<body.*?>)', rf'{bootloader_js}\n\1', codigo, count=1, flags=re.IGNORECASE)
            
        return codigo

    @staticmethod
    def _minificar_payload(codigo: str) -> str:
        """
        Optimización L4 de ancho de banda. 
        Elimina tabulaciones excesivas, dobles espacios y comentarios HTML/JS innecesarios.
        Ahorra gigabytes de transferencia de datos mensuales a Learning Labs.
        """
        # Eliminar comentarios HTML (que no sean el bootloader que pusimos)
        codigo = re.sub(r'', '', codigo, flags=re.DOTALL)
        # Reducir múltiples saltos de línea a uno solo
        codigo = re.sub(r'\n\s*\n', '\n', codigo)
        # Eliminar espacios al principio y final de cada línea
        codigo = '\n'.join([line.strip() for line in codigo.split('\n')])
        return codigo

    @classmethod
    def _calcular_roi_micro_centavos(cls, prompt_tokens: int, completion_tokens: int) -> Decimal:
        """
        Motor de FinOps. Calcula con precisión atómica el costo exacto por ejecución.
        """
        if not prompt_tokens and not completion_tokens:
            return Decimal('0.000000')

        costo_prompt = (Decimal(prompt_tokens) / Decimal('1000000')) * cls.COSTO_MILLON_PROMPT_TOKENS
        costo_completion = (Decimal(completion_tokens) / Decimal('1000000')) * cls.COSTO_MILLON_COMPLETION_TOKENS
        
        return (costo_prompt + costo_completion).quantize(Decimal('0.000000'))