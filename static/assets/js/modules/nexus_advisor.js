export function initNexusAdvisor() {
    const btnDecision = document.getElementById('btn-decision-mode');
    const resultsContainer = document.getElementById('nexus-results-container');
    
    // Inputs de configuración
    const inputCapital = document.getElementById('input-capital');
    const inputAportacion = document.getElementById('input-aportacion');
    const chips = document.querySelectorAll('.select-chip');

    if (!btnDecision || !resultsContainer) return;

    // --- 1. LÓGICA DE INTERACCIÓN DE CHIPS ---
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            const value = chip.dataset.value;
            if (value === "Equilibrado") {
                chips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
            } else {
                const equilibradoChip = document.querySelector('.select-chip[data-value="Equilibrado"]');
                if (equilibradoChip) equilibradoChip.classList.remove('active');
                chip.classList.toggle('active');
            }
            if (document.querySelectorAll('.select-chip.active').length === 0) {
                const eq = document.querySelector('.select-chip[data-value="Equilibrado"]');
                if (eq) eq.classList.add('active');
            }
        });
    });

    // --- 2. LÓGICA DE PERSISTENCIA ---
    const cachedPlan = localStorage.getItem('nexus_last_plan');
    if (cachedPlan) {
        renderNexusCards(JSON.parse(cachedPlan), resultsContainer);
    }

    btnDecision.addEventListener('click', async () => {
        const enfoques = Array.from(document.querySelectorAll('.select-chip.active'))
                             .map(c => c.dataset.value)
                             .join(", ");

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
            const apiUrl = btnDecision.getAttribute('data-url');
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(params)
            });

            if (!response.ok) throw new Error('Error de conexión');

            const result = await response.json();

            if (result.status === 'success') {
                const data = result.data;
                localStorage.setItem('nexus_last_plan', JSON.stringify(data));
                
                // --- CONEXIÓN CON LAS FUNCIONES NUEVAS ---
                renderNexusCards(data, resultsContainer);
                
                // Si el servidor mandó datos históricos, pintamos la gráfica
                if (result.time_machine) {
                    renderTimeMachine(result.time_machine);
                }

                resultsContainer.style.opacity = '1';
            } else {
                throw new Error(result.message);
            }

        } catch (error) {
            console.error('Error NEXUS:', error);
            resultsContainer.innerHTML = `
                <div class="nexus-error-alert">
                    <i class="fas fa-times-circle"></i> Error con el Agente: ${error.message}.
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
 * Renderizado con Checklist de Agenda Mensual
 */
function renderNexusCards(data, container) {
    const nivelRiesgo = (data.nivel_riesgo || "").toLowerCase();
    let riskClass = 'risk-low';
    if (nivelRiesgo.includes('alto') || nivelRiesgo.includes('crítico')) riskClass = 'risk-high';
    else if (nivelRiesgo.includes('medio')) riskClass = 'risk-medium';

    // Generar el HTML de la Agenda Mensual (Checklist)
    let agendaHtml = '';
    if (data.hoja_ruta_mensual && Array.isArray(data.hoja_ruta_mensual)) {
        agendaHtml = `<div class="hoja-ruta-container">
            <h4 style="margin-bottom: 1rem; color: #1a2a6c;">📋 Tu Agenda de Aportaciones:</h4>`;
        data.hoja_ruta_mensual.forEach(item => {
            agendaHtml += `
                <div class="ruta-item">
                    <span class="mes-badge">${item.mes}</span>
                    <span class="tarea-text">${item.tarea}</span>
                </div>`;
        });
        agendaHtml += `</div>`;
    }

    const htmlTarjetas = `
        <div class="nexus-card ${riskClass}">
            <div class="nexus-card-header">
                <span class="nexus-icon-wrapper"><i class="fas fa-exclamation-triangle"></i></span>
                <h3 class="nexus-card-title">Diagnóstico de Riesgo</h3>
            </div>
            <div class="nexus-card-body markdown-content">
                ${marked.parse(data.riesgo_detectado)}
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
            <div class="nexus-card-body markdown-content">
                <p class="mission-action">${data.accion_inmediata}</p>
                <div style="margin-top: 1.5rem">
                    ${marked.parse(data.justificacion)}
                </div>
                ${agendaHtml} </div>
            <div class="nexus-badge-wrapper">
                <span class="nexus-badge">Objetivo: ${data.porcentaje_objetivo}</span>
            </div>
        </div>

        <div class="nexus-card card-fiscal">
            <div class="nexus-card-header">
                <span class="nexus-icon-wrapper"><i class="fas fa-landmark"></i></span>
                <h3 class="nexus-card-title">Hack Fiscal México</h3>
            </div>
            <div class="nexus-card-body markdown-content">
                ${marked.parse(data.hack_fiscal)}
            </div>
            <div class="nexus-badge-wrapper">
                <span class="nexus-badge" style="background: rgba(124, 58, 237, 0.1); color: #a78bfa; text-transform: none;">LISR / SAT</span>
            </div>
        </div>
    `;

    container.innerHTML = htmlTarjetas;
    container.classList.add('is-visible');
}

// --- MÁQUINA DEL TIEMPO ---
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
                tension: 0.4,
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { ticks: { callback: (v) => '$' + v.toLocaleString() } }
            }
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