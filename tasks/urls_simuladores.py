# Archivo: tasks/urls_simuladores.py
from django.urls import path
from . import views_simuladores

urlpatterns = [
    path('', views_simuladores.hub_simuladores, name='hub_simuladores'),
    path('play/<slug:slug>/', views_simuladores.reproductor_god_tier, name='reproductor_god_tier'),
]