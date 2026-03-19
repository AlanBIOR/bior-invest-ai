/**
 * Inicializa la gráfica de dona con porcentajes y total central
 * Sincronizada con la paleta de colores de Sass
 */
export function initPortfolioChart() {
    const ctx = document.getElementById('portfolioChart');
    if (!ctx) return;

    // Diccionario de colores basado en tus variables de Sass
    const categoryColors = {
        'Efectivo': '#00b894',                // $success-green
        'Renta Variable': '#1a2a6c',          // $primary-color
        'Renta Fija': '#64748b',              // $text-muted
        'Inversiones Alternativas': '#3498db', // Azul claro
        'Inmuebles': '#fdbb2d',               // $accent-color
        'Private Equity': '#8e44ad'           // Morado
    };

    let labels = [];
    let values = [];
    try {
        const rawLabels = ctx.dataset.labels || '[]';
        const rawValues = ctx.dataset.values || '[]';

        if (rawLabels.includes('<br') || rawLabels.includes('<b>')) {
            throw new Error("PHP Error detectado en Data Attributes");
        }

        labels = JSON.parse(rawLabels);
        values = JSON.parse(rawValues);
    } catch (e) {
        console.error("Fallo al parsear datos de la gráfica:", e.message);
        return;
    }

    const total = values.reduce((a, b) => a + b, 0);
    const existingChart = Chart.getChart(ctx);
    if (existingChart) existingChart.destroy();

    // Mapeamos los colores dinámicamente según el label
    const backgroundColors = labels.map(label => categoryColors[label] || '#cccccc');

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: backgroundColors, // <--- Colores sincronizados
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 15
            }]
        },
        options: {
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: { 
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        font: { family: "'Roboto', sans-serif", size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const val = context.raw;
                            const percent = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                            return `${context.label}: $${val.toLocaleString()} (${percent}%)`;
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
                ctx.fillStyle = "#1a2a6c"; // Tu $primary-color
                const text = "Total: $" + total.toLocaleString('es-MX', { minimumFractionDigits: 2 });
                ctx.fillText(text, width / 2, height / 2);
                ctx.restore();
            }
        }]
    });
}

/**
 * Paginación de la tabla: 10 en Desktop / 5 en Móvil
 */
/**
 * Paginación de la tabla Responsiva
 * Escritorio: 10 elementos | Móvil: 5 elementos
 */
export function initTablePagination() {
    const tableBody = document.querySelector('.portfolio-table tbody');
    if (!tableBody) return;

    const rows = Array.from(tableBody.querySelectorAll('tr'));
    if (rows.length === 0) return;

    // Encapsulamos la lógica para poder recalcular si el usuario gira el celular
    const renderPagination = () => {
        // Detectamos si es pantalla móvil usando tu breakpoint de Sass (768px)
        const isMobile = window.innerWidth <= 768;
        const rowsPerPage = isMobile ? 5 : 10; // <--- Magia responsiva aquí
        
        let currentPage = 1;
        const totalPages = Math.ceil(rows.length / rowsPerPage);

        const showPage = (page) => {
            const start = (page - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            rows.forEach((row, index) => {
                row.style.display = (index >= start && index < end) ? '' : 'none';
            });
        };

        const updateControls = () => {
            showPage(currentPage);
            const info = document.getElementById('pageI');
            if (info) info.textContent = `Pág. ${currentPage}/${totalPages}`;
        };

        // Limpiamos la paginación anterior (útil si se redimensiona la pantalla)
        const oldPagination = document.querySelector('.table-pagination');
        if (oldPagination) oldPagination.remove();

        // Solo renderizamos los botones si hay más de 1 página
        if (totalPages > 1) {
            const container = document.createElement('div');
            container.className = 'table-pagination';
            container.style.cssText = 'display:flex; justify-content:center; gap:15px; padding:20px; align-items:center; margin-top:10px;';
            container.innerHTML = `
                <button id="prevP" style="padding:6px 16px; cursor:pointer; background:#fff; border:1px solid #cbd5e1; border-radius:6px; font-weight:bold; color:#1a2a6c;">&laquo;</button>
                <span id="pageI" style="font-weight:600; color:#64748b; font-size:0.95rem;">Pág. ${currentPage}/${totalPages}</span>
                <button id="nextP" style="padding:6px 16px; cursor:pointer; background:#fff; border:1px solid #cbd5e1; border-radius:6px; font-weight:bold; color:#1a2a6c;">&raquo;</button>
            `;
            tableBody.closest('.card').appendChild(container);

            document.getElementById('prevP').onclick = () => { 
                if(currentPage > 1) { currentPage--; updateControls(); } 
            };
            document.getElementById('nextP').onclick = () => { 
                if(currentPage < totalPages) { currentPage++; updateControls(); } 
            };
        }

        updateControls();
    };

    // 1. Ejecutamos la primera vez al cargar
    renderPagination();

    // 2. Listener Inteligente: Recalcula si el usuario redimensiona la ventana en PC 
    // o gira su celular de vertical a horizontal.
    window.addEventListener('resize', () => {
        clearTimeout(window.resizeTimer);
        window.resizeTimer = setTimeout(renderPagination, 250); // Evita saturar el navegador
    });
}

/**
 * Gestiona los Pop-ups de éxito o error al cargar la página
 */
export function initNotifications() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('success')) {
        const type = urlParams.get('success');
        let title = type === 'added' ? '¡Activo Registrado!' : '¡Activo Eliminado!';
        Swal.fire({ 
            icon: 'success', 
            title: title, 
            timer: 2000, 
            showConfirmButton: false 
        });
    }
}
/**
 * Confirmación de eliminación con Token CSRF
 */
export function confirmDelete(id, name, token) {
    Swal.fire({
        title: '¿Eliminar activo?',
        text: `¿Estás seguro de borrar "${name}"?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        confirmButtonText: 'Sí, borrar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            // Se agrega el parámetro &token a la URL
            window.location.href = `includes/delete_investment.php?id=${id}&token=${token}`;
        }
    });
}

/**
 * Controla la visibilidad de los campos según la categoría
 */
export function toggleFields() {
    const categoryId = document.getElementById('category_id')?.value;
    const dynamicFields = document.getElementById('dynamic-fields');
    const yieldGroup = document.getElementById('yield-group');
    const assetSearch = document.getElementById('asset_search');
    const cetesOptions = document.getElementById('cetes-options');

    if (!categoryId || !dynamicFields) return; // Protección contra páginas sin formulario

    const assetName = assetSearch ? assetSearch.value.toLowerCase() : '';

    dynamicFields.classList.remove('hidden');
    if (categoryId === "5" || categoryId === "6") {
        yieldGroup.classList.remove('hidden');
    } else {
        yieldGroup.classList.add('hidden');
        const yieldInput = document.getElementById('annual_yield');
        if (yieldInput) yieldInput.value = "0";
    }

    if (assetName.includes('cetes') || categoryId === "6") {
        cetesOptions.classList.remove('hidden');
    } else {
        cetesOptions.classList.add('hidden');
    }
}

/**
 * Consulta la tasa real de CetesDirecto mediante el puente PHP
 */
export async function updateCetesSeries() {
    const series = document.getElementById('cetes_plazo').value;
    const yieldInput = document.getElementById('annual_yield');
    const banxicoHidden = document.getElementById('banxico_series_hidden');

    if (!series || !yieldInput) return;
    banxicoHidden.value = series;

    yieldInput.placeholder = "Obteniendo tasa...";
    yieldInput.value = ""; 

    try {
        const response = await fetch(`includes/get_cetes_rate.php?series=${series}`);
        const text = await response.text();
        
        // Limpiamos el texto de cualquier espacio o símbolo raro
        const rate = parseFloat(text.trim());

        if(!isNaN(rate) && rate > 0) {
            yieldInput.value = rate.toFixed(2);
            // Avisamos al sistema que el valor cambió
            yieldInput.dispatchEvent(new Event('input'));
        } else {
            yieldInput.placeholder = "No disponible";
        }
    } catch (error) {
        console.error("Error al obtener tasa:", error);
        yieldInput.placeholder = "Error API";
    }
}

/**
 * Buscador híbrido: Local + API CoinGecko
 */
let searchTimeout = null;
export async function handleSearch(query) {
    const resultsDiv = document.getElementById('api-results');
    const categorySelect = document.getElementById('category_id');
    const assetInput = document.getElementById('asset_search');
    if (!resultsDiv || !assetInput) return;

    const lowerQuery = query.toLowerCase().trim();

    const localMapping = {
        'nu': { name: 'Nu México', cat: '5', yield: '14.25', platform: 'Nu' },
        'cetes': { name: 'CETES Directo', cat: '6', yield: '', platform: 'CETES' },
        'efectivo': { name: 'Efectivo', cat: '5', yield: '0', platform: 'Billetera' }
    };

    if (localMapping[lowerQuery]) {
        assetInput.value = localMapping[lowerQuery].name;
        categorySelect.value = localMapping[lowerQuery].cat;
        document.getElementById('annual_yield').value = localMapping[lowerQuery].yield;
        document.getElementById('platform').value = localMapping[lowerQuery].platform;
        resultsDiv.innerHTML = '';
        resultsDiv.style.display = 'none';
        toggleFields();
        return;
    }

    if (query.length < 3) {
        resultsDiv.style.display = 'none';
        return;
    }

    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
        try {
            const response = await fetch(`https://api.coingecko.com/api/v3/search?query=${query}`);
            const data = await response.json();
            if (localMapping[assetInput.value.toLowerCase().trim()]) return;

            resultsDiv.innerHTML = '';
            resultsDiv.style.display = 'block';

            data.coins.slice(0, 5).forEach(coin => {
                const div = document.createElement('div');
                div.className = 'suggestion-item';
                div.innerHTML = `<img src="${coin.thumb}" class="coin-thumb"> <span>${coin.name} (${coin.symbol})</span>`;
                div.onclick = () => {
                    assetInput.value = `${coin.name} (${coin.symbol})`;
                    document.getElementById('api_id_hidden').value = coin.id;
                    categorySelect.value = "4"; 
                    resultsDiv.style.display = 'none';
                    toggleFields();
                };
                resultsDiv.appendChild(div);
            });
        } catch (error) { console.error(error); }
    }, 400);
}