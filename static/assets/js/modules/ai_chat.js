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

    // --- NUEVO: CARGAR HISTORIAL AL INICIAR ---
    loadChatFromLocal();

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

        // 🚨 CAMBIO DE SEGURIDAD: 
        // Primero intentamos leer del HTML, si no existe, usamos la llave fija
        const phone = chatWindow.dataset.whatsappPhone;
        const apiKey = chatWindow.dataset.apiKey || "BIOR_Secure_v1_20370519_xYz-NumAPI"; 

        appendUserMessage(text);
        chatInput.value = ''; 
        showLoading();

        try {
            // 🚨 FORZAMOS LA RUTA CORRECTA
            const response = await fetch('/api/v1/ai-chat/', { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Api-Key': apiKey, 
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ 
                    whatsapp_phone: phone, 
                    text: text 
                }), 
            });

            if (response.status === 403) {
                console.error("Error 403: La llave enviada fue:", apiKey);
                throw new Error('No autorizado (Llave incorrecta)');
            }
            
            if (!response.ok) throw new Error('Error en la respuesta del servidor');

            const data = await response.json();

            if (data.status === 'success') {
                appendAIMessage(data.response);
            } else {
                appendAIMessage(data.response || data.message);
            }

        } catch (error) {
            console.error('Error en el Chatbot:', error);
            appendAIMessage("Disculpa, el asesor está experimentando problemas técnicos.");
        } finally {
            hideLoading();
        }
    }
    // Eventos
    chatSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 4. Funciones auxiliares
    function appendUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'user-message flex justify-end mb-4';
        div.innerHTML = `<div class="bg-blue-600 p-3 rounded-t-xl rounded-l-xl max-w-[85%] text-white shadow-lg"><p>${escapeHTML(text)}</p></div>`;
        chatMessages.appendChild(div);
        saveChatToLocal(); // 💾 Guardar en local
        scrollToBottom();
    }

    function appendAIMessage(text) {
        const div = document.createElement('div');
        div.className = 'ai-message flex justify-start mb-4';
        const htmlContent = marked.parse(text);

        div.innerHTML = `
            <div class="bg-gray-800 p-3 rounded-t-xl rounded-r-xl max-w-[85%] border border-gray-700 text-white shadow-lg">
                <div class="markdown-body text-sm">${htmlContent}</div>
            </div>
        `;
        chatMessages.appendChild(div);
        saveChatToLocal(); // 💾 Guardar en local
        scrollToBottom();
    }

    // --- NUEVAS FUNCIONES DE PERSISTENCIA ---
    function saveChatToLocal() {
        // Usamos una llave única por usuario para evitar mezclar chats si cambian de cuenta
        localStorage.setItem(`bior_chat_${username}`, chatMessages.innerHTML);
    }

    function loadChatFromLocal() {
        const savedChat = localStorage.getItem(`bior_chat_${username}`);
        if (savedChat) {
            chatMessages.innerHTML = savedChat;
            scrollToBottom();
        }
    }

    // Auxiliares estándar
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

    function showLoading() { chatLoading.classList.remove('hidden'); }
    function hideLoading() { chatLoading.classList.add('hidden'); }
    function scrollToBottom() { chatMessages.scrollTop = chatMessages.scrollHeight; }
    
    function escapeHTML(str) {
        return str.replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[m]);
    }
}