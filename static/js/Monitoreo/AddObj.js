document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const addBtn = document.getElementById('AddBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const errorMsg = document.getElementById('errorMsg');
    const successMsg = document.getElementById('successMsg'); 

    // Función para limpiar el formulario
    function resetForm() {
        document.querySelectorAll('input').forEach(input => input.value = '');
        document.getElementById('Nave').value = '';
        errorMsg.textContent = '';
        successMsg.textContent = ''; 
    }

    // Manejar el envío del formulario
    if (addBtn) {
        addBtn.addEventListener('click', async function(e) {
            e.preventDefault();

            // Limpiar mensajes previos
            errorMsg.textContent = '';
            successMsg.textContent = '';

            // Obtener valores de los campos
            const Nombre = document.getElementById('Nombre').value;
            const Nave = document.getElementById('Nave').value;
            const x = document.getElementById('x').value;
            const y = document.getElementById('y').value;
            const Enc_NProd = document.getElementById('Enc_NProd').value;
            const Enc_Prod = document.getElementById('Enc_Prod').value;
            const Alert = document.getElementById('Alert').value;
            const Rad = document.getElementById('Rad').value;
            const Area = document.getElementById('Area').value;

            // Validar que todos los campos estén llenos
            if (!Nombre || !Nave || !x || !y || !Enc_NProd || !Enc_Prod || !Alert || !Rad || !Area) {
                errorMsg.textContent = 'Por favor, complete todos los campos.';
                return;
            }

            // Crear FormData para enviar al backend
            const formData = new FormData();
            formData.append('Nombre', Nombre); 
            formData.append('Nave', Nave); 
            formData.append('x', x);
            formData.append('y', y);
            formData.append('Enc_NProd', Enc_NProd);
            formData.append('Enc_Prod', Enc_Prod);
            formData.append('Alert', Alert);
            formData.append('Rad', Rad);
            formData.append('Area', Area);

            try {
                const response = await fetch('/Monitoreo_Energetico/add_object', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                if (response.ok) {
                    resetForm(); // Limpiar el formulario tras éxito
                    successMsg.textContent = 'Equipo agregado exitosamente';
                } else {
                    errorMsg.textContent = result.error || 'Error al agregar el equipo';
                }
            } catch (error) {
                errorMsg.textContent = 'Error de conexión con el servidor';
                console.error('Error:', error);
            }
        });
    }

    // Manejar el botón de cancelar
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            resetForm(); // Limpiar el formulario
        });
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