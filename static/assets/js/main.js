// assets/js/main.js
import * as Calc from './modules/calculadora.js';
import { initGrafico } from './modules/grafico.js';
import { generarImagen } from './modules/reporte.js';
import * as Portfolio from './modules/portfolio.js';
import { initToasts, initAlertsConf } from './modules/alerts.js';
import { initPrivacyMode } from './modules/privacy.js';

document.addEventListener('DOMContentLoaded', () => {
    
    // --- 0. INICIALIZACIÓN PRIORITARIA ---
    // Lo ponemos al principio para que las alertas funcionen siempre
    initToasts();
    initAlertsConf();
    initPrivacyMode();

    // --- 1. EXPOSICIÓN GLOBAL ---
    window.handleSearch = Portfolio.handleSearch;
    window.toggleFields = Portfolio.toggleFields; 
    window.updateCetesSeries = Portfolio.updateCetesSeries;
    window.confirmDelete = Portfolio.confirmDelete;

    // --- 2. LÓGICA DEL MENÚ RESPONSIVO ---
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

    // Verificación de existencia antes de ejecutar paginación
    const tableBody = document.querySelector('.portfolio-table tbody');
    if (tableBody && typeof Portfolio.initTablePagination === 'function') {
        Portfolio.initTablePagination();
    }

    // --- 4. LÓGICA ESPECÍFICA DE PORTAFOLIO.PHP ---
    const assetSearch = document.getElementById('asset_search');
    if (assetSearch) {
        Portfolio.initNotifications();
        assetSearch.addEventListener('input', (e) => Portfolio.handleSearch(e.target.value));
        
        const categorySelect = document.getElementById('category_id');
        categorySelect?.addEventListener('change', Portfolio.toggleFields);

        const cetesPlazo = document.getElementById('cetes_plazo');
        cetesPlazo?.addEventListener('change', Portfolio.updateCetesSeries);
    }

    // --- 5. LÓGICA DEL CARRUSEL INFINITO ---
    const slider = document.getElementById('suggestionsSlider');
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');

    if (slider && nextBtn && prevBtn) {
        const scrollAmount = 300;
        nextBtn.addEventListener('click', () => {
            if (slider.scrollLeft + slider.clientWidth >= slider.scrollWidth - 5) {
                slider.scrollTo({ left: 0, behavior: 'smooth' });
            } else {
                slider.scrollBy({ left: scrollAmount, behavior: 'smooth' });
            }
        });
        prevBtn.addEventListener('click', () => {
            if (slider.scrollLeft <= 5) {
                slider.scrollTo({ left: slider.scrollWidth, behavior: 'smooth' });
            } else {
                slider.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
            }
        });
    }

    // --- 6. LÓGICA DE LA CALCULADORA & PERSISTENCIA ---
    const dataElement = document.getElementById('inversiones-data');
    if (dataElement) {
        try {
            const config = JSON.parse(dataElement.textContent);
            const inputMonto = document.getElementById('montoTotal');
            const inputAportacion = document.getElementById('montoAportacion');
            const btnPDF = document.getElementById('btnDescargarPDF');

            initGrafico(config.labels, config.datasets);

            const refrescarUI = () => {
                const cap = parseFloat(inputMonto?.value) || 0;
                const apor = parseFloat(inputAportacion?.value) || 0;
                Calc.recalcularCards(cap); 
                Calc.aplicarSugerencias(cap);
                Calc.proyectarCrecimiento(cap, apor);
            };

            inputMonto?.addEventListener('input', refrescarUI);
            inputAportacion?.addEventListener('input', refrescarUI);

            Calc.initPersistence();

            btnPDF?.addEventListener('click', (e) => {
                e.preventDefault();
                generarImagen();
            });

            refrescarUI(); 
        } catch (err) {
            console.error("Error inicializando calculadora:", err);
        }
    }

    // --- 7. EVENTOS GLOBALES ---
    document.addEventListener('click', (event) => {
        const resultsDiv = document.getElementById('api-results');
        const searchContainer = document.querySelector('.search-container');
        if (searchContainer && !searchContainer.contains(event.target) && resultsDiv) {
            resultsDiv.innerHTML = '';
            resultsDiv.style.display = 'none';
        }
    });
});