/**
 * Módulo de Exportación de Imagen (PNG) - BIOR Invest
 * Técnica: Limpieza de estilos en clon para evitar bloques azules y desalineación
 */

export function generarImagen() {
    const original = document.querySelector('.main-content');
    if (!original) return;

    // 1. Clonamos el contenedor
    const clon = original.cloneNode(true);

    // 2. TRUCO DE INGENIERÍA: Copiar manualmente el contenido de los Canvas (Gráficas)
    const originalCanvases = original.querySelectorAll('canvas');
    const clonedCanvases = clon.querySelectorAll('canvas');
    originalCanvases.forEach((orig, i) => {
        clonedCanvases[i].getContext('2d').drawImage(orig, 0, 0);
    });

    // 3. LIMPIEZA DE ESTILOS EN EL CLON (Evita los bloques azules y bordes negros)
    const inputs = clon.querySelectorAll('input');
    inputs.forEach(inp => {
        // Convertimos el input en texto plano visualmente para la foto
        inp.style.border = 'none';
        inp.style.background = 'transparent';
        inp.style.boxShadow = 'none';
        inp.style.padding = '0';
        inp.style.margin = '0';
        inp.style.outline = 'none';
    });

    // Eliminamos el botón de descarga y su espacio
    const btnContenedor = clon.querySelector('.actions-container');
    if (btnContenedor) btnContenedor.remove();

    // 4. POSICIONAMIENTO INVISIBLE
    clon.style.position = 'fixed';
    clon.style.left = '-9999px';
    clon.style.top = '0';
    clon.style.width = original.offsetWidth + 'px';
    document.body.appendChild(clon);

    // 5. CAPTURA CON RENDERIZADO MEJORADO
    html2canvas(clon, {
        scale: 3, // Mayor escala para evitar pixelado en los números
        useCORS: true,
        backgroundColor: "#f4f7f6", // Mantiene tu fondo gris limpio
        logging: false,
        onclone: (clonedDoc) => {
            // Ajuste final de elementos que se mueven
            const cards = clonedDoc.querySelectorAll('.card');
            cards.forEach(c => {
                c.style.overflow = 'hidden';
                c.style.display = 'block'; // Asegura que no se muevan los bloques
            });
        }
    }).then(canvas => {
        const link = document.createElement('a');
        link.download = `Estrategia_BIOR_Invest.png`;
        link.href = canvas.toDataURL("image/png");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Limpieza final
        document.body.removeChild(clon);
    }).catch(err => {
        console.error("Error en la captura:", err);
        if (document.body.contains(clon)) document.body.removeChild(clon);
    });
}