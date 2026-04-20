# ===================================================================
# tasks/routing.py (RUTAS WEBSOCKET TIER-GOD)
# ===================================================================

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # 🔔 Ruta para Notificaciones Personales (Campanita & Toasts en tiempo real)
    # 🔒 El '^' asegura que la ruta comience exactamente aquí, evitando route-bleeding
    re_path(r'^ws/notifications/$', consumers.NotificationConsumer.as_asgi()),

    # 💬 Ruta para Chat Grupal (Comunidad / Salas)
    # Captura el nombre de la sala alfanumérica en <room_name>
    re_path(r'^ws/chat/group/(?P<room_name>\w+)/$', consumers.GroupChatConsumer.as_asgi()),
    
    # 🤖 Ruta para Chat Socrático con IA (Copiloto)
    re_path(r'^ws/chat/ai/socratic/$', consumers.SocraticAIConsumer.as_asgi()),
]