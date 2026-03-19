// assets/js/modules/calculadora.js

/**
 * Formatea valores numéricos a moneda MXN
 */
const formatMXN = (valor) => {
    return valor.toLocaleString('es-MX', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
};

// --- SECCIÓN: PERSISTENCIA (COOKIES Y BASE DE DATOS) ---

/**
 * Guarda una cookie en el navegador (para usuarios no logueados)
 */
function setInvCookie(name, value) {
    const d = new Date();
    d.setTime(d.getTime() + (30 * 24 * 60 * 60 * 1000)); // Expira en 30 días
    let expires = "expires=" + d.toUTCString();
    document.cookie = `${name}=${value};${expires};path=/;SameSite=Lax`;
}

/**
 * Envía el capital y aportación a MySQL vía AJAX (para usuarios logueados)
 */
export async function guardarEnBaseDeDatos(monto, aportacion = 0) {
    try {
        const response = await fetch('includes/update_capital.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                capital: monto, 
                aportacion: aportacion 
            })
        });
        const data = await response.json();
        if (data.status === 'success') {
            console.log('✅ Base de Datos actualizada correctamente');
        }
    } catch (error) {
        console.error('❌ Error de red al sincronizar con MySQL:', error);
    }
}

/**
 * Inicializa los escuchadores de eventos para guardar datos automáticamente
 */
export function initPersistence() {
    const inputCapital = document.getElementById('montoTotal');
    const inputAportacion = document.getElementById('montoAportacion');
    
    // Verificamos el estado de sesión definido en index.php
    const isLoggedIn = window.BIOR_CONFIG?.isLoggedIn ?? false;

    if (inputCapital && inputAportacion) {
        const manejarCambio = () => {
            const cap = parseFloat(inputCapital.value) || 0;
            const apor = parseFloat(inputAportacion.value) || 0;

            if (isLoggedIn) {
                // Caso Usuario Registrado
                guardarEnBaseDeDatos(cap, apor);
            } else {
                // Caso Invitado
                setInvCookie('bior_inv_capital', cap);
                setInvCookie('bior_inv_aportacion', apor);
                console.log('🍪 Datos de invitado guardados en cookies');
            }

            // Forzamos el recalcular por si acaso el evento change no disparó el input
            recalcularCards(cap);
            aplicarSugerencias(cap);
            proyectarCrecimiento(cap, apor);
        };

        inputCapital.addEventListener('change', manejarCambio);
        inputAportacion.addEventListener('change', manejarCambio);
    }
}

// --- SECCIÓN: LÓGICA DE CÁLCULO Y UI ---

export function initCalculadora() {
    const input = document.getElementById('montoTotal');
    if (!input) console.warn("No se encontró #montoTotal para inicializar");
}

/**
 * Actualiza los montos sugeridos en cada tarjeta de activo
 */
export function recalcularCards(monto) {
    const displays = document.querySelectorAll('.monto-calculado');
    displays.forEach(span => {
        const perc = parseFloat(span.dataset.porcentaje) / 100;
        span.innerText = formatMXN(monto * perc);
    });
}

/**
 * Cambia el texto y estilos de las tarjetas según el capital ingresado
 */
export function aplicarSugerencias(monto) {
    const cardInmuebles = document.querySelector('[data-category="INMUEBLES"]'); 
    const cardPrivateEquity = document.querySelector('[data-category="PRIVATE EQUITY"]');

    if (!cardInmuebles || !cardPrivateEquity) return;

    const smallInmuebles = cardInmuebles.querySelector('small');
    const smallPE = cardPrivateEquity.querySelector('small');

    // Lógica para Inmuebles
    if (monto < 1000000) {
        if (smallInmuebles) {
            smallInmuebles.innerHTML = `<strong>Sugerencia:</strong> Invierte en <strong>REITs (Fibras)</strong>. Es más accesible que una propiedad física.`;
        }
        cardInmuebles.classList.add('card--warning');
    } else {
        if (smallInmuebles) {
            smallInmuebles.textContent = "Residencia principal, Alquiler a largo plazo y Vacacional";
        }
        cardInmuebles.classList.remove('card--warning');
    }

    // Lógica para Private Equity
    if (monto < 200000) {
        if (smallPE) {
            smallPE.innerHTML = `<strong>Aviso:</strong> Ticket mínimo alto. Considera <strong>crowdfunding</strong>.`;
        }
    } else {
        if (smallPE) {
            smallPE.textContent = "Empresas privadas, Search Funds y Venture Capital";
        }
    }
}

/**
 * Calcula la proyección de interés compuesto ponderado
 */
export function proyectarCrecimiento(capitalInicial, aportacionMensual) {
    const rendimientos = {
        'RENTA VARIABLE': 0.10,
        'INMUEBLES': 0.08,
        'PRIVATE EQUITY': 0.12,
        'INVERSIONES ALTERNATIVAS': 0.15,
        'EFECTIVO': 0.03,
        'RENTA FIJA': 0.05
    };

    let rendimientoPonderadoAnual = 0;
    const cards = document.querySelectorAll('.monto-calculado');
    
    cards.forEach(span => {
        const cardParent = span.closest('.card');
        const nombreCat = cardParent ? cardParent.dataset.category : '';
        const porcentaje = parseFloat(span.dataset.porcentaje) / 100;
        const tasaRecurso = rendimientos[nombreCat] || 0.08;
        rendimientoPonderadoAnual += (porcentaje * tasaRecurso);
    });

    const TASA_MENSUAL = rendimientoPonderadoAnual / 12;
    const periodos = [1, 2, 3, 5, 10, 20]; 
    const proyeccionContenedor = document.getElementById('proyeccion-resultados');

    if (!proyeccionContenedor) return;

    let html = '';
    periodos.forEach(anios => {
        const n = anios * 12;
        const vfCapital = capitalInicial * Math.pow(1 + TASA_MENSUAL, n);
        
        // Fórmula de anualidades para las aportaciones mensuales
        let vfAportaciones = 0;
        if (TASA_MENSUAL > 0) {
            vfAportaciones = aportacionMensual * ((Math.pow(1 + TASA_MENSUAL, n) - 1) / TASA_MENSUAL);
        } else {
            vfAportaciones = aportacionMensual * n;
        }

        const total = vfCapital + vfAportaciones;

        html += `
            <div class="proyeccion-item">
                <span class="proyeccion-label">${anios} ${anios === 1 ? 'año' : 'años'}</span>
                <span class="proyeccion-value">$${formatMXN(total)}</span>
            </div>
        `;
    });
    proyeccionContenedor.innerHTML = html;
}