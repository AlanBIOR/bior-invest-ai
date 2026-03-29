// Exportamos la función para que tu main.js la pueda importar y ejecutar
export function initNexusAdvisor() {
    const btnDecision = document.getElementById('btn-decision-mode');
    const resultsContainer = document.getElementById('nexus-results-container');

    // Si no estamos en la página del Action Hub, detenemos la ejecución aquí
    if (!btnDecision || !resultsContainer) return;

    btnDecision.addEventListener('click', async () => {
        // 1. Estado de Carga (UX)
        const originalText = btnDecision.innerHTML;
        btnDecision.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando tu portafolio con NEXUS AI...';
        btnDecision.disabled = true;
        btnDecision.style.opacity = '0.7';
        
        resultsContainer.innerHTML = '';
        resultsContainer.style.display = 'none';

        try {
            // 2. Llamada a la API
            const response = await fetch('/api/v1/modo-decision/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            const result = await response.json();

            if (result.status === 'success') {
                const data = result.data;
                
                // 3. Renderizado de Tarjetas Dinámicas
                const colorRiesgo = data.nivel_riesgo.toLowerCase().includes('alto') ? '#ef4444' : 
                                   (data.nivel_riesgo.toLowerCase().includes('medio') ? '#f59e0b' : '#10b981');

                const htmlTarjetas = `
                    <div style="background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                            <span style="background: ${colorRiesgo}20; color: ${colorRiesgo}; padding: 8px; border-radius: 8px;"><i class="fas fa-exclamation-triangle"></i></span>
                            <h3 style="margin: 0; font-size: 1.1rem; color: #c9d1d9;">Diagnóstico de Riesgo</h3>
                        </div>
                        <p style="color: #8b949e; font-size: 0.95rem; margin-bottom: 10px;">${data.riesgo_detectado}</p>
                        <span style="display: inline-block; background: ${colorRiesgo}; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">Nivel: ${data.nivel_riesgo}</span>
                    </div>

                    <div style="background: #1c2128; border: 1px solid #238636; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); position: relative; overflow: hidden;">
                        <div style="position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: #238636;"></div>
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                            <span style="background: #23863620; color: #3fb950; padding: 8px; border-radius: 8px;"><i class="fas fa-bolt"></i></span>
                            <h3 style="margin: 0; font-size: 1.1rem; color: #c9d1d9;">Tu Misión de Hoy</h3>
                        </div>
                        <p style="color: #ffffff; font-size: 1.05rem; font-weight: bold; margin-bottom: 10px;">${data.accion_inmediata}</p>
                        <p style="color: #8b949e; font-size: 0.9rem; margin-bottom: 15px;"><em>" ${data.justificacion} "</em></p>
                        <span style="display: inline-block; background: #3fb950; color: #000; padding: 2px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">Objetivo Mínimo: ${data.porcentaje_objetivo}</span>
                    </div>

                    <div style="background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                            <span style="background: #8957e520; color: #a371f7; padding: 8px; border-radius: 8px;"><i class="fas fa-file-invoice-dollar"></i></span>
                            <h3 style="margin: 0; font-size: 1.1rem; color: #c9d1d9;">Hack Fiscal México</h3>
                        </div>
                        <p style="color: #8b949e; font-size: 0.95rem;">${data.hack_fiscal}</p>
                    </div>
                `;

                resultsContainer.innerHTML = htmlTarjetas;
                resultsContainer.style.display = 'grid';

            } else {
                throw new Error(result.message || 'Error desconocido en el servidor');
            }

        } catch (error) {
            console.error('Error procesando Modo Decisión:', error);
            resultsContainer.innerHTML = `
                <div style="grid-column: 1 / -1; background: #ef444420; border: 1px solid #ef4444; color: #ff7b72; padding: 15px; border-radius: 8px; text-align: center;">
                    <i class="fas fa-times-circle"></i> Ocurrió un error al contactar con NEXUS. Intenta nuevamente.
                </div>
            `;
            resultsContainer.style.display = 'grid';
        } finally {
            btnDecision.innerHTML = originalText;
            btnDecision.disabled = false;
            btnDecision.style.opacity = '1';
        }
    });
}

// Helper Function privada
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