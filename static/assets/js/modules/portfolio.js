/**
 * portfolio.js - Módulo de gestión de activos reales para BIOR Invest
 * Maneja: Gráficas, Búsqueda API, Paginación y Eliminación.
 */

/**
 * 1. INICIALIZACIÓN DE GRÁFICA DE DONA
 */
export function initPortfolioChart() {
    const ctx = document.getElementById('portfolioChart');
    const dataScript = document.getElementById('portfolio-data-json');
    
    if (!ctx || !dataScript) return;

    // Paleta de colores sincronizada con Sass
    const categoryColors = {
        'Efectivo': '#00b894',
        'Renta Variable': '#1a2a6c',
        'Renta Fija': '#64748b',
        'Inversiones Alternativas': '#3498db',
        'Inmuebles': '#fdbb2d',
        'Private Equity': '#8e44ad'
    };

    let labels = [];
    let values = [];

    try {
        const config = JSON.parse(dataScript.textContent);
        labels = config.labels || [];
        values = config.values || [];
    } catch (e) {
        console.error("Error al parsear datos de la gráfica:", e);
        return;
    }

    const total = values.reduce((a, b) => a + (parseFloat(b) || 0), 0);
    const existingChart = Chart.getChart(ctx);
    if (existingChart) existingChart.destroy();

    const backgroundColors = labels.map(label => categoryColors[label] || '#cccccc');

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: backgroundColors,
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: { position: 'bottom', labels: { padding: 20, usePointStyle: true } },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const val = context.raw;
                            const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                            return `${context.label}: $${val.toLocaleString()} (${pct}%)`;
                        }
                    }
                }
            }
        },
        plugins: [{
            id: 'centerText',
            afterDraw: (chart) => {
                const { width, height, ctx } = chart;
                ctx.save();
                ctx.font = "bold 1.1em 'Roboto', sans-serif";
                ctx.textBaseline = "middle";
                ctx.textAlign = "center";
                ctx.fillStyle = "#1a2a6c";
                const text = "Total: $" + total.toLocaleString('es-MX', { minimumFractionDigits: 2 });
                ctx.fillText(text, width / 2, height / 2);
                ctx.restore();
            }
        }]
    });
}

/**
 * 2. PAGINACIÓN RESPONSIVA
 */
export function initTablePagination() {
    const tableBody = document.querySelector('.portfolio-table tbody');
    if (!tableBody) return;

    const rows = Array.from(tableBody.querySelectorAll('tr'));
    if (rows.length === 0 || rows[0].classList.contains('empty-row')) return;

    const renderPagination = () => {
        const isMobile = window.innerWidth <= 768;
        const rowsPerPage = isMobile ? 5 : 10;
        let currentPage = 1;
        const totalPages = Math.ceil(rows.length / rowsPerPage);

        const showPage = (page) => {
            const start = (page - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            rows.forEach((row, i) => row.style.display = (i >= start && i < end) ? '' : 'none');
        };

        const oldPagination = document.querySelector('.table-pagination');
        if (oldPagination) oldPagination.remove();

        if (totalPages > 1) {
            const container = document.createElement('div');
            container.className = 'table-pagination';
            container.innerHTML = `
                <button id="prevP" class="btn-page">&laquo;</button>
                <span id="pageI">Pág. ${currentPage}/${totalPages}</span>
                <button id="nextP" class="btn-page">&raquo;</button>
            `;
            tableBody.closest('.card').appendChild(container);

            document.getElementById('prevP').onclick = () => { if(currentPage > 1) { currentPage--; update(); } };
            document.getElementById('nextP').onclick = () => { if(currentPage < totalPages) { currentPage++; update(); } };
        }

        const update = () => {
            showPage(currentPage);
            const info = document.getElementById('pageI');
            if (info) info.textContent = `Pág. ${currentPage}/${totalPages}`;
        };
        update();
    };

    renderPagination();
    window.addEventListener('resize', renderPagination);
}

/**
 * 3. NOTIFICACIONES (Solución al error de la línea 75)
 */
export function initNotifications() {
    // Django ya maneja mensajes en el HTML, pero esto asegura compatibilidad con main.js
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('success') && typeof Swal !== 'undefined') {
        const type = urlParams.get('success');
        Swal.fire({
            icon: 'success',
            title: type === 'added' ? '¡Activo Registrado!' : '¡Activo Eliminado!',
            toast: true,
            position: 'top-end',
            timer: 3000,
            showConfirmButton: false,
            timerProgressBar: true
        });
    }
}

/**
 * 4. CONFIRMACIÓN DE ELIMINACIÓN (Ruta Django)
 */
export function confirmDelete(id, name) {
    if (typeof Swal === 'undefined') {
        if (confirm(`¿Borrar ${name}?`)) window.location.href = `/eliminar-activo/${id}/`;
        return;
    }

    Swal.fire({
        title: '¿Eliminar activo?',
        text: `¿Estás seguro de borrar "${name}"?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        confirmButtonText: 'Sí, borrar',
        cancelButtonText: 'Cancelar',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = `/eliminar-activo/${id}/`;
        }
    });
}

/**
 * 5. CONTROL DE CAMPOS DINÁMICOS (Blindado contra nulls)
 */
export function toggleFields() {
    const categorySelect = document.getElementById('category_id');
    const dynamicFields = document.getElementById('dynamic-fields');
    if (!categorySelect || !dynamicFields) return;

    const categoryId = categorySelect.value;
    const assetSearch = document.getElementById('asset_search');
    const assetName = assetSearch ? assetSearch.value.toLowerCase() : '';

    dynamicFields.classList.remove('hidden');

    // Control de Cetes y Rendimientos
    const yieldGroup = document.getElementById('yield-group');
    const cetesOptions = document.getElementById('cetes-options');

    if (yieldGroup) {
        if (categoryId === "5" || categoryId === "6") yieldGroup.classList.remove('hidden');
        else yieldGroup.classList.add('hidden');
    }

    if (cetesOptions) {
        if (assetName.includes('cetes') || categoryId === "6") cetesOptions.classList.remove('hidden');
        else cetesOptions.classList.add('hidden');
    }
}

/**
 * 6. ACTUALIZACIÓN DE TASAS CETES (Preparado para Django API)
 */
export async function updateCetesSeries() {
    const series = document.getElementById('cetes_plazo')?.value;
    const yieldInput = document.getElementById('annual_yield');
    if (!series || !yieldInput) return;

    yieldInput.placeholder = "Obteniendo tasa...";
    
    try {
        // Nota: Deberás crear esta ruta en Django después
        const response = await fetch(`/api/get-cetes-rate/?series=${series}`);
        const data = await response.json();
        if (data.rate) {
            yieldInput.value = data.rate;
            yieldInput.dispatchEvent(new Event('input'));
        }
    } catch (e) {
        yieldInput.placeholder = "No disponible";
    }
}

/**
 * 7. BUSCADOR HÍBRIDO (Blindado contra nulls)
 */
let searchTimeout = null;
export async function handleSearch(query) {
    const resultsDiv = document.getElementById('api-results');
    const assetInput = document.getElementById('asset_search');
    if (!resultsDiv || !assetInput) return;

    const lowerQuery = query.toLowerCase().trim();
    const localMapping = {
        'nu': { name: 'Nu México', cat: '5', yield: '14.25', platform: 'Nu' },
        'cetes': { name: 'CETES Directo', cat: '6', yield: '11.00', platform: 'CETES' },
        'efectivo': { name: 'Efectivo', cat: '5', yield: '0', platform: 'Billetera' }
    };

    if (localMapping[lowerQuery]) {
        assetInput.value = localMapping[lowerQuery].name;
        const catSelect = document.getElementById('category_id');
        if (catSelect) catSelect.value = localMapping[lowerQuery].cat;
        
        const yieldIn = document.getElementById('annual_yield');
        if (yieldIn) yieldIn.value = localMapping[lowerQuery].yield;

        const platIn = document.getElementById('platform');
        if (platIn) platIn.value = localMapping[lowerQuery].platform;

        resultsDiv.style.display = 'none';
        toggleFields();
        return;
    }

    if (query.length < 3) { resultsDiv.style.display = 'none'; return; }

    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
        try {
            const response = await fetch(`https://api.coingecko.com/api/v3/search?query=${query}`);
            const data = await response.json();
            
            resultsDiv.innerHTML = '';
            resultsDiv.style.display = 'block';

            data.coins.slice(0, 5).forEach(coin => {
                const div = document.createElement('div');
                div.className = 'suggestion-item';
                div.innerHTML = `<img src="${coin.thumb}" width="20"> <span>${coin.name}</span>`;
                div.onclick = () => {
                    assetInput.value = coin.name;
                    const apiIn = document.getElementById('api_id_hidden');
                    if (apiIn) apiIn.value = coin.id;
                    const catSelect = document.getElementById('category_id');
                    if (catSelect) catSelect.value = "4"; 
                    resultsDiv.style.display = 'none';
                    toggleFields();
                };
                resultsDiv.appendChild(div);
            });
        } catch (e) { console.error("Error API:", e); }
    }, 400);
}