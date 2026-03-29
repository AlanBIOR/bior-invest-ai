export function initNexusAdvisor() {
    const btnDecision = document.getElementById('btn-decision-mode');
    const resultsContainer = document.getElementById('nexus-results-container');
    const inputCapital = document.getElementById('input-capital');
    const inputAportacion = document.getElementById('input-aportacion');
    const chips = document.querySelectorAll('.select-chip');

    if (!btnDecision || !resultsContainer) return;

    // --- 1. LÓGICA DE INTERACCIÓN DE CHIPS (Mantenida) ---
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            const value = chip.dataset.value;
            if (value === "Equilibrado") {
                chips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
            } else {
                const eq = document.querySelector('.select-chip[data-value="Equilibrado"]');
                if (eq) eq.classList.remove('active');
                chip.classList.toggle('active');
            }
            if (document.querySelectorAll('.select-chip.active').length === 0) {
                document.querySelector('.select-chip[data-value="Equilibrado"]')?.classList.add('active');
            }
        });
    });

    // --- 2. NUEVA LÓGICA DE PERSISTENCIA TOTAL ---
    const cachedPlan = localStorage.getItem('nexus_last_plan');
    const cachedGraph = localStorage.getItem('nexus_last_graph');

    if (cachedPlan) {
        renderNexusCards(JSON.parse(cachedPlan), resultsContainer);
    }
    if (cachedGraph) {
        setTimeout(() => renderTimeMachine(JSON.parse(cachedGraph)), 100);
    }

    btnDecision.addEventListener('click', async () => {
        const enfoques = Array.from(document.querySelectorAll('.select-chip.active'))
                             .map(c => c.dataset.value).join(", ");

        const params = {
            capital_extra: parseFloat(inputCapital.value) || 0,
            aportacion: parseFloat(inputAportacion.value) || 0,
            preferencia: enfoques
        };

        const originalText = btnDecision.innerHTML;
        btnDecision.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Consultando al Agente Senior...';
        btnDecision.disabled = true;
        resultsContainer.style.opacity = '0.5';

        try {
            const response = await fetch(btnDecision.getAttribute('data-url'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify(params)
            });

            // --- VALIDACIÓN DE RESPUESTA (Evita el error del token '<') ---
            const contentType = response.headers.get("content-type");
            
            if (!response.ok || !contentType || !contentType.includes("application/json")) {
                throw new Error('El servidor tardó demasiado o respondió con un formato inválido (504/HTML).');
            }

            const result = await response.json();

            if (result.status === 'success') {
                localStorage.setItem('nexus_last_plan', JSON.stringify(result.data));
                localStorage.setItem('nexus_last_graph', JSON.stringify(result.time_machine));
                
                renderNexusCards(result.data, resultsContainer);
                
                if (result.time_machine) {
                    renderTimeMachine(result.time_machine);
                }
                resultsContainer.style.opacity = '1';
            } else {
                throw new Error(result.message || 'Error desconocido en el motor.');
            }

        } catch (error) {
            console.error('Error:', error);
            // Mostramos el error visualmente al usuario
            resultsContainer.innerHTML = `
                <div class="nexus-card risk-high">
                    <div class="nexus-card-header"><i class="fas fa-plug"></i><h3 class="nexus-card-title">Error de Conexión</h3></div>
                    <div class="nexus-card-body">
                        NEXUS no pudo responder a tiempo. Esto suele pasar cuando el análisis de rebalanceo es muy complejo o el servidor está saturado. 
                        <br><br><strong>Detalle:</strong> ${error.message}
                    </div>
                </div>
            `;
            resultsContainer.style.opacity = '1';
        } finally {
            btnDecision.innerHTML = originalText;
            btnDecision.disabled = false;
        }
    });
}

// --- FUNCIONES DE RENDERIZADO (Mantenidas íntegras) ---

function renderNexusCards(data, container) {
    const nivelRiesgo = (data.nivel_riesgo || "").toLowerCase();
    let riskClass = 'risk-low';
    if (nivelRiesgo.includes('alto') || nivelRiesgo.includes('crítico')) riskClass = 'risk-high';
    else if (nivelRiesgo.includes('medio')) riskClass = 'risk-medium';

    let agendaHtml = '';
    if (data.hoja_ruta_mensual) {
        agendaHtml = `<div class="hoja-ruta-container"><h4 style="margin:1rem 0; color:#1a2a6c;">📋 Hoja de Ruta Mensual:</h4>`;
        data.hoja_ruta_mensual.forEach(item => {
            agendaHtml += `<div class="ruta-item"><span class="mes-badge">${item.mes}</span><span class="tarea-text">${item.tarea}</span></div>`;
        });
        agendaHtml += `</div>`;
    }

    container.innerHTML = `
        <div class="nexus-card ${riskClass}">
            <div class="nexus-card-header"><i class="fas fa-exclamation-triangle"></i><h3 class="nexus-card-title">Diagnóstico de Riesgo</h3></div>
            <div class="nexus-card-body">${marked.parse(data.riesgo_detectado)}</div>
        </div>
        <div class="nexus-card card-mission">
            <div class="nexus-card-header"><i class="fas fa-bullseye"></i><h3 class="nexus-card-title">Tu Misión de Hoy</h3></div>
            <div class="nexus-card-body">
                <p class="mission-action">${data.accion_inmediata}</p>
                <div style="margin-top:1.5rem">${marked.parse(data.justificacion)}</div>
                ${agendaHtml}
            </div>
        </div>
        <div class="nexus-card card-fiscal">
            <div class="nexus-card-header"><i class="fas fa-landmark"></i><h3 class="nexus-card-title">Hack Fiscal México</h3></div>
            <div class="nexus-card-body">${marked.parse(data.hack_fiscal)}</div>
        </div>
    `;
    container.classList.add('is-visible');
}

let timeChart = null;
function renderTimeMachine(datos) {
    const canvas = document.getElementById('timeMachineChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (timeChart) timeChart.destroy();

    timeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: datos.map(d => d.mes),
            datasets: [{
                label: 'Crecimiento Simulado',
                data: datos.map(d => d.valor),
                borderColor: '#1a2a6c',
                backgroundColor: 'rgba(26, 42, 108, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { ticks: { callback: (v) => '$' + v.toLocaleString() } } }
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