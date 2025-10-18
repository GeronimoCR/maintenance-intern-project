
document.addEventListener('DOMContentLoaded', () => {
    const chatbotIcon = document.getElementById('chatbot-icon');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotMessages = document.getElementById('chatbot-messages');

    // Abrir/cerrar ventana
    chatbotIcon.addEventListener('click', () => {
        chatbotWindow.style.display = chatbotWindow.style.display === 'none' ? 'flex' : 'none';
    });

    chatbotClose.addEventListener('click', () => {
        chatbotWindow.style.display = 'none';
    });

    // Enviar pregunta
    chatbotSend.addEventListener('click', () => {
        const pregunta = chatbotInput.value.trim();
        if (pregunta) {
            // Mostrar pregunta del usuario
            const userMessage = document.createElement('div');
            userMessage.textContent = pregunta; // Sin prefijo "Tú: "
            userMessage.className = 'user-message'; // Clase para usuario
            chatbotMessages.appendChild(userMessage);

            // Enviar al backend
            fetch('/chatbot/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pregunta })
            })
            .then(response => response.json())
            .then(data => {
                // Mostrar respuesta del chatbot
                const botMessage = document.createElement('div');
                botMessage.textContent = `Chatbot:\n${data.respuesta}`; 
                botMessage.className = 'bot-message'; // Clase para chatbot
                chatbotMessages.appendChild(botMessage);
                chatbotMessages.scrollTop = chatbotMessages.scrollHeight; // Scroll al final
            })
            .catch(error => console.error('Error:', error));

            chatbotInput.value = ''; // Limpiar input
        }
    });

    // Enviar con Enter
    chatbotInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            chatbotSend.click();
        }
    });
});