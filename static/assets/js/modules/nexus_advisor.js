export function initNexusAdvisor() {
    const btnDecision = document.getElementById('btn-decision-mode');
    const resultsContainer = document.getElementById('nexus-results-container');

    if (!btnDecision || !resultsContainer) return;

    btnDecision.addEventListener('click', async () => {
        // 1. Estado de Carga (UX)
        const originalText = btnDecision.innerHTML;
        btnDecision.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando tu portafolio con NEXUS AI...';
        btnDecision.disabled = true;
        
        resultsContainer.innerHTML = '';
        resultsContainer.classList.remove('is-visible');

        try {
            // 2. Llamada a la API
            const apiUrl = btnDecision.getAttribute('data-url');
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            const result = await response.json();

            if (result.status === 'success') {
                const data = result.data;
                
                // 3. Lógica de Clases CSS para el Riesgo
                const nivelRiesgo = data.nivel_riesgo.toLowerCase();
                let riskClass = 'risk-low';
                if (nivelRiesgo.includes('alto')) riskClass = 'risk-high';
                else if (nivelRiesgo.includes('medio')) riskClass = 'risk-medium';

                // 4. Renderizado Limpio de Tarjetas Dinámicas
                const htmlTarjetas = `
                    <div class="nexus-card ${riskClass}">
                        <div class="nexus-card-header">
                            <span class="nexus-icon-wrapper"><i class="fas fa-exclamation-triangle"></i></span>
                            <h3 class="nexus-card-title">Diagnóstico de Riesgo</h3>
                        </div>
                        <p class="nexus-card-text">${data.riesgo_detectado}</p>
                        <span class="nexus-badge">Nivel: ${data.nivel_riesgo}</span>
                    </div>

                    <div class="nexus-card card-mission">
                        <div class="mission-border"></div>
                        <div class="nexus-card-header">
                            <span class="nexus-icon-wrapper"><i class="fas fa-bolt"></i></span>
                            <h3 class="nexus-card-title">Tu Misión de Hoy</h3>
                        </div>
                        <p class="nexus-card-text mission-action">${data.accion_inmediata}</p>
                        <p class="nexus-card-text mission-quote"><em>" ${data.justificacion} "</em></p>
                        <span class="nexus-badge">Objetivo Mínimo: ${data.porcentaje_objetivo}</span>
                    </div>

                    <div class="nexus-card card-fiscal">
                        <div class="nexus-card-header">
                            <span class="nexus-icon-wrapper"><i class="fas fa-file-invoice-dollar"></i></span>
                            <h3 class="nexus-card-title">Hack Fiscal México</h3>
                        </div>
                        <p class="nexus-card-text">${data.hack_fiscal}</p>
                    </div>
                `;

                resultsContainer.innerHTML = htmlTarjetas;
                resultsContainer.classList.add('is-visible');

            } else {
                throw new Error(result.message || 'Error desconocido en el servidor');
            }

        } catch (error) {
            console.error('Error procesando Modo Decisión:', error);
            resultsContainer.innerHTML = `
                <div class="nexus-error-alert">
                    <i class="fas fa-times-circle"></i> Ocurrió un error al contactar con NEXUS. Intenta nuevamente.
                </div>
            `;
            resultsContainer.classList.add('is-visible');
        } finally {
            btnDecision.innerHTML = originalText;
            btnDecision.disabled = false;
        }
    });
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