// assets/js/modules/privacy.js

export function initPrivacyMode() {
    // Usamos querySelectorAll para agarrar TODOS los botones del ojo que existan en la página
    const privacyBtns = document.querySelectorAll('#privacy-toggle'); 
    
    if (privacyBtns.length === 0) {
        console.warn("No se encontró el botón de privacidad.");
        return;
    }

    // 1. Revisar si el usuario ya lo tenía activo (al recargar la página)
    const isSaved = localStorage.getItem('bior_privacy') === 'true';
    if (isSaved) {
        document.body.classList.add('is-masked');
        actualizarIconos(true);
    }

    // 2. Asignar el evento a TODOS los botones encontrados
    privacyBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const isMasked = document.body.classList.toggle('is-masked');
            
            // Guardamos la preferencia
            localStorage.setItem('bior_privacy', isMasked);
            actualizarIconos(isMasked);
        });
    });

    // 3. Cambiar el ícono en todos los botones
    function actualizarIconos(masked) {
        privacyBtns.forEach(btn => {
            const icon = btn.querySelector('i');
            if (!icon) return;
            
            if (masked) {
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    }
}