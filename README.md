# BIOR Invest AI 🚀
**Tracker de Inversiones y Análisis de Portafolio impulsado por IA.**

> **🔗 Enlaces Rápidos:**
> - **[🚀 DEMO EN VIVO](https://invest-ai.bior-studio.com)**
> - **[💬 PROBAR ASESOR EN WHATSAPP](https://wa.me/5212414208768?text=Hola,%20ayúdame%20con%20mi%20portafolio)**
> - **[📺 VIDEO PRESENTACIÓN](https://tu-enlace-al-video.com)**

---

## 📑 Abstract e Introducción

**BIOR Invest AI** es una plataforma integral de gestión patrimonial diseñada específicamente para el entorno macroeconómico y fiscal mexicano. El sistema está desarrollado para democratizar el acceso a la educación financiera, permitiendo a los usuarios que mantienen capital estático o en instrumentos de bajo riesgo (como CETES o Efectivo) dar el salto hacia la construcción de un portafolio diversificado que aproveche el poder matemático del interés compuesto.

El diferenciador técnico del proyecto y su función estrella es un **Agente de IA integrado** (potenciado por LLMs), accesible tanto por interfaz web como por canales conversacionales asíncronos (WhatsApp). Este agente monitorea la distribución real de los activos del usuario y ejecuta análisis cuantitativos para sugerir optimizaciones en tiempo real. 

Para garantizar un estándar institucional en las recomendaciones, el motor analítico está fundamentado empíricamente en las estrategias de diversificación de **[Long Angle](https://www.longangle.com/)** (comunidad global de inversionistas de alto patrimonio). La plataforma adapta y parametriza estos principios para que cualquier usuario minorista pueda construir un portafolio resiliente.

A nivel de infraestructura, el ecosistema consolida proyecciones algorítmicas y procesamiento de lenguaje natural en una arquitectura altamente escalable. El despliegue se orquesta en su totalidad sobre Ubuntu 24.04 utilizando Dokploy dentro de la infraestructura de alto rendimiento de **CubePath**.

## 1. 💡 Utilidad del Proyecto: ¿Qué problema resolvemos?

En México, proteger tu dinero de la inflación y entender cómo funcionan los impuestos (como el ISR o los beneficios de las SOFIPOS) suele ser un dolor de cabeza. Por eso, mucha gente deja su dinero estático o se queda solo con herramientas básicas, perdiendo la oportunidad de diversificar.

**BIOR Invest AI** llega para romper esa barrera. Tomamos las estrategias de diversificación que usan los expertos en finanzas (basadas en la comunidad *Long Angle*) y las "traducimos" para que cualquier persona pueda aplicarlas a su propio bolsillo.

Más que ser una simple libreta digital para anotar qué compraste, el sistema actúa como un proyector de tu futuro financiero. Para lograrlo, el motor de la plataforma calcula el interés compuesto real de tu portafolio usando este modelo:

$$VF = \sum_{i=1}^{n} \left[ VP_i(1 + r_i)^t + A_i \frac{(1 + r_i)^t - 1}{r_i} \right]$$

*¿Qué significa esta ecuación en la práctica? Básicamente, calculamos tu Valor Futuro ($VF$) tomando tu capital inicial ($VP$), y le sumamos el impacto multiplicador de tus aportaciones mensuales ($A$) junto con el rendimiento específico que te da cada activo ($r$) a lo largo del tiempo ($t$).*

![Demostración del Dashboard BIOR](ruta/a/tu/gif_del_dashboard.gif)
*Fig. 1: El dashboard calculando en tiempo real las proyecciones de crecimiento con base en los activos del usuario.*

## 2. 🏗️ Arquitectura de Infraestructura

Se desplego toda la infraestructura en la nube de **CubePath**, ubicando nuestro servidor en Miami, FL, para asegurar la latencia más baja posible al conectarnos con las APIs de OpenAI, CoinGecko y Banxico.

En lugar de derrochar recursos, aplicamos un enfoque de **arquitectura optimizada**. Logramos correr todo el ecosistema (Web + IA + Automatización) de manera fluida en una instancia **gp.nano** de CubePath.

**¿Cómo estructuramos el servidor (1 vCPU, 2 GB RAM, 40 GB Storage)?**

1. **Orquestación y Seguridad Automatizada (Dokploy + Docker):** Utilizamos Dokploy como nuestro panel de control (PaaS) para gestionar los contenedores Docker. Dokploy se encargó de la magia del enrutamiento interno (Traefik), conectando nuestro dominio personalizado (`invest-ai.bior-studio.com`) y emitiendo automáticamente los certificados SSL para garantizar que todo el tráfico viaje encriptado (HTTPS).

2. **Base de Datos Ligera y Eficiente (SQLite):**
   Para proteger la memoria RAM del servidor (2 GB) y evitar cuellos de botella, tomamos la decisión técnica de omitir motores pesados como PostgreSQL o MySQL. En su lugar, utilizamos **SQLite** integrado de forma nativa en Django. Al ser una base de datos basada en archivos, nos da lecturas y escrituras rapidísimas con un consumo de recursos casi nulo, ideal para la gestión de perfiles de esta etapa.

3. **Motor de Automatización Aislado (n8n):**
   Para darle vida a nuestro asistente de WhatsApp, desplegamos un contenedor de **n8n** operando en paralelo con Django. Este contenedor funciona como el "puente de comunicaciones": recibe las notas de voz de los usuarios por WhatsApp, las procesa, consulta a la IA y devuelve las estrategias financieras, todo centralizado bajo nuestro mismo dominio.

### Diagrama de Topología de Red (Capa L7)
```mermaid
graph TD
    %% Entidades Externas
    Client[Cliente Web / Móvil]
    WA[Usuario WhatsApp]
    
    %% Infraestructura CubePath
    subgraph CubePath_Cloud_VPS [CubePath VPS - Ubuntu 24.04 Miami]
        Proxy[Reverse Proxy / SSL]
        
        subgraph Docker_Dokploy_Engine [Red Docker Orchestrada por Dokploy]
            Django[Django 5.x Backend]
            DB[(Relational DB)]
            N8N[n8n Automation Node]
        end
    end
    
    %% APIs y Servicios Cloud
    Banxico[Banxico API - Tasas]
    CoinGecko[CoinGecko API - Cripto]
    OpenAI[OpenAI - Whisper & GPT-4]
    
    %% Flujos de Datos
    Client <-->|HTTPS / TLS 1.3| Proxy
    Proxy <-->|Port 8000| Django
    Django <-->|ORM| DB
    Django -->|Fetch HTTP| Banxico
    Django -->|Fetch HTTP| CoinGecko
    
    WA <-->|Webhook Event| Proxy
    Proxy <-->|Port 5678| N8N
    N8N <-->|Bridge API POST| Django
    N8N <-->|API REST| OpenAI
```

*Fig. 2: Diagrama arquitectónico detallando el flujo de datos entre el usuario final, la infraestructura en CubePath y los microservicios acoplados.*

---

## 3. ⚙️ Implementación Técnica: Backend y Frontend

### 3.1. Núcleo Monolítico (Django & Python)
El backend actúa como la única fuente de verdad (SSOT), manejando la lógica de negocio y la capa de seguridad.
- **Data Fetching Híbrido:** Integración de módulos `services.py` para consumir la API de Banco de México (Banxico) y obtener tasas reales de CETES (ej. SF43936), asegurando proyecciones con datos fidedignos del mercado.
- **Enrutamiento Dinámico:** Patrón de diseño MVC (MVT en Django) utilizando resolutores de *slugs* (`/detalle/<slug:slug>/`) para inyectar dinámicamente contextos de renderizado sin duplicación de código.

### 3.2. Arquitectura Frontend Modular (Vanilla JS)
Se adoptó un enfoque *Zero-Framework* para el core de la interfaz, estructurando el código en módulos ES6 (`calculadora.js`, `portfolio.js`, `auth.js`) orquestados por un `main.js` limpio mediante el patrón *Facade*.
- **Mecanismos de Sincronización:** Uso de `debouncing` (500ms) en la captura de *inputs* para mitigar la sobrecarga de solicitudes `POST /guardar-progreso/` al servidor, protegiendo el I/O de la base de datos.
- **Buscador Asíncrono de Activos:** Motor híbrido que cruza diccionarios de memoria local (activos fiat) con llamadas HTTP en tiempo real a CoinGecko para indexación de criptoactivos, disparando eventos del DOM (`dispatchEvent`) de manera programática.

![Buscador Híbrido en Acción](ruta/a/tu/imagen_del_buscador.png)
*Fig. 3: Módulo de búsqueda reactiva integrando fuentes locales y externas.*

---

## 4. 🧠 Creatividad: Tu asesor de inversiones en la Web y en WhatsApp

La gran diferencia de este proyecto es que no necesitas estar pegado a la computadora para recibir consejos. Logramos que la Inteligencia Artificial salga del navegador y llegue directamente a tu celular.

### 4.1. El Asistente Inteligente del Dashboard (Python + IA)
Dentro de la página pusimos un chat que no es un bot cualquiera. Este asistente tiene permiso para "leer" cómo tienes repartido tu dinero en tu portafolio de Django. 
- **¿Qué hace?** Compara lo que tú tienes invertido contra el modelo ideal de *Long Angle*.
- **¿Cuál es el resultado?** Te escribe una lista de consejos personalizados para que sepas exactamente qué activos te faltan comprar para correr menos riesgos y ganar más.

### 4.2. El Puente de Audio: Hablándole a BIOR por WhatsApp (n8n)
Para que fuera más fácil de usar, creamos un sistema de automatización en **n8n** (que también vive dentro de nuestro servidor en CubePath). Esto permite que el usuario le mande un audio a BIOR como si fuera un mensaje a un amigo.

> **👉 [¡Haz clic aquí para enviar un audio de prueba por WhatsApp!](https://wa.me/5212414208768?text=Hola,%20quiero%20analizar%20mi%20inversión)**

**Así funciona el camino de tu mensaje:**
1. **Recibimos el audio:** Capturamos la nota de voz que mandas desde WhatsApp.
2. **De voz a texto:** Usamos una herramienta llamada Whisper para "escuchar" el audio y convertirlo en texto.
3. **Análisis experto:** Ese texto se lo pasamos a la IA, la cual ya sabe de finanzas mexicanas, impuestos y estrategias de inversión.
4. **Respuesta rápida:** La IA genera un consejo útil y n8n te lo envía de vuelta por texto a tu chat.

![Flujo de Trabajo en n8n](ruta/a/tu/imagen_del_nodo_n8n.png)
*Fig. 4: El mapa de pasos que sigue n8n para procesar tus mensajes de voz.*

## 5. 🎨 Experiencia del Usuario (UX/UI)

El diseño de la interfaz prioriza la carga cognitiva reducida y la legibilidad de datos financieros complejos.
- **Visualización de Datos:** Integración de `Chart.js` para renderizar gráficas de dona reactivas (Doughnut Charts) que reflejan instantáneamente los rebalanceos del portafolio.
- **Retroalimentación Visual:** Sistema de notificaciones no intrusivas (Toasts) implementado con `SweetAlert2` y validación de estado asíncrono para operaciones CRUD de activos.
- **Diseño Responsivo:** Tablas de datos con paginación algorítmica calculada en el cliente y adaptación *mobile-first*.

![Visualización de Gráficas](ruta/a/tu/imagen_de_la_grafica.png)
*Fig. 5: Componente de visualización estratégica reflejando la distribución de activos.*

---

## 6. 📦 Guía de Despliegue (Reproducibilidad)

El proyecto está empaquetado para ser desplegado eficientemente en infraestructura Linux (probado en Ubuntu 24.04).

### Prerrequisitos
- Servidor VPS (Recomendado: [CubePath](https://cubepath.com/))
- Docker y Docker Compose instalados.
- Instancia de Dokploy (Opcional, para gestión gráfica).

### Pasos de Instalación Rápida

1. Clonar el repositorio:
   ```bash
   git clone [https://github.com/AlanBIOR/bior-invest-ai.git](https://github.com/AlanBIOR/bior-invest-ai.git)
   cd bior-invest-ai
   ```
   
2. Configurar el entorno virtual y dependencias:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configurar variables de entorno (`.env`):
   ```env
   SECRET_KEY=tu_django_secret
   DEBUG=False
   BANXICO_TOKEN=tu_token_banxico
   OPENAI_API_KEY=tu_token_openai
   ```

4. Ejecutar migraciones y levantar el servicio (vía Gunicorn/Uvicorn en producción):
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py runserver 0.0.0.0:8000
   ```

---

✨ **Un proyecto de [Alan Alfonso Rodríguez Ibarra](https://github.com/AlanBIOR)**

Desarrollar **BIOR Invest AI** para la **CubePath Hackathon 2026** fue una experiencia brutal. Me encantó el reto de exprimir al máximo un VPS para crear una herramienta que realmente ayude a las personas a mejorar sus finanzas y entender el poder de su dinero. ¡Gracias por ser parte de este camino y por revisar mi trabajo! 
