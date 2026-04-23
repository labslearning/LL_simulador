# Archivo: tasks/views_simuladores.py
import logging
import hashlib
from typing import Optional

from django.shortcuts import render, get_object_or_404
from django.core.cache import cache
from django.db.models import F
from django.http import HttpResponseNotModified, HttpRequest, HttpResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Importamos el modelo God Tier que creamos en el paso anterior
from .models_simuladores import SimuladorAvanzado

# Logger de Operaciones Nivel Elite
logger = logging.getLogger(__name__)

# =====================================================================
# 1. SUBSISTEMA DE ANALÍTICA ASÍNCRONA (WRITE-BEHIND CACHE PATTERN)
# =====================================================================
class MetricsBuffer:
    """
    Sistema de buffering en RAM para evitar el bloqueo de filas en SQL (Lock Contention).
    En lugar de hacer un UPDATE en PostgreSQL por cada estudiante, acumulamos
    las visitas en Redis/Memcached y solo escribimos en la Base de Datos en bloques.
    """
    FLUSH_THRESHOLD = 50  # Cada 50 visitas en RAM, se hace 1 escritura en SQL.

    @classmethod
    def registrar_vista_asincrona(cls, slug: str) -> None:
        cache_key = f"simulador_vistas_buffer_{slug}"
        
        try:
            # Incremento atómico en memoria RAM (O(1), latencia < 1ms)
            vistas_actuales = cache.add(cache_key, 1, timeout=86400)
            if not vistas_actuales:
                vistas_actuales = cache.incr(cache_key)

            # Cuando el buffer se llena, vaciamos a PostgreSQL (Flush to Disk)
            if vistas_actuales >= cls.FLUSH_THRESHOLD:
                # Reseteamos el buffer de forma atómica
                cache.set(cache_key, 0, timeout=86400)
                # Una sola escritura SQL para 50 usuarios. Reducción del 98% en carga de DB.
                SimuladorAvanzado.objects.filter(slug=slug).update(vistas=F('vistas') + cls.FLUSH_THRESHOLD)
                logger.debug(f"MetricsBuffer: Flush completado para simulador '{slug}'.")
                
        except Exception as e:
            logger.error(f"Fallo en MetricsBuffer (Operación no crítica). Error: {str(e)}")
            # Fallback elegante: Si Redis falla, no bloqueamos la experiencia del usuario.
            pass

# =====================================================================
# 2. MOTOR DE OPTIMIZACIÓN DE RED (EDGE CACHING & ETAGS)
# =====================================================================
def generar_etag(request: HttpRequest, simulador: SimuladorAvanzado) -> str:
    """
    Genera una huella digital criptográfica (ETag) basada en la versión del juego
    y el usuario. Permite devolver un código HTTP 304 (Not Modified).
    Costo de servidor y transferencia = $0.00 si el alumno ya tiene el juego en su PC.
    """
    identificador = f"{simulador.slug}_{simulador.version}_{simulador.hash_integridad}_{request.user.id}"
    return f'W/"{hashlib.md5(identificador.encode("utf-8")).hexdigest()}"'

# =====================================================================
# 3. CONTROLADORES DE TRÁFICO (VIEWS) GOD TIER
# =====================================================================

