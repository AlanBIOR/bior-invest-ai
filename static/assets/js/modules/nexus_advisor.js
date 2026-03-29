export function initNexusAdvisor() {
    const btnDecision = document.getElementById('btn-decision-mode');
    const resultsContainer = document.getElementById('nexus-results-container');
    
    // Inputs de configuración (IDs del HTML)
    const inputCapital = document.getElementById('input-capital');
    const inputAportacion = document.getElementById('input-aportacion');
    // Chips para selección múltiple
    const chips = document.querySelectorAll('.select-chip');

    if (!btnDecision || !resultsContainer) return;

    // --- 1. LÓGICA DE INTERACCIÓN DE CHIPS (Selección Múltiple) ---
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            const value = chip.dataset.value;

            if (value === "Equilibrado") {
                // Si elige Equilibrado, limpiamos el resto
                chips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
            } else {
                // Si elige otro, quitamos el "Equilibrado" y toggleamos el actual
                const equilibradoChip = document.querySelector('.select-chip[data-value="Equilibrado"]');
                if (equilibradoChip) equilibradoChip.classList.remove('active');
                
                chip.classList.toggle('active');
            }

            // Si nada queda seleccionado, regresamos a Equilibrado por defecto
            const activeCount = document.querySelectorAll('.select-chip.active').length;
            if (activeCount === 0) {
                const eq = document.querySelector('.select-chip[data-value="Equilibrado"]');
                if (eq) eq.classList.add('active');
            }
        });
    });

    // --- 2. LÓGICA DE PERSISTENCIA (Cargar caché al entrar) ---
    const cachedPlan = localStorage.getItem('nexus_last_plan');
    if (cachedPlan) {
        renderNexusCards(JSON.parse(cachedPlan), resultsContainer);
    }

    btnDecision.addEventListener('click', async () => {
        // Obtenemos los valores de los chips activos como una lista separada por comas
        const enfoquesSeleccionados = Array.from(document.querySelectorAll('.select-chip.active'))
                                           .map(c => c.dataset.value)
                                           .join(", ");

        // Preparar datos para el Mentor Senior
        const params = {
            capital_extra: parseFloat(inputCapital.value) || 0,
            aportacion: parseFloat(inputAportacion.value) || 0,
            preferencia: enfoquesSeleccionados
        };

        // Estado de Carga (UX Premium)
        const originalText = btnDecision.innerHTML;
        btnDecision.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Consultando al Agente Senior...';
        btnDecision.disabled = true;
        resultsContainer.style.opacity = '0.5';

        try {
            const apiUrl = btnDecision.getAttribute('data-url');
            
            // Llamada a la API enviando los parámetros
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
                
                // Guardar en memoria local
                localStorage.setItem('nexus_last_plan', JSON.stringify(data));

                // Renderizado
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
 * Función encargada de dibujar las tarjetas (Sin cambios en clases/variables)
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