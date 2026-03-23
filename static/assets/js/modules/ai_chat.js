export function initAIChat() {
    // 1. Elementos del DOM
    const chatToggle = document.getElementById('ai-chat-toggle');
    const chatWindow = document.getElementById('ai-chat-window');
    
    if (!chatToggle || !chatWindow) return; 

    const chatClose = document.getElementById('ai-chat-close');
    const chatMessages = document.getElementById('ai-chat-messages');
    const chatInput = document.getElementById('ai-chat-input');
    const chatSend = document.getElementById('ai-chat-send');
    const chatLoading = document.getElementById('ai-chat-loading');

    const username = chatWindow.dataset.username;

    // 2. Funciones de apertura/cierre
    chatToggle.addEventListener('click', () => {
        chatWindow.classList.toggle('hidden');
        if (!chatWindow.classList.contains('hidden')) {
            chatInput.focus();
            scrollToBottom();
        }
    });

    chatClose.addEventListener('click', () => {
        chatWindow.classList.add('hidden');
    });

    // 3. Función de envío a Gemini
    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // 1. Extraemos los datos del HTML de forma segura
        const phone = chatWindow.dataset.whatsappPhone;
        const apiKey = chatWindow.dataset.apiKey; 

        appendUserMessage(text);
        chatInput.value = ''; 
        showLoading();

        try {
            // 🚨 CAMBIO DE RUTA: Apuntamos a tu lógica interna de IA, no al webhook de n8n
            const response = await fetch('/api/v1/ai-chat/', { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Api-Key': apiKey, // Seguridad: El candado que pusimos
                    'X-CSRFToken': getCookie('csrftoken'), // Importante en Django para POST internos
                },
                body: JSON.stringify({ 
                    whatsapp_phone: phone, 
                    text: text 
                }), 
            });

            if (response.status === 403) throw new Error('No autorizado');
            if (!response.ok) throw new Error('Error en la respuesta del servidor');

            const data = await response.json();

            if (data.status === 'success') {
                appendAIMessage(data.response);
            } else {
                // Si el perfil no existe o hay error de IA
                appendAIMessage(data.response || data.message);
            }

        } catch (error) {
            console.error('Error en el Chatbot:', error);
            appendAIMessage("Disculpa, el asesor está experimentando problemas técnicos.");
        } finally {
            hideLoading();
        }
    }

    // Función auxiliar para el CSRF de Django (Cópiala también)
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

    // Eventos
    chatSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 4. Funciones auxiliares (Burbujas con Soporte Markdown)
    function appendUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'user-message flex justify-end';
        // Para el usuario seguimos escapando por seguridad
        div.innerHTML = `<div class="bg-blue-600 p-3 rounded-t-xl rounded-l-xl max-w-[85%] text-white shadow-lg"><p>${escapeHTML(text)}</p></div>`;
        chatMessages.appendChild(div);
        scrollToBottom();
    }

    function appendAIMessage(text) {
        const div = document.createElement('div');
        div.className = 'ai-message flex justify-start';
        
        // 🎨 Procesamos el texto con Marked.js para renderizar negritas, listas, etc.
        const htmlContent = marked.parse(text);

        div.innerHTML = `
            <div class="bg-gray-800 p-3 rounded-t-xl rounded-r-xl max-w-[85%] border border-gray-700 text-white shadow-lg">
                <div class="markdown-body">${htmlContent}</div>
            </div>
        `;
        chatMessages.appendChild(div);
        scrollToBottom();
    }

    function showLoading() { chatLoading.classList.remove('hidden'); }
    function hideLoading() { chatLoading.classList.add('hidden'); }
    function scrollToBottom() { chatMessages.scrollTop = chatMessages.scrollHeight; }
    
    function escapeHTML(str) {
        return str.replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[m]);
    }
}