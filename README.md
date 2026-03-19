# 🚀 BIOR Invest AI - Smart Portfolio Advisor

### 📝 Descripción
Plataforma inteligente de gestión de inversiones desarrollada con **Django** y orquestada mediante **Agentes de IA**. BIOR Invest AI permite a los usuarios centralizar y visualizar sus activos (Renta Variable, Inmuebles, etc.) mientras interactúan con un ecosistema **Self-hosted** diseñado para ofrecer asesoría financiera personalizada y privada en tiempo real.

### 🌟 Funcionalidades Destacadas
- **Agentes de IA Financieros:** Sistema basado en agentes que utiliza **Claude (OpenClaw)** para analizar el portafolio del usuario, ejecutar consultas complejas y proponer estrategias de inversión contextuales.
- **Interfaz Híbrida WhatsApp (Voice & Text):** Sistema inteligente que permite la gestión del portafolio mediante mensajes de texto o **notas de voz**. Los audios son procesados localmente con **Faster-Whisper** en Docker, permitiendo que el Agente de IA interprete y ejecute comandos financieros complejos (NLP) con total privacidad, sin que la información salga de la infraestructura privada.
- **Orquestación con n8n:** Flujos de trabajo automatizados para la ingesta de datos, procesamiento de lenguaje natural (NLP) y sincronización entre la interfaz de mensajería y el backend.
- **Estrategia Dinámica:** Selector inteligente de activos que permite filtrar y enfocar la inversión en categorías específicas según el perfil de riesgo detectado por la IA.
- **Notificaciones Inteligentes:** Alertas proactivas vía Email y WhatsApp con resúmenes de rendimiento generados por IA, informando movimientos clave del mercado y del portafolio.

### 🛠️ Stack Tecnológico
- **Backend:** `Django (Python)` & `PostgreSQL`
- **IA/ML:** `Faster-Whisper` (Self-hosted), `Claude (OpenClaw)` & `LangChain`
- **Automatización:** `n8n` (Self-hosted)
- **Infraestructura:** `Docker` & `Dokploy`
- **Cloud:** `CubePath`

### 🔗 Enlaces
- **Repositorio:** [github.com/AlanBIOR/bior-invest-ai](https://github.com/AlanBIOR/bior-invest-ai)
- **Demo:** 🚧 *En desarrollo - Desplegado en infraestructura propia sobre CubePath*

---
Proyecto desarrollado por **BIOR** para la **Hackatón CubePath 2026**.