@login_required(login_url='/login/')  # Seguridad: Solo estudiantes matriculados
@require_GET                          # Seguridad: Bloquea mutaciones (POST/DELETE) en endpoints de lectura
def hub_simuladores(request: HttpRequest) -> HttpResponse:
    """
    El 'Netflix' de los laboratorios.
    Optimizado con paginación diferida y exclusión de payloads gigantes.
    """
    # 1. Usamos el custom manager select_optimizados() del modelo God Tier.
    # Esto evita cargar los megabytes de código fuente en la memoria de Django.
    query_base = SimuladorAvanzado.objects.alto_rendimiento().select_optimizados().order_by('-vistas')
    
    # 2. Paginación robusta (Evita ataques de agotamiento de memoria)
    paginator = Paginator(query_base, 12)  # 12 juegos por página
    page = request.GET.get('page', 1)
    
    try:
        simuladores = paginator.page(page)
    except PageNotAnInteger:
        simuladores = paginator.page(1)
    except EmptyPage:
        # Si piden la página 9999, devolvemos la última existente de forma segura
        simuladores = paginator.page(paginator.num_pages)

    # 3. Configuración de Edge Headers para que Cloudflare cachee el Hub temporalmente
    response = render(request, 'tasks/simuladores/hub.html', {'simuladores': simuladores})
    response['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=60'  # 5 minutos de caché
    
    return response


@login_required(login_url='/login/')
@require_GET
def reproductor_god_tier(request: HttpRequest, slug: str) -> HttpResponse:
    """
    El motor de inyección de código. Diseñado para resistir ataques DDoS y
    picos de tráfico (Slashdot effect) garantizando latencia cero.
    """
    cache_key_payload = f"simulador_dto_{slug}"
    
    # ---------------------------------------------------------
    # FASE 1: BÚSQUEDA EN MEMORIA RAM (LATENCIA ULTRA-BAJA)
    # ---------------------------------------------------------
    simulador: Optional[SimuladorAvanzado] = cache.get(cache_key_payload)

    if not simulador:
        logger.info(f"Cache Miss. Accediendo a bóveda principal para: {slug}")
        # Búsqueda en disco (PostgreSQL)
        simulador = get_object_or_404(SimuladorAvanzado, slug=slug, activo=True)
        
        # Guardamos en RAM. Usamos un timeout con "Jitter" (aleatoriedad)
        # Esto previene el 'Cache Stampede' donde miles de juegos expiran al mismo exacto milisegundo.
        # 12 horas base + hasta 30 minutos de aleatoriedad.
        import random
        timeout_seguro = 43200 + random.randint(1, 1800)
        cache.set(cache_key_payload, simulador, timeout=timeout_seguro)

    # ---------------------------------------------------------
    # FASE 2: OPTIMIZACIÓN DE ANCHO DE BANDA (BROWSER CACHING)
    # ---------------------------------------------------------
    etag = generar_etag(request, simulador)
    
    # Si el navegador del alumno ya tiene exactamente esta versión del código, 
    # abortamos el envío y le decimos al navegador que use su disco duro.
    if request.META.get('HTTP_IF_NONE_MATCH') == etag:
        logger.debug(f"Ahorro de red (HTTP 304). Sirviendo desde PC del alumno: {slug}")
        # Analítica asíncrona en memoria RAM (Write-Behind) aunque no rendericemos
        MetricsBuffer.registrar_vista_asincrona(slug)
        return HttpResponseNotModified()

    # ---------------------------------------------------------
    # FASE 3: TELEMETRÍA DE ALTO RENDIMIENTO (WRITE-BEHIND)
    # ---------------------------------------------------------
    # Esto elimina el cuello de botella que tenías en la versión anterior.
    MetricsBuffer.registrar_vista_asincrona(slug)

    # ---------------------------------------------------------
    # FASE 4: ENSAMBLAJE DE SEGURIDAD (HTTP HEADERS)
    # ---------------------------------------------------------
    contexto = {
        'simulador': simulador,
        'sandbox_permissions': simulador.get_sandbox_permissions() # Viene del modelo God Tier
    }
    
    response = render(request, 'tasks/simuladores/reproductor.html', contexto)
    
    # Cabeceras de Rendimiento y Seguridad
    response['ETag'] = etag
    response['Cache-Control'] = 'private, max-age=86400, must-revalidate' # Cachea por 24h en el navegador del alumno
    
    # Protege a Learning Labs de ataques Clickjacking asegurando que este reproductor
    # solo pueda ser embebido por el mismo servidor, no por un atacante externo.
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response['X-Content-Type-Options'] = 'nosniff'

    return response