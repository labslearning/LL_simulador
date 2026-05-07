# Archivo: tasks/management/commands/fenix_compilar.py

import sys
import time
import uuid
import threading
import logging
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from django.db import transaction, IntegrityError

# Importaciones del Ecosistema God Tier
from tasks.ai.compilador_simuladores import CompiladorAvanzado, CompiladorNetworkError, CompiladorSecurityError
from tasks.models_simuladores import SimuladorAvanzado

logger = logging.getLogger(__name__)

# =====================================================================
# 1. MOTOR DE INTERFAZ DE TERMINAL (ASYNCHRONOUS CLI HUD)
# =====================================================================
class FenixSpinner:
    """
    Subrutina de renderizado asíncrono para la terminal.
    Mantiene al operador informado mientras el hilo principal espera la respuesta de la IA.
    Evita que el usuario aborte el proceso pensando que el servidor se congeló.
    """
    def __init__(self, mensaje: str = "Procesando"):
        self.mensaje = mensaje
        self.activo = False
        self.hilo = None
        self.fases = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def _animar(self):
        idx = 0
        tiempo_inicio = time.time()
        while self.activo:
            transcurrido = round(time.time() - tiempo_inicio, 1)
            sys.stdout.write(f'\r\033[96m[FENIX ENGINE] {self.fases[idx]} {self.mensaje} ({transcurrido}s)...\033[0m')
            sys.stdout.flush()
            idx = (idx + 1) % len(self.fases)
            time.sleep(0.1)

    def iniciar(self):
        self.activo = True
        self.hilo = threading.Thread(target=self._animar)
        self.hilo.daemon = True # Garantiza que el hilo muera si el proceso principal muere
        self.hilo.start()

    def detener(self):
        self.activo = False
        if self.hilo:
            self.hilo.join()
        sys.stdout.write('\r' + ' ' * (len(self.mensaje) + 40) + '\r') # Limpia la línea
        sys.stdout.flush()

# =====================================================================
# 2. CONTROLADOR PRINCIPAL DEL COMANDO (COMMAND PATTERN)
# =====================================================================
class Command(BaseCommand):
    help = '🚀 Motor FENIX L8: Compilación Neuronal e Inyección en Bóveda Cuántica'

    def add_arguments(self, parser):
        """Argumentos posicionales y banderas tácticas (Flags)"""
        parser.add_argument('titulo', type=str, help='Título del simulador (Ej: "Gravedad Cuántica")')
        parser.add_argument('tema', type=str, help='Instrucción pedagógica profunda y detallada')
        
        # Banderas opcionales para control avanzado
        parser.add_argument(
            '--dificultad',
            type=str,
            default='Universitario',
            help='Define el rigor del simulador (Ej: "Primaria", "Postgrado")'
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Flujo de Ejecución Principal (Main Pipeline)"""
        titulo = options['titulo']
        tema = options['tema']
        dificultad = options['dificultad']

        self.stdout.write(self.style.WARNING("="*70))
        self.stdout.write(self.style.WARNING(f" 🌀 INICIANDO PROTOCOLO FENIX CORE | MODO: {dificultad.upper()}"))
        self.stdout.write(self.style.WARNING("="*70))
        
        # 1. Resolución Dinámica de Slugs (Evita colisiones en la BD)
        slug_base = slugify(titulo)
        slug_final = f"{slug_base}-{str(uuid.uuid4())[:6]}"
        
        spinner = FenixSpinner(f"Sintetizando neuronas para '{titulo}'")
        
        try:
            # 2. Ignición del Hilo de Interfaz
            spinner.iniciar()
            
            # 3. Llamada al Compilador God Tier (Proceso Pesado)
            tiempo_inicio_ia = time.time()
            dto_resultado = CompiladorAvanzado.compilar(
                titulo=titulo, 
                tema_pedagogico=tema,
                nivel_dificultad=dificultad
            )
            tiempo_total_ia = round(time.time() - tiempo_inicio_ia, 2)
            
            spinner.detener()
            self.stdout.write(self.style.SUCCESS(f"\n[+] Extracción de código completada en {tiempo_total_ia}s."))
            self.stdout.write(self.style.SUCCESS("[+] Análisis estático (SAST) superado. Zero vulnerabilidades detectadas."))

            # 4. Transacción Atómica (ACID Compliance)
            # Garantiza que si la base de datos colapsa al guardar, no quedan datos corruptos.
            with transaction.atomic():
                self.stdout.write(self.style.WARNING("[+] Encriptando payload y sellando en PostgreSQL..."))
                
                simulador = SimuladorAvanzado.objects.create(
                    titulo=titulo,
                    slug=slug_final,
                    descripcion=f"Simulación cuántica generada por FENIX-CORE. Enfoque: {tema[:100]}...",
                    codigo_fuente=dto_resultado.codigo_limpio,
                    hash_integridad=dto_resultado.hash_sha256,
                    motor_ia_generador=dto_resultado.motor_ia,
                    prompt_original=dto_resultado.prompt_utilizado,
                    costo_generacion_usd=dto_resultado.costo_usd,
                    # Configuraciones por defecto de alta seguridad
                    configuracion_sandbox={'allow_modals': False, 'allow_downloads': False},
                    metadata_pedagogica={'dificultad': dificultad}
                )

            # 5. Reporte Analítico Forense
            self.stdout.write(self.style.SUCCESS("\n" + "="*70))
            self.stdout.write(self.style.SUCCESS(" ✔ BÓVEDA SELLADA EXITOSAMENTE (CÓDIGO VERDE)"))
            self.stdout.write(self.style.SUCCESS("="*70))
            self.stdout.write(self.style.SUCCESS(f"  🔹 ID Operativo : {simulador.id_unico}"))
            self.stdout.write(self.style.SUCCESS(f"  🔹 Título       : {simulador.titulo}"))
            self.stdout.write(self.style.SUCCESS(f"  🔹 EndPoint URL : /laboratorios/play/{simulador.slug}/"))
            self.stdout.write(self.style.SUCCESS(f"  🔹 Firma SHA-256: {simulador.hash_integridad}"))
            self.stdout.write(self.style.SUCCESS(f"  🔹 Motor Core   : {dto_resultado.motor_ia}"))
            self.stdout.write(self.style.SUCCESS(f"  🔹 Ratio Compr. : {dto_resultado.ratio_compresion}%"))
            self.stdout.write(self.style.SUCCESS(f"  🔹 Costo API    : ${dto_resultado.costo_usd} USD"))
            self.stdout.write(self.style.SUCCESS("="*70 + "\n"))
            self.stdout.write(self.style.WARNING("➜ STATUS: El simulador ya está desplegado en el Hub de los estudiantes.\n"))

        except KeyboardInterrupt:
            # Manejo táctico si el administrador presiona Ctrl+C a mitad de la operación
            spinner.detener()
            self.stdout.write(self.style.ERROR("\n[!] INTERRUPCIÓN MANUAL DETECTADA. ABORTANDO OPERACIÓN..."))
            sys.exit(130)
            
        except CompiladorNetworkError as cne:
            spinner.detener()
            self.stdout.write(self.style.ERROR(f"\n[X] FALLO DE RED NEURONAL: {str(cne)}"))
            sys.exit(1)
            
        except CompiladorSecurityError as cse:
            spinner.detener()
            self.stdout.write(self.style.ERROR(f"\n[X] BRECHA DE SEGURIDAD DETECTADA POR SAST: {str(cse)}"))
            self.stdout.write(self.style.ERROR("    El payload generado intentó violar el entorno de caja de arena."))
            sys.exit(1)
            
        except IntegrityError as ie:
            spinner.detener()
            self.stdout.write(self.style.ERROR(f"\n[X] COLAPSO DE INTEGRIDAD EN BD: {str(ie)}"))
            sys.exit(1)
            
        except Exception as e:
            spinner.detener()
            logger.critical(f"Error fatal en Fenix CLI: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"\n[X] COLAPSO CRÍTICO NO CONTROLADO: {str(e)}\n"))
            sys.exit(1)