export function initNexusAdvisor() {
    const btnDecision = document.getElementById('btn-decision-mode');
    const resultsContainer = document.getElementById('nexus-results-container');
    
    // Inputs de configuración
    const inputCapital = document.getElementById('input-capital');
    const inputAportacion = document.getElementById('input-aportacion');
    const inputPreferencia = document.getElementById('input-preferencia');

    if (!btnDecision || !resultsContainer) return;

    // --- LÓGICA DE PERSISTENCIA (Cargar último plan guardado al entrar) ---
    const cachedPlan = localStorage.getItem('nexus_last_plan');
    if (cachedPlan) {
        renderNexusCards(JSON.parse(cachedPlan), resultsContainer);
    }

    btnDecision.addEventListener('click', async () => {
        // 1. Preparar datos para el Mentor Senior
        const params = {
            capital_extra: parseFloat(inputCapital.value) || 0,
            aportacion: parseFloat(inputAportacion.value) || 0,
            preferencia: inputPreferencia.value
        };

        // 2. Estado de Carga (UX Premium)
        const originalText = btnDecision.innerHTML;
        btnDecision.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Consultando al Agente Senior...';
        btnDecision.disabled = true;
        
        // Efecto de feedback visual: ocultamos lo viejo suavemente
        resultsContainer.style.opacity = '0.5';

        try {
            const apiUrl = btnDecision.getAttribute('data-url');
            
            // 3. Llamada a la API enviando los parámetros del usuario
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(params)
            });

            if (!response.ok) throw new Error('Fallo en la conexión con el servidor');

            const result = await response.json();

            if (result.status === 'success') {
                const data = result.data;
                
                // 4. Guardar en memoria local para evitar que se pierda al salir/regresar
                localStorage.setItem('nexus_last_plan', JSON.stringify(data));

                // 5. Renderizado
                renderNexusCards(data, resultsContainer);
                resultsContainer.style.opacity = '1';

            } else {
                throw new Error(result.message || 'Error en el motor NEXUS');
            }

        } catch (error) {
            console.error('Error NEXUS:', error);
            resultsContainer.innerHTML = `
                <div class="nexus-error-alert">
                    <i class="fas fa-times-circle"></i> El Agente detectó una anomalía: ${error.message}. Intenta de nuevo.
                </div>
            `;
            resultsContainer.classList.add('is-visible');
            resultsContainer.style.opacity = '1';
        } finally {
            btnDecision.innerHTML = originalText;
            btnDecision.disabled = false;
        }
    });
}

/**
 * Función encargada de dibujar las tarjetas con el diseño Premium
 */
function renderNexusCards(data, container) {
    const nivelRiesgo = data.nivel_riesgo.toLowerCase();
    let riskClass = 'risk-low';
    if (nivelRiesgo.includes('alto') || nivelRiesgo.includes('crítico')) riskClass = 'risk-high';
    else if (nivelRiesgo.includes('medio')) riskClass = 'risk-medium';

    const htmlTarjetas = `
        <div class="nexus-card ${riskClass}">
            <div class="nexus-card-header">
                <span class="nexus-icon-wrapper"><i class="fas fa-exclamation-triangle"></i></span>
                <h3 class="nexus-card-title">Diagnóstico de Riesgo</h3>
            </div>
            <div class="nexus-card-body">
                <p class="nexus-card-text">${data.riesgo_detectado}</p>
            </div>
            <div class="nexus-badge-wrapper">
                <span class="nexus-badge">Nivel: ${data.nivel_riesgo}</span>
            </div>
        </div>

        <div class="nexus-card card-mission">
            <div class="nexus-card-header">
                <span class="nexus-icon-wrapper"><i class="fas fa-bullseye"></i></span>
                <h3 class="nexus-card-title">Tu Misión de Hoy</h3>
            </div>
            <div class="nexus-card-body">
                <p class="nexus-card-text mission-action">${data.accion_inmediata}</p>
                <p class="nexus-card-text mission-quote">" ${data.justificacion} "</p>
            </div>
            <div class="nexus-badge-wrapper">
                <span class="nexus-badge">Objetivo: ${data.porcentaje_objetivo}</span>
            </div>
        </div>

        <div class="nexus-card card-fiscal">
            <div class="nexus-card-header">
                <span class="nexus-icon-wrapper"><i class="fas fa-landmark"></i></span>
                <h3 class="nexus-card-title">Hack Fiscal México</h3>
            </div>
            <div class="nexus-card-body">
                <p class="nexus-card-text">${data.hack_fiscal}</p>
            </div>
            <div class="nexus-badge-wrapper">
                <span class="nexus-badge" style="background: rgba(124, 58, 237, 0.1); color: #a78bfa;">LISR / SAT</span>
            </div>
        </div>
    `;

    container.innerHTML = htmlTarjetas;
    container.classList.add('is-visible');
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}