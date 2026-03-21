/**
 * Formatea valores numéricos a moneda MXN
 */
const formatMXN = (valor) => {
    return valor.toLocaleString('es-MX', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
};

/**
 * Obtiene el CSRF Token para peticiones POST de Django
 */
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

// --- SECCIÓN: PERSISTENCIA (COOKIES Y DJANGO) ---

function setInvCookie(name, value) {
    const d = new Date();
    d.setTime(d.getTime() + (30 * 24 * 60 * 60 * 1000));
    let expires = "expires=" + d.toUTCString();
    document.cookie = `${name}=${value};${expires};path=/;SameSite=Lax`;
}

export async function guardarEnBaseDeDatos(monto, aportacion = 0) {
    const csrftoken = getCookie('csrftoken');
    
    try {
        const response = await fetch('/guardar-progreso/', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken 
            },
            body: JSON.stringify({ 
                capital: monto, 
                aportacion: aportacion 
            })
        });
        const data = await response.json();
        if (data.status === 'ok') {
            console.log('✅ Base de Datos Django actualizada');
        }
    } catch (error) {
        console.error('❌ Error al sincronizar con Django:', error);
    }
}

// --- SECCIÓN: LÓGICA DE CÁLCULO Y UI ---

export function recalcularCards(monto) {
    const displays = document.querySelectorAll('.monto-calculado');
    displays.forEach(span => {
        const perc = parseFloat(span.dataset.porcentaje) / 100;
        span.innerText = formatMXN(monto * perc);
    });
}

export function aplicarSugerencias(monto) {
    // Ajustado a los nombres exactos de tu DB/Seed
    const cardInmuebles = document.querySelector('[data-category="Inmuebles"]'); 
    const cardPE = document.querySelector('[data-category="Private Equity"]');

    if (cardInmuebles) {
        const small = cardInmuebles.querySelector('small');
        if (monto < 1000000) {
            small.innerHTML = `<strong>Sugerencia:</strong> Invierte en <strong>Fibras</strong>. Más accesible que propiedad física.`;
            cardInmuebles.classList.add('card--warning');
        } else {
            small.textContent = "Residencial, Alquiler a largo plazo y FIBRAS";
            cardInmuebles.classList.remove('card--warning');
        }
    }

    if (cardPE) {
        const small = cardPE.querySelector('small');
        if (monto < 200000) {
            small.innerHTML = `<strong>Aviso:</strong> Ticket mínimo alto. Considera <strong>crowdfunding</strong>.`;
        } else {
            small.textContent = "Empresas privadas, Search Funds y Venture Capital";
        }
    }
}

export function proyectarCrecimiento(capitalInicial, aportacionMensual) {
    const rendimientos = {
        'Renta Variable': 0.10,
        'Inmuebles': 0.08,
        'Private Equity': 0.12,
        'Inversiones Alternativas': 0.15,
        'Efectivo': 0.03,
        'Renta Fija': 0.11
    };

    let rendimientoPonderadoAnual = 0;
    const cards = document.querySelectorAll('.monto-calculado');
    
    cards.forEach(span => {
        const cardParent = span.closest('.investment-card');
        const nombreCat = cardParent ? cardParent.dataset.category : '';
        const porcentaje = parseFloat(span.dataset.porcentaje) / 100;
        const tasa = rendimientos[nombreCat] || 0.08;
        rendimientoPonderadoAnual += (porcentaje * tasa);
    });

    const TASA_MENSUAL = rendimientoPonderadoAnual / 12;
    const periodos = [1, 2, 3, 5, 10, 20]; 
    const contenedor = document.getElementById('proyeccion-resultados');

    if (!contenedor) return;

    let html = '';
    periodos.forEach(anios => {
        const n = anios * 12;
        const vfCapital = capitalInicial * Math.pow(1 + TASA_MENSUAL, n);
        let vfAportaciones = TASA_MENSUAL > 0 
            ? aportacionMensual * ((Math.pow(1 + TASA_MENSUAL, n) - 1) / TASA_MENSUAL)
            : aportacionMensual * n;

        html += `
            <div class="proyeccion-item">
                <span class="proyeccion-label">${anios} ${anios === 1 ? 'año' : 'años'}</span>
                <span class="proyeccion-value">$${formatMXN(vfCapital + vfAportaciones)}</span>
            </div>
        `;
    });
    contenedor.innerHTML = html;
}

// --- INICIALIZADOR ÚNICO ---

export function initCalculadora() {
    const inputCapital = document.getElementById('montoTotal');
    const inputAportacion = document.getElementById('montoAportacion');
    
    if (!inputCapital || !inputAportacion) return;

    const isLoggedIn = window.BIOR_CONFIG?.isLoggedIn ?? false;

    const manejarCambio = () => {
        const cap = parseFloat(inputCapital.value) || 0;
        const apor = parseFloat(inputAportacion.value) || 0;

        // 1. Cálculos Visuales
        recalcularCards(cap);
        aplicarSugerencias(cap);
        proyectarCrecimiento(cap, apor);

        // 2. Persistencia
        if (isLoggedIn) {
            guardarEnBaseDeDatos(cap, apor);
        } else {
            setInvCookie('bior_inv_capital', cap);
            setInvCookie('bior_inv_aportacion', apor);
        }
    };

    // Usamos 'input' para actualización inmediata y profesional
    inputCapital.addEventListener('input', manejarCambio);
    inputAportacion.addEventListener('input', manejarCambio);

    // Ejecución inicial
    manejarCambio();
}