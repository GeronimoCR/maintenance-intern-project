document.getElementById('uploadForm').addEventListener('submit', async function (event) {
        event.preventDefault(); // Evitar recarga de la página

        const form = event.target;
        const formData = new FormData(form);
        const messageDiv = document.getElementById('message');

        try {
            const response = await fetch('/Monitoreo_Energetico/upload_map', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                // Mostrar mensaje de éxito y limpiar el formulario
                messageDiv.textContent = result.message;
                messageDiv.className = 'message success';
                form.reset();
            } else {
                // Mostrar mensaje de error
                messageDiv.textContent = result.error;
                messageDiv.className = 'message error';
            }
        } catch (error) {
            // Mostrar error de red o servidor
            messageDiv.textContent = 'Error en el servidor: ' + error.message;
            messageDiv.className = 'message error';
        }
    });


// Obtener elementos
const helpBtn = document.getElementById('helpBtn');
const helpModal = document.getElementById('helpModal');
const closeModal = document.getElementById('closeModal');

// Abrir modal al hacer clic en el botón de ayuda
helpBtn.onclick = function() {
    helpModal.style.display = 'block';
}

// Cerrar modal al hacer clic en la X
closeModal.onclick = function() {
    helpModal.style.display = 'none';
}

// Cerrar modal al hacer clic fuera del contenido
window.onclick = function(event) {
    if (event.target == helpModal) {
        helpModal.style.display = 'none';
    }
}