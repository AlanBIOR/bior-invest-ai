const categoryColors = {
    'Efectivo': '#00b894',
    'Renta Variable': '#1a2a6c',
    'Renta Fija': '#64748b',
    'Inversiones Alternativas': '#3498db',
    'Inmuebles': '#fdbb2d',
    'Private Equity': '#8e44ad'
};

/**
 * 1. Gráfico de la Calculadora / Dashboard
 * @param {Array} labels - Nombres de las categorías
 * @param {Array} values - Montos calculados
 */
export function initGrafico(labels, values) {
    // CAMBIO: Usamos el ID que tienes en tu HTML (portfolioChart)
    const ctx = document.getElementById('portfolioChart'); 
    if (!ctx) return;

    // Calculamos el total para el texto del centro
    const total = values.reduce((sum, val) => sum + parseFloat(val), 0);

    // Mapeo de colores
    const backgroundColors = labels.map(label => {
        const key = Object.keys(categoryColors).find(k => k.toLowerCase() === label.toLowerCase());
        return key ? categoryColors[key] : '#cccccc';
    });

    // Destruir instancia previa para evitar errores de Chart.js
    const existingChart = Chart.getChart(ctx);
    if (existingChart) existingChart.destroy();

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
            cutout: '75%', // Espacio para el texto central
            plugins: {
                legend: { display: false }, // Usamos tus tarjetas como leyenda
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const val = context.raw;
                            return `${context.label}: $${parseFloat(val).toLocaleString('es-MX')}`;
                        }
                    }
                }
            }
        },
        plugins: [{
            id: 'centerText',
            afterDraw: (chart) => {
                const { ctx } = chart;
                const { width, height } = chart;
                const centerX = width / 2;
                const centerY = height / 2;

                ctx.save();
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";

                // Dibujar "Total"
                ctx.font = "500 14px 'Roboto', sans-serif";
                ctx.fillStyle = "#64748b";
                ctx.fillText("Total sugerido:", centerX, centerY - 15);

                // Dibujar el Monto
                ctx.font = "bold 20px 'Roboto', sans-serif";
                ctx.fillStyle = "#1a2a6c";
                const text = "$" + total.toLocaleString('es-MX', { minimumFractionDigits: 2 });
                ctx.fillText(text, centerX, centerY + 10);
                ctx.restore();
            }
        }]
    });
}

/**
 * 2. Gráfico del Portafolio Real (Aislado mediante Fetch API)
 */
export function initPortfolioChart() {
    const ctx = document.getElementById('portfolioChart');
    if (!ctx) return;

    // --- EL FIX: En lugar de fetch, leemos los datos que Django ya inyectó ---
    try {
        const labels = JSON.parse(ctx.dataset.labels);
        const values = JSON.parse(ctx.dataset.values).map(v => parseFloat(v));

        const total = values.reduce((sum, val) => sum + val, 0);

        // Mapeo de colores (esto ya lo tenías bien)
        const backgroundColors = labels.map(label => {
            const key = Object.keys(categoryColors).find(k => k.toLowerCase() === label.toLowerCase());
            return key ? categoryColors[key] : '#cccccc';
        });

        const existingChart = Chart.getChart(ctx);
        if (existingChart) existingChart.destroy();

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
                maintainAspectRatio: false,
                cutout: '80%',
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const val = context.raw;
                                const percent = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return `${context.label}: $${val.toLocaleString('es-MX')} (${percent}%)`;
                            }
                        }
                    }
                }
            },
            plugins: [{
                id: 'centerText',
                afterDraw: (chart) => {
                    const { ctx } = chart;
                    const meta = chart.getDatasetMeta(0);
                    if (!meta.data.length) return;

                    // Matemáticas exactas: Buscamos el centro real geométrico
                    const centerX = meta.data[0].x;
                    const centerY = meta.data[0].y;

                    // Responsividad: Tamaño basado en el radio interior
                    const innerRadius = chart.innerRadius;
                    const titleSize = innerRadius * 0.25; 
                    const valueSize = innerRadius * 0.35; 

                    ctx.save();
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";

                    // Dibujamos "Total:" alineado hacia arriba
                    ctx.font = `500 ${titleSize}px 'Roboto', sans-serif`;
                    ctx.fillStyle = "#64748b"; // $text-muted
                    ctx.fillText("Total:", centerX, centerY - (titleSize * 0.8));

                    // Dibujamos la cantidad alineada hacia abajo
                    ctx.font = `bold ${valueSize}px 'Roboto', sans-serif`;
                    ctx.fillStyle = "#1a2a6c"; // $primary-color
                    const text = "$" + total.toLocaleString('es-MX', { minimumFractionDigits: 2 });
                    ctx.fillText(text, centerX, centerY + (valueSize * 0.6));

                    ctx.restore();
                }
            }]
        });
    } catch (e) {
        console.error("Error al inicializar gráfica de Django:", e);
    }
}