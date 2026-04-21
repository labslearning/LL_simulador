import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone

# Infraestructura Stratos-AI
from .ai.orchestrator import ai_orchestrator 
from .ai.constants import ACCION_TUTOR_PARETO

logger = logging.getLogger(__name__)
User = get_user_model()

@csrf_exempt
@login_required
def api_ai_agent(request):
    """
    ⚡ MOTOR FRONT-CONTROLLER ESTRATOS v2.4 (INDUSTRIAL GRADE)
    Maneja el flujo asíncrono entre el Frontend y el Orquestador de DeepSeek.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'content': '🚨 Método de transmisión inválido.'}, status=405)

    try:
        # Intercepción de carga útil
        raw_data = request.body.decode('utf-8')
        data = json.loads(raw_data)
        
        # Extracción resiliente (acepta múltiples nomenclaturas de frontend)
        action_type = data.get('action_type') or data.get('action')
        user_query = data.get('query') or data.get('user_query', '')
        params = data.get('params', {})
        historial = data.get('historial', [])

        # Lógica de Continuidad Constructivista
        if not action_type and user_query:
            # Si hay texto pero no acción, es una respuesta al modelo Socrático
            action_type = 'chat_socratico' # Alineado con el frontend

        if not action_type:
            return JsonResponse({'success': False, 'content': '⚠️ Protocolo incompleto: Falta definición de intención (intent).'}, status=400)

        # ---------------------------------------------------------
        # SEGURIDAD DE ACCESO Y ELEVACIÓN DE PRIVILEGIOS
        # ---------------------------------------------------------
        target_user_id = params.get('target_user_id')
        if target_user_id:
            perfil = getattr(request.user, 'perfil', None)
            # Validación por ROL (más seguro que por nombre de grupo)
            es_autorizado = perfil and perfil.rol in ['DOCENTE', 'ADMINISTRADOR', 'COORD_ACADEMICO', 'PSICOLOGO']
            
            if not es_autorizado and not request.user.is_staff:
                 logger.warning(f"🚫 Intento de acceso no autorizado a datos de terceros por: {request.user.username}")
                 return JsonResponse({'success': False, 'content': '⛔ Acceso denegado: Privilegios insuficientes.'}, status=403)
            
            try:
                params['target_user'] = User.objects.select_related('perfil').get(id=target_user_id)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'content': '❌ Error: El expediente del estudiante no existe.'}, status=404)

        # ---------------------------------------------------------
        # EJECUCIÓN EN EL ORQUESTADOR (DEEPSEEK CORE)
        # ---------------------------------------------------------
        logger.info(f"🤖 IA-REQUEST [{action_type}] - User: {request.user.username}")
        
        # El orquestador procesa la lógica pedagógica, PEI y SIEE
        response_data = ai_orchestrator.process_request(
            user=request.user,
            action_type=action_type,
            user_query=user_query,
            historial=historial,
            **params
        )
        
        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'content': '🛑 Error: Fragmentación de datos JSON.'}, status=400)
        
    except Exception as e:
        # Captura forense del error
        logger.critical(f"💥 FALLO CRÍTICO MOTOR IA: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False, 
            'content': '📡 Error de enlace con el satélite Stratos-AI. Reintentando sincronización...'
        }, status=500)