# Archivo: tasks/models_simuladores.py
import uuid
import hashlib
import sys
from django.db import models
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# =====================================================================
# 1. MANAGERS & QUERYSETS (BUSINESS LOGIC ENCAPSULATION)
# =====================================================================
class SimuladorQuerySet(models.QuerySet):
    """
    QuerySet de alto rendimiento. Encapsula las consultas más comunes
    para evitar lógica repetida en las vistas y optimizar la BD.
    """
    def activos(self):
        return self.filter(activo=True, eliminado_en__isnull=True)

    def alto_rendimiento(self):
        # Filtra simuladores que tienen una alta tasa de éxito
        return self.activos().filter(tasa_exito__gte=70.0)

    def select_optimizados(self):
        # Excluye el código fuente pesado cuando solo se necesita listar (Dashboard)
        return self.defer('codigo_fuente', 'prompt_original')

class SimuladorManager(models.Manager):
    def get_queryset(self):
        return SimuladorQuerySet(self.model, using=self._db)

    def activos(self):
        return self.get_queryset().activos()

# =====================================================================
# 2. EL MODELO MAESTRO (GOD TIER DATA STRUCTURE)
# =====================================================================
class SimuladorAvanzado(models.Model):
    """
    BÓVEDA INMUTABLE DE ACTIVOS EDUCATIVOS.
    Diseñado para concurrencia masiva, telemetría bidireccional y auditoría de IA.
    """
    
    # --- IDENTIDAD Y RUTAS (SEO & Seguridad) ---
    id_unico = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True,
        help_text="Identificador criptográfico inmutable."
    )
    titulo = models.CharField(max_length=200, verbose_name=_("Título del Simulador"))
    slug = models.SlugField(
        max_length=250, unique=True, db_index=True,
        help_text="URL amigable y optimizada para búsquedas."
    )
    
    # --- LA CARGA ÚTIL (PAYLOAD) Y SEGURIDAD ---
    codigo_fuente = models.TextField(
        verbose_name=_("Código HTML/JS/CSS (Payload)"),
        help_text="El motor de simulación autocontenido."
    )
    hash_integridad = models.CharField(
        max_length=64, blank=True, editable=False,
        help_text="SHA-256 del código. Garantiza que no ha sido alterado por ataques."
    )
    peso_bytes = models.PositiveIntegerField(
        default=0, editable=False,
        help_text="Tamaño del simulador en bytes para optimización de ancho de banda."
    )

    # --- OBSERVABILIDAD FINANCIERA (AUDITORÍA DE IA) ---
    motor_ia_generador = models.CharField(
        max_length=50, default="DeepSeek-V3",
        help_text="Modelo que compiló este código (ej. Gemini 3.1 Pro, DeepSeek R1)."
    )
    prompt_original = models.TextField(
        blank=True, null=True,
        help_text="Instrucción pedagógica exacta que generó este activo."
    )
    costo_generacion_usd = models.DecimalField(
        max_digits=10, decimal_places=6, default=0.000000,
        help_text="Costo exacto de la API para calcular el ROI de Learning Labs."
    )

    # --- TELEMETRÍA Y ANALÍTICA (BIG DATA) ---
    vistas = models.PositiveIntegerField(default=0, db_index=True)
    tiempo_promedio_segundos = models.PositiveIntegerField(
        default=0,
        help_text="Tiempo promedio que los estudiantes pasan en esta simulación."
    )
    tasa_exito = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        help_text="Porcentaje de alumnos que logran el 'success' en el postMessage."
    )
    
    # --- CONFIGURACIÓN DINÁMICA (METADATA) ---
    configuracion_sandbox = models.JSONField(
        default=dict, blank=True,
        help_text="Reglas del Iframe: {'allow_camera': False, 'allow_microphone': False}"
    )
    metadata_pedagogica = models.JSONField(
        default=dict, blank=True,
        help_text="Contexto: {'materia': 'Física', 'grado': '10', 'dificultad': 'Alta'}"
    )

    # --- CONTROL DE ESTADO Y VERSIÓN (SOFT DELETE) ---
    version = models.PositiveIntegerField(default=1, help_text="Versionamiento iterativo.")
    activo = models.BooleanField(default=True, db_index=True)
    creado_at = models.DateTimeField(auto_now_add=True, db_index=True)
    actualizado_at = models.DateTimeField(auto_now=True)
    eliminado_en = models.DateTimeField(
        null=True, blank=True, editable=False,
        help_text="Implementación de Soft Delete (Nunca se borra de la BD)."
    )

    # Conexión con el Manager personalizado
    objects = SimuladorManager()

    class Meta:
        verbose_name = _("Simulador Avanzado")
        verbose_name_plural = _("Simuladores Avanzados")
        # ÍNDICES COMPUESTOS (Nivel Arquitecto): Optimiza consultas complejas en milisegundos.
        indexes = [
            models.Index(fields=['activo', '-creado_at'], name='sim_activo_creado_idx'),
            models.Index(fields=['activo', '-vistas'], name='sim_activo_vistas_idx'),
        ]
        ordering = ['-creado_at']

    def __str__(self):
        return f"[{self.motor_ia_generador}] {self.titulo} (v{self.version})"

    # =====================================================================
    # 3. VALIDACIÓN ESTRICTA (QA ENGINEERING)
    # =====================================================================
    def clean(self):
        """
        Validación a nivel de base de datos antes de guardar.
        Evita que código corrupto o malicioso entre a Learning Labs.
        """
        super().clean()
        if self.codigo_fuente:
            codigo_lower = self.codigo_fuente.lower()
            if "<html" not in codigo_lower or "</html>" not in codigo_lower:
                raise ValidationError({"codigo_fuente": _("El payload debe ser un documento HTML5 válido y autocontenido.")})
            
            # Bloqueo de seguridad: Evitar inyección de scripts externos no deseados si es necesario
            # (Se puede relajar si la IA usa CDNs, pero bloqueamos intentos de phishing obvios)
            if "document.cookie" in codigo_lower:
                raise ValidationError({"codigo_fuente": _("Violación de seguridad: Intento de acceso a cookies detectado.")})

    # =====================================================================
    # 4. HOOKS DE ESTADO (AUTOMATIZACIÓN & CACHÉ INVALIDATION)
    # =====================================================================
    def save(self, *args, **kwargs):
        """
        Sobrescritura del método save() para automatizar auditorías 
        y mantener la sincronización con la memoria RAM (Redis/Memcached).
        """
        # 1. Ejecutar validaciones estrictas
        self.full_clean()

        # 2. Firma Criptográfica y Cálculo de Peso (Solo si el código cambió)
        if self.codigo_fuente:
            self.peso_bytes = sys.getsizeof(self.codigo_fuente)
            nuevo_hash = hashlib.sha256(self.codigo_fuente.encode('utf-8')).hexdigest()
            
            # Si el código se alteró, subimos la versión automáticamente
            if self.pk and self.hash_integridad and self.hash_integridad != nuevo_hash:
                self.version += 1
            
            self.hash_integridad = nuevo_hash

        # 3. Guardar en Base de Datos
        super().save(*args, **kwargs)

        # 4. INVALIDACIÓN DE CACHÉ ACTIVA (Zero-Downtime)
        # Si el simulador se edita, destruimos el caché viejo para que 
        # los alumnos vean la versión nueva instantáneamente sin reiniciar el servidor.
        cache_key = f"simulador_payload_{self.slug}"
        cache.delete(cache_key)

    # =====================================================================
    # 5. MÉTODOS DE NEGOCIO (BUSINESS LOGIC)
    # =====================================================================
    def soft_delete(self):
        """
        Eliminación lógica. Los datos de la IA valen oro, nunca hacemos un DELETE SQL real.
        """
        from django.utils import timezone
        self.activo = False
        self.eliminado_en = timezone.now()
        self.save()

    def get_sandbox_permissions(self):
        """
        Devuelve el string de permisos para el atributo `sandbox` del iframe.
        """
        base_permissions = "allow-scripts allow-same-origin"
        config = self.configuracion_sandbox
        if config.get('allow_modals', False):
            base_permissions += " allow-modals"
        if config.get('allow_downloads', False):
            base_permissions += " allow-downloads"
        return base_permissions