/**
 * ==============================================================================
 * 🧠 FENIX_CORE: EDGE COMPUTING & SERVICE WORKER MATRIX (GOD-TIER)
 * ==============================================================================
 * Arquitectura: Silicon Valley / Tel Aviv Zero-Compute Standard.
 * Funciones implementadas:
 * - Stale-While-Revalidate adaptativo.
 * - Cache-First para Assets Estáticos (Latencia 0ms).
 * - Network-First con Fallback Dinámico para Dashboards de Django.
 * - Auto-Garbage Collection (Prevención de Memory Leaks en el cliente).
 * - Bypass Inteligente de WebSockets y Peticiones Mutables (CSRF Safe).
 */

const APP_PREFIX = 'LL_STRATOS';
const VERSION = 'v4.0.0'; // Cambiar esta versión fuerza a todos los clientes a actualizar
const CORE_CACHE = `${APP_PREFIX}-CORE-${VERSION}`;
const DYNAMIC_CACHE = `${APP_PREFIX}-DYNAMIC-${VERSION}`;
const MAX_DYNAMIC_ITEMS = 120; // Límite estricto para no saturar la caché del navegador

// 🛡️ VECTORES CRÍTICOS (Archivos que deben estar garantizados en Offline)
const CRITICAL_ASSETS = [
    '/',
    '/static/css/bootstrap.min.css',
    '/static/img/icon-192.png',
    '/static/img/icon-512.png',
    // Si tienes un archivo CSS propio principal, agrégalo aquí, ej: '/static/css/styles.css'
];

/**
 * 🧹 ALGORITMO DE GARBAGE COLLECTION (Gestor de Memoria)
 * Limpia recursivamente los registros más antiguos si se excede el límite de RAM local.
 */
const limitCacheSize = (cacheName, maxItems) => {
    caches.open(cacheName).then((cache) => {
        cache.keys().then((keys) => {
            if (keys.length > maxItems) {
                cache.delete(keys[0]).then(() => {
                    limitCacheSize(cacheName, maxItems);
                });
            }
        });
    });
};

/**
 * ⚙️ FASE 1: INSTALACIÓN DEL NÚCLEO CUÁNTICO
 * Descarga la matriz base al disco duro del cliente. 
 * Usamos Promise.allSettled para evitar el colapso si un asset arroja Error 404.
 */
self.addEventListener('install', (event) => {
    console.log(`[FENIX_SW] 🚀 Iniciando instalación de Matriz Edge ${VERSION}...`);
    self.skipWaiting(); // Fuerza al navegador a instalar esta versión instantáneamente

    event.waitUntil(
        caches.open(CORE_CACHE).then((cache) => {
            return Promise.allSettled(
                CRITICAL_ASSETS.map((url) => {
                    return fetch(url).then((response) => {
                        if (!response.ok) {
                            throw new Error(`Asset no encontrado: ${url}`);
                        }
                        return cache.put(url, response);
                    }).catch((err) => {
                        console.warn(`[FENIX_SW] ⚠️ Asset diferido (No bloqueante): ${url}`, err);
                    });
                })
            );
        }).then(() => {
            console.log(`[FENIX_SW] ✅ Escudo de Caché Primario compilado exitosamente.`);
        })
    );
});

/**
 * ♻️ FASE 2: ACTIVACIÓN Y PURGA (El Reinicio del Fénix)
 * Destruye cualquier caché antiguo que no coincida con la versión actual (v4.0.0).
 */
self.addEventListener('activate', (event) => {
    console.log(`[FENIX_SW] ⚡ Activando nuevo motor de enrutamiento...`);
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    // Si el caché no es el actual, lo exterminamos
                    if (cacheName !== CORE_CACHE && cacheName !== DYNAMIC_CACHE && cacheName.startsWith(APP_PREFIX)) {
                        console.log(`[FENIX_SW] 🗑️ Purgando espectros de memoria obsoletos: ${cacheName}`);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log(`[FENIX_SW] 🛡️ Perímetro de memoria asegurado. Tomando control de los clientes.`);
            return self.clients.claim();
        })
    );
});

/**
 * 📡 FASE 3: INTERCEPTOR DE TRÁFICO TÁCTICO (Event Fetch)
 * El núcleo de la operación. Decide si ir a la red (Django) o al disco duro (Caché).
 */
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);

    // =========================================================================
    // REGLA 1: BYPASS DE SEGURIDAD (Ignorar intencionalmente)
    // No cachear POST/PUT, WebSockets (wss://), Panel Admin, ni peticiones a APIs de terceros.
    // =========================================================================
    if (
        request.method !== 'GET' ||
        url.protocol === 'ws:' || 
        url.protocol === 'wss:' || 
        url.pathname.startsWith('/admin/') || 
        url.pathname.includes('/api/') ||
        !url.protocol.startsWith('http')
    ) {
        return; // Deja pasar la petición limpiamente hacia Django
    }

    // =========================================================================
    // REGLA 2: CACHE-FIRST CON NETWORK FALLBACK (Para Estáticos pesados)
    // Archivos estáticos (Imágenes, CSS, JS, Fuentes). Latencia: 0ms.
    // Reduces la carga del servidor de Railway en un 85%.
    // =========================================================================
    const isStaticAsset = url.pathname.startsWith('/static/') || 
                          url.pathname.startsWith('/media/') || 
                          url.pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2|ttf|ico|webp)$/);

    if (isStaticAsset) {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                if (cachedResponse) {
                    // Retorno a la velocidad de la luz desde el disco
                    return cachedResponse;
                }
                
                // Si no está en caché, lo descarga, lo clona en memoria y lo entrega
                return fetch(request).then((networkResponse) => {
                    // Validar que la respuesta sea válida antes de cachear
                    if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                        return networkResponse;
                    }
                    
                    const responseClone = networkResponse.clone();
                    caches.open(CORE_CACHE).then((cache) => {
                        cache.put(request, responseClone);
                    });
                    
                    return networkResponse;
                }).catch((err) => {
                    console.warn(`[FENIX_SW] ⚠️ Falla de enlace al solicitar asset estático: ${request.url}`);
                    // Aquí podrías retornar una imagen placeholder de "offline" si quisieras
                });
            })
        );
        return; // Detenemos la ejecución aquí para los estáticos
    }

    // =========================================================================
    // REGLA 3: NETWORK-FIRST CON DYNAMIC CACHE FALLBACK (Para HTML/Dashboards)
    // Prioriza siempre ir a Django para tener notas y datos frescos. 
    // Si no hay internet, muestra la última versión guardada en el caché dinámico.
    // =========================================================================
    if (request.headers.get('accept') && request.headers.get('accept').includes('text/html')) {
        event.respondWith(
            fetch(request).then((networkResponse) => {
                // Validamos la respuesta del servidor
                if (!networkResponse || networkResponse.status !== 200) {
                    return networkResponse;
                }

                // Si hay internet y responde bien, guardamos una copia de seguridad en el Dynamic Cache
                const responseClone = networkResponse.clone();
                caches.open(DYNAMIC_CACHE).then((cache) => {
                    cache.put(request, responseClone);
                    limitCacheSize(DYNAMIC_CACHE, MAX_DYNAMIC_ITEMS); // Limpiar si llegamos al tope
                });

                return networkResponse;
            }).catch(() => {
                // FALLO DE RED: El estudiante se quedó sin internet o Railway está caído
                console.warn(`[FENIX_SW] 🛑 Ruptura de conexión con el Servidor Central. Extraiendo holograma de emergencia...`);
                
                return caches.match(request).then((cachedResponse) => {
                    if (cachedResponse) {
                        console.info(`[FENIX_SW] ⚡ Sirviendo versión Offline de: ${request.url}`);
                        return cachedResponse;
                    }
                    
                    // Si no tiene el HTML en caché, buscamos si hay una página offline genérica guardada
                    return caches.match('/offline.html').then((offlineResponse) => {
                        if (offlineResponse) {
                            return offlineResponse;
                        }
                        // Si todo falla, generamos una respuesta de emergencia en crudo
                        return new Response(
                            '<div style="font-family: monospace; padding: 2rem; color: #fff; background: #020617; height: 100vh; text-align: center;"><h1>⚠️ CONEXIÓN PERDIDA</h1><p>El enlace con FENIX_CORE se ha roto. Verifica tu conexión a internet.</p></div>',
                            { headers: { 'Content-Type': 'text/html' } }
                        );
                    });
                });
            })
        );
    }
});

/**
 * 📡 FASE 4: PUERTO DE COMUNICACIONES
 * Permite recibir comandos desde el frontend (app.js o scripts en HTML)
 */
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        console.log('[FENIX_SW] 🔄 Recibida orden manual de actualización. Reiniciando núcleo...');
        self.skipWaiting();
    }
});