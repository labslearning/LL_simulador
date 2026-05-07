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

from .models_simuladores import SimuladorAvanzado

logger = logging.getLogger(__name__)

class MetricsBuffer:
    FLUSH_THRESHOLD = 50

    @classmethod
    def registrar_vista_asincrona(cls, slug: str) -> None:
        cache_key = f"simulador_vistas_buffer_{slug}"
        try:
            vistas_actuales = cache.add(cache_key, 1, timeout=86400)
            if not vistas_actuales:
                vistas_actuales = cache.incr(cache_key)

            if vistas_actuales >= cls.FLUSH_THRESHOLD:
                cache.set(cache_key, 0, timeout=86400)
                SimuladorAvanzado.objects.filter(slug=slug).update(vistas=F('vistas') + cls.FLUSH_THRESHOLD)
                logger.debug(f"MetricsBuffer: Flush completado para simulador '{slug}'.")
        except Exception as e:
            pass

def generar_etag(request: HttpRequest, simulador: SimuladorAvanzado) -> str:
    identificador = f"{simulador.slug}_{simulador.version}_{simulador.hash_integridad}_{request.user.id}"
    return f'W/"{hashlib.md5(identificador.encode("utf-8")).hexdigest()}"'

@login_required(login_url='/login/')
@require_GET
def hub_simuladores(request: HttpRequest) -> HttpResponse:
    query_base = SimuladorAvanzado.objects.activos().select_optimizados().order_by('-creado_at')
    paginator = Paginator(query_base, 12)
    page = request.GET.get('page', 1)
    
    try:
        simuladores = paginator.page(page)
    except PageNotAnInteger:
        simuladores = paginator.page(1)
    except EmptyPage:
        simuladores = paginator.page(paginator.num_pages)

    response = render(request, 'tasks/simuladores/hub.html', {'simuladores': simuladores})
    response['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=60'
    return response


@login_required(login_url='/login/')
@require_GET
def reproductor_god_tier(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Kermel Mode: DEBUG / DEVELOPMENT
    Caché estricto desactivado para permitir hot-reloading del código HTML.
    """
    cache_key_payload = f"simulador_dto_{slug}"
    simulador: Optional[SimuladorAvanzado] = cache.get(cache_key_payload)

    if not simulador:
        simulador = get_object_or_404(SimuladorAvanzado, slug=slug, activo=True)
        import random
        timeout_seguro = 43200 + random.randint(1, 1800)
        cache.set(cache_key_payload, simulador, timeout=timeout_seguro)

    etag = generar_etag(request, simulador)
    
    # 🔥 FIX DE INGENIERÍA INVERSA: 
    # Comentamos el retorno 304 para obligar a Django a leer el HTML modificado.
    # if request.META.get('HTTP_IF_NONE_MATCH') == etag:
    #     MetricsBuffer.registrar_vista_asincrona(slug)
    #     return HttpResponseNotModified()

    MetricsBuffer.registrar_vista_asincrona(slug)

    contexto = {
        'simulador': simulador,
        'sandbox_permissions': simulador.get_sandbox_permissions()
    }
    
    # ⚠️ IMPORTANTE: Asegúrate de que este sea el archivo HTML que estás editando ⚠️
    response = render(request, 'tasks/simuladores/reproductor.html', contexto)
    
    # 🔥 FIX L7: Obligamos al navegador a NO CACHEAR la página bajo ninguna circunstancia
    response['ETag'] = etag
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response['X-Content-Type-Options'] = 'nosniff'

    return response

from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

@login_required(login_url='/login/')
@require_GET
def render_raw_simulador(request, slug):
    """
    Motor JSFiddle: Renderiza el HTML crudo directamente.
    Bypass total de restricciones de Iframe.
    """
    simulador = get_object_or_404(SimuladorAvanzado, slug=slug, activo=True)
    
    response = HttpResponse(simulador.codigo_fuente)
    # Permite que Learning Labs lo incruste sin que el navegador bloquee los scripts
    response['X-Frame-Options'] = 'SAMEORIGIN'
    
    return response