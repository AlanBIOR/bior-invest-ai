/**
 * Diccionario Global de Colores
 * Ambas gráficas lo leen para verse igual, pero sus datos no se mezclan.
 */
const categoryColors = {
    'Efectivo': '#00b894',
    'Renta Variable': '#1a2a6c',
    'Renta Fija': '#64748b',
    'Inversiones Alternativas': '#3498db',
    'Inmuebles': '#fdbb2d',
    'Private Equity': '#8e44ad'
};

/**
 * 1. Gráfico de la Calculadora / Dashboard (Aislado y Reforzado)
 */
export function initGrafico(labels, rawData) {
    const ctx = document.getElementById('graficoInversiones');
    if (!ctx) return;

    // Limpieza de datos por si PHP envía una estructura anidada en el Dashboard
    let finalData = [];
    if (Array.isArray(rawData) && rawData[0] && rawData[0].data) {
        finalData = rawData[0].data; 
    } else {
        finalData = rawData; 
    }

    // Mapeo dinámico e insensible a mayúsculas/minúsculas
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
                data: finalData,
                backgroundColor: backgroundColors,
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '80%', // Actualizado para consistencia visual
            plugins: {
                legend: { 
                    position: 'bottom',
                    labels: { padding: 20, usePointStyle: true }
                }
            }
        }
    });
}

/**
 * 2. Gráfico del Portafolio Real (Aislado mediante Fetch API)
 */
export function initPortfolioChart() {
    const ctx = document.getElementById('portfolioChart');
    if (!ctx) return;

    // Túnel independiente hacia tu servidor PHP
    fetch('includes/get_portfolio_data.php')
        .then(response => response.json())
        .then(data => {
            const labels = data.map(item => item.categoria);
            const values = data.map(item => item.total);

            // Mapeo de colores a prueba de errores tipográficos
            const backgroundColors = labels.map(label => {
                const key = Object.keys(categoryColors).find(k => k.toLowerCase() === label.toLowerCase());
                return key ? categoryColors[key] : '#cccccc';
            });
            
            const total = values.reduce((sum, val) => sum + parseFloat(val), 0);

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
                    cutout: '80%', // Espacio vital para el texto móvil
                    plugins: {
                        legend: { 
                            position: 'bottom',
                            labels: { padding: 20, usePointStyle: true, font: { family: "'Roboto', sans-serif" } }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const val = context.raw;
                                    const percent = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                    return `${context.label}: $${val.toLocaleString('es-MX', { minimumFractionDigits: 2 })} (${percent}%)`;
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
        })
        .catch(error => console.error("Error al cargar la gráfica del portafolio:", error));
}