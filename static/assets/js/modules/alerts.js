// assets/js/modules/alerts.js

/**
 * --- BLOQUE 1: GESTIÓN DE TOASTS ---
 */
export function initToasts() {
    // Delegación global para cerrar Toasts (clic en la X)
    document.body.addEventListener('click', (e) => {
        const closeBtn = e.target.closest('.toast-close');
        if (closeBtn) {
            e.preventDefault();
            e.stopPropagation();
            const toast = closeBtn.closest('.toast');
            if (toast) cerrarElemento(toast);
        }
    });

    // Auto-cierre para Toasts de éxito que vienen de PHP
    document.querySelectorAll('.toast--success').forEach(toast => {
        setTimeout(() => cerrarElemento(toast), 5000);
    });
}

function cerrarElemento(el) {
    if (!el || el.classList.contains('fade-out')) return;
    el.style.pointerEvents = 'none';
    el.classList.add('fade-out');
    
    // Animación de salida
    el.style.opacity = '0';
    el.style.transform = 'translateX(50px)';
    el.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
    
    setTimeout(() => {
        if (el.parentNode) el.remove();
    }, 450);
}

/**
 * --- BLOQUE 2: GESTIÓN DE MODAL PERSONALIZADO ---
 */
const modal = document.getElementById('custom-confirm');
const btnConfirm = document.getElementById('modal-confirm');
const btnCancel = document.getElementById('modal-cancel');
const modalMessage = document.getElementById('modal-message');

function mostrarModal(mensaje) {
    return new Promise((resolve) => {
        if (!modal) return resolve(true); // Si no existe el modal, dejamos pasar el form

        modalMessage.innerText = mensaje;
        modal.classList.add('active');

        const handleConfirm = () => {
            modal.classList.remove('active');
            cleanup();
            resolve(true);
        };

        const handleCancel = () => {
            modal.classList.remove('active');
            cleanup();
            resolve(false);
        };

        const cleanup = () => {
            btnConfirm.removeEventListener('click', handleConfirm);
            btnCancel.removeEventListener('click', handleCancel);
        };

        btnConfirm.addEventListener('click', handleConfirm);
        btnCancel.addEventListener('click', handleCancel);
    });
}

/**
 * --- BLOQUE 3: INICIALIZADOR DE ALERTAS DE CONFIGURACIÓN ---
 */
export function initAlertsConf() {
    const forms = document.querySelectorAll('.config-form--conf');

    forms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault(); 
            
            const actionInput = this.querySelector('input[name="action"]');
            const action = actionInput ? actionInput.value : '';
            
            let msg = "¿Confirmas los cambios en tu perfil?";
            if (action === 'update_password') {
                msg = "Tu contraseña será modificada. ¿Estás seguro de continuar?";
            }

            const confirmed = await mostrarModal(msg);
            if (confirmed) {
                HTMLFormElement.prototype.submit.call(this);
            }
        });
    });

    // Manejo de botones de Zona de Peligro (SIN ALERTAS NATIVAS)
    const dangerButtons = document.querySelectorAll('.danger-actions--conf .btn-danger--conf');
    dangerButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const isCookieBtn = btn.classList.contains('outline--conf');
            
            // Personalizamos el mensaje del Modal según la acción
            const msg = isCookieBtn 
                ? "¿Seguro que quieres cerrar tu sesión actual?" 
                : "¡ACCIÓN IRREVERSIBLE! Estás por eliminar permanentemente tu cuenta y todos tus datos financieros.";
            
            // Llamamos a tu modal personalizado
            const confirmed = await mostrarModal(msg);
            
            if (confirmed) {
                if (isCookieBtn) {
                    // Si acepta borrar cookies, mandamos al logout
                    window.location.href = 'logout';
                } else {
                    // Si acepta borrar cuenta, mandamos directo al PHP de borrado
                    // Hemos quitado el confirm() nativo para mantener la estética
                    window.location.href = 'includes/delete_account.php';
                }
            }
        });
    });
}