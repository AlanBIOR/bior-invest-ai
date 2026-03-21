// static/assets/js/main.js
import * as Calc from './modules/calculadora.js';
import { initGrafico } from './modules/grafico.js';
import { generarImagen } from './modules/reporte.js';
import * as Portfolio from './modules/portfolio.js';
import { initToasts, initAlertsConf } from './modules/alerts.js';
import { initPrivacyMode } from './modules/privacy.js';

// --- FUNCIONES DE PERSISTENCIA PARA DJANGO ---
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

const sincronizarProgreso = (cap, apor) => {
    const isLogged = window.BIOR_CONFIG?.isLoggedIn || false;
    if (isLogged) {
        fetch('/guardar-progreso/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ capital: cap, aportacion: apor })
        }).catch(err => console.error("Error de sincronización:", err));
    } else {
        localStorage.setItem('bior_capital', cap);
        localStorage.setItem('bior_aportacion', apor);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    
    // --- 0. INICIALIZACIÓN PRIORITARIA ---
    initToasts();
    initAlertsConf();
    if (typeof initPrivacyMode === 'function') initPrivacyMode();

    // --- 1. EXPOSICIÓN GLOBAL (Para botones en HTML) ---
    window.handleSearch = Portfolio.handleSearch;
    window.toggleFields = Portfolio.toggleFields; 
    window.updateCetesSeries = Portfolio.updateCetesSeries;
    window.confirmDelete = Portfolio.confirmDelete;

    // --- 2. LÓGICA DEL MENÚ ---
    const header = document.querySelector('.main-header');
    const menuToggle = document.querySelector('.menu-toggle');
    const mainNav = document.querySelector('.main-nav');
    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', () => {
            mainNav.classList.toggle('open');
            header?.classList.toggle('menu-open');
        });
    }

    // --- 3. INICIALIZACIÓN DE GRÁFICAS ---
    if (document.getElementById('portfolioChart')) {
        Portfolio.initPortfolioChart();
    }

    const tableBody = document.querySelector('.portfolio-table tbody');
    if (tableBody && typeof Portfolio.initTablePagination === 'function') {
        Portfolio.initTablePagination();
    }

    // --- 4. LÓGICA DE PORTAFOLIO ---
    const assetSearch = document.getElementById('asset_search');
    if (assetSearch) {
        // CORRECCIÓN: Solo llamamos si existe para evitar el error de la línea 75
        if (typeof Portfolio.initNotifications === 'function') {
            Portfolio.initNotifications();
        }
        assetSearch.addEventListener('input', (e) => Portfolio.handleSearch(e.target.value));
        document.getElementById('category_id')?.addEventListener('change', Portfolio.toggleFields);
        document.getElementById('cetes_plazo')?.addEventListener('change', Portfolio.updateCetesSeries);
    }

    // --- 5. LÓGICA DEL CARRUSEL ---
    const slider = document.getElementById('suggestionsSlider');
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    if (slider && nextBtn && prevBtn) {
        const scrollAmount = 300;
        nextBtn.onclick = () => {
            if (slider.scrollLeft + slider.clientWidth >= slider.scrollWidth - 5) slider.scrollTo({ left: 0, behavior: 'smooth' });
            else slider.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        };
        prevBtn.onclick = () => {
            if (slider.scrollLeft <= 5) slider.scrollTo({ left: slider.scrollWidth, behavior: 'smooth' });
            else slider.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        };
    }

    // --- 6. CALCULADORA & PERSISTENCIA ---
    const dataElement = document.getElementById('inversiones-data');
    const inputMonto = document.getElementById('montoTotal');

    if (dataElement && inputMonto) {
        try {
            const config = JSON.parse(dataElement.textContent);
            const inputAportacion = document.getElementById('montoAportacion');
            const btnPDF = document.getElementById('btnDescargarPDF');

            const refrescarUI = () => {
                const cap = parseFloat(inputMonto.value) || 0;
                const apor = parseFloat(inputAportacion?.value) || 0;
                Calc.recalcularCards(cap); 
                Calc.aplicarSugerencias(cap);
                Calc.proyectarCrecimiento(cap, apor);
                sincronizarProgreso(cap, apor); // <--- Actualizado para Django
                
                // Actualizar gráfica de estrategia
                const labels = config.map(c => c.name);
                const values = config.map(c => (cap * (c.target_percentage / 100)).toFixed(2));
                initGrafico(labels, values); 
            };

            inputMonto.addEventListener('input', refrescarUI);
            inputAportacion?.addEventListener('input', refrescarUI);
            
            // Si tenías initPersistence en Calc, lo llamamos aquí
            if (typeof Calc.initPersistence === 'function') Calc.initPersistence();

            btnPDF?.addEventListener('click', (e) => { e.preventDefault(); generarImagen(); });
            refrescarUI(); 
        } catch (err) {
            console.error("Error inicializando calculadora:", err);
        }
    }

    const portfolioCanvas = document.getElementById('portfolioChart');
    if (portfolioCanvas) {
        // Si la función en grafico.js o portfolio.js ya no usa fetch, esto cargará al instante
        Portfolio.initPortfolioChart(); 
    }

    // --- 7. EVENTOS GLOBALES ---
    document.addEventListener('click', (e) => {
        const resultsDiv = document.getElementById('api-results');
        const searchContainer = document.querySelector('.search-container');
        if (searchContainer && !searchContainer.contains(e.target) && resultsDiv) {
            resultsDiv.innerHTML = '';
            resultsDiv.style.display = 'none';
        }
    });
});