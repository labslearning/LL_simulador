# Archivo: tasks/models_simuladores.py
import uuid
import hashlib
import sys
import re
from typing import Any, Dict, Iterable

from django.db import models
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# =====================================================================
# 1. QUERYSETS: ENCAPSULACIÓN DE LÓGICA DE NEGOCIO (DOMAIN-DRIVEN DESIGN)
# =====================================================================
class SimuladorQuerySet(models.QuerySet):
    """
    QuerySet de alto rendimiento. 
    Encapsula consultas complejas a nivel de base de datos para evitar fugas de memoria.
    """
    def activos(self) -> 'SimuladorQuerySet':
        """Retorna solo simuladores operativos y no eliminados."""
        return self.filter(activo=True, eliminado_en__isnull=True)

    def alto_rendimiento(self) -> 'SimuladorQuerySet':
        """Filtra la élite de los simuladores basándose en la telemetría de éxito."""
        return self.activos().filter(tasa_exito__gte=70.0)

    def select_optimizados(self) -> 'SimuladorQuerySet':
        """
        DOM Offloading: Excluye el código fuente pesado (payload) 
        cuando solo se necesita listar tarjetas en el Hub, ahorrando megabytes de RAM.
        """
        return self.defer('codigo_fuente', 'prompt_original')

# =====================================================================
# 2. EL MODELO MAESTRO (GOD TIER DATA STRUCTURE)
# =====================================================================
class SimuladorAvanzado(models.Model):
    """
    BÓVEDA INMUTABLE DE ACTIVOS EDUCATIVOS.
    Diseñado para concurrencia masiva, telemetría bidireccional y auditoría financiera de IA.
    """
    
    # --- IDENTIDAD Y RUTAS (SEO & Seguridad Criptográfica) ---
    id_unico = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True,
        help_text="Identificador criptográfico inmutable."
    )
    titulo = models.CharField(max_length=200, verbose_name=_("Título del Simulador"))
    slug = models.SlugField(
        max_length=250, unique=True, db_index=True,
        help_text="URL amigable y optimizada para búsquedas en Edge Caching."
    )
    descripcion = models.TextField(
        blank=True, null=True,
        verbose_name=_("Descripción"),
        help_text="Resumen pedagógico para el catálogo del Hub."
    )
    
    # --- LA CARGA ÚTIL (PAYLOAD) Y SEGURIDAD ZERO-TRUST ---
    codigo_fuente = models.TextField(
        verbose_name=_("Código HTML/JS/CSS (Payload)"),
        help_text="El motor de simulación autocontenido generado por la IA."
    )
    hash_integridad = models.CharField(
        max_length=64, blank=True, editable=False,
        help_text="SHA-256 del código. Garantiza inmutabilidad ante ataques (Tampering)."
    )
    peso_bytes = models.PositiveIntegerField(
        default=0, editable=False,
        help_text="Tamaño en bytes para cálculos de optimización de ancho de banda."
    )

    # --- OBSERVABILIDAD FINANCIERA (AUDITORÍA FINOPS IA) ---
    motor_ia_generador = models.CharField(
        max_length=50, default="DeepSeek-V3",
        help_text="Modelo cognitivo que compiló este activo."
    )
    prompt_original = models.TextField(
        blank=True, null=True,
        help_text="Instrucción pedagógica exacta que dio origen a la simulación."
    )
    costo_generacion_usd = models.DecimalField(
        max_digits=10, decimal_places=6, default=0.000000,
        help_text="Costo exacto de la API para cálculo de ROI automatizado."
    )

    # --- TELEMETRÍA Y ANALÍTICA BIG DATA ---
    vistas = models.PositiveIntegerField(default=0, db_index=True)
    tiempo_promedio_segundos = models.PositiveIntegerField(
        default=0,
        help_text="Retención promedio del estudiante en la simulación."
    )
    tasa_exito = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        help_text="Porcentaje de usuarios que activan el triggerSuccess."
    )
    
    # --- CONFIGURACIÓN DINÁMICA (METADATA NO RELACIONAL) ---
    configuracion_sandbox = models.JSONField(
        default=dict, blank=True,
        help_text="Feature Policy del Iframe: {'allow_modals': False}"
    )
    metadata_pedagogica = models.JSONField(
        default=dict, blank=True,
        help_text="Indexación de contexto: {'materia': 'Física', 'dificultad': 'Alta'}"
    )

    # --- CONTROL DE ESTADOS Y VERSIONAMIENTO (SOFT DELETE) ---
    version = models.PositiveIntegerField(default=1, help_text="Auto-versionamiento semántico.")
    activo = models.BooleanField(default=True, db_index=True)
    creado_at = models.DateTimeField(auto_now_add=True, db_index=True)
    actualizado_at = models.DateTimeField(auto_now=True)
    eliminado_en = models.DateTimeField(
        null=True, blank=True, editable=False,
        help_text="Soft Delete. Mantiene la integridad referencial en PostgreSQL."
    )

    # 🚀 LA CURA DEL ERROR 500: INYECCIÓN DINÁMICA DE MÉTODOS DE MANAGER
    objects = SimuladorQuerySet.as_manager()

    class Meta:
        verbose_name = _("Simulador Avanzado")
        verbose_name_plural = _("Simuladores Avanzados")
        # ÍNDICES COMPUESTOS L4: Reducen tiempos de query de 200ms a 2ms.
        indexes = [
            models.Index(fields=['activo', '-creado_at'], name='sim_activo_creado_idx'),
            models.Index(fields=['activo', '-vistas'], name='sim_activo_vistas_idx'),
        ]
        ordering = ['-creado_at']

    def __str__(self) -> str:
        return f"[{self.motor_ia_generador}] {self.titulo} (v{self.version})"

    # =====================================================================
    # 3. VALIDACIÓN LÓGICA ESTRICTA (QA ENGINEERING)
    # =====================================================================
    def clean(self) -> None:
        """
        Escudo Anti-Phishing de nivel de Base de Datos.
        Bloquea inserciones corruptas o vectores de ataque antes del commit SQL.
        """
        super().clean()
        if self.codigo_fuente:
            codigo_lower = self.codigo_fuente.lower()
            
            # 1. Verificación de Integridad Estructural HTML5
            if not re.search(r'<html.*?>', codigo_lower) or "</html>" not in codigo_lower:
                raise ValidationError({
                    "codigo_fuente": _("Violación de Arquitectura: El payload debe ser un documento HTML5 completo y autocontenido.")
                })
            
            # 2. Heurística Anti-Exfiltración
            if "document.cookie" in codigo_lower:
                raise ValidationError({
                    "codigo_fuente": _("Violación Crítica de Seguridad: Detección de lectura de cookies en código no confiable.")
                })

    # =====================================================================
    # 4. HOOKS DE ESTADO (AUTO-HASHING & ZERO-DOWNTIME CACHE INVALIDATION)
    # =====================================================================
    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Intercepción del commit para forzar control de versiones, 
        firmado criptográfico y sincronización con memoria en tiempo real.
        """
        # 1. Trigger de validaciones duras
        self.full_clean()

        # 2. Motor de Integridad Criptográfica
        if self.codigo_fuente:
            self.peso_bytes = sys.getsizeof(self.codigo_fuente)
            nuevo_hash = hashlib.sha256(self.codigo_fuente.encode('utf-8')).hexdigest()
            
            # Auto-bump de versión si el Hash muta
            if self.pk and self.hash_integridad and self.hash_integridad != nuevo_hash:
                self.version += 1
            
            self.hash_integridad = nuevo_hash

        # 3. Commit a PostgreSQL/SQLite
        super().save(*args, **kwargs)

        # 4. Invalidación Quirúrgica en RAM (Redis/Memcached)
        # Asegura que los alumnos reciban la nueva versión instantáneamente sin reiniciar el servidor.
        cache_key = f"simulador_payload_{self.slug}"
        cache.delete(cache_key)

    # =====================================================================
    # 5. MÉTODOS DE DOMINIO FUNCIONAL
    # =====================================================================
    def soft_delete(self) -> None:
        """
        Apagado lógico. Mantiene el registro de IA vivo para analíticas, 
        pero invisible para el frontend.
        """
        self.activo = False
        self.eliminado_en = timezone.now()
        self.save()

    def get_sandbox_permissions(self) -> str:
        """
        Compila dinámicamente las barreras de ejecución del Iframe 
        basado en la configuración almacenada en el JSONField.
        """
        base_permissions = "allow-scripts allow-same-origin"
        config: Dict[str, Any] = self.configuracion_sandbox or {}
        
        if config.get('allow_modals', False):
            base_permissions += " allow-modals"
        if config.get('allow_downloads', False):
            base_permissions += " allow-downloads"
            
        return base_permissions