document.addEventListener('DOMContentLoaded', () => {
    
    const nombreInput = document.getElementById('nombre');
    const naveSelect = document.getElementById('nave');
    const editFields = document.getElementById('editFields');
    const editBtn = document.getElementById('editBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const errorMsg = document.getElementById('errorMsg');

    // Mostrar campos de edición cuando se selecciona una nave y hay un nombre
    naveSelect.addEventListener('change', fetchObjectData);
    nombreInput.addEventListener('input', () => {
        if (naveSelect.value) fetchObjectData();
    });

    function fetchObjectData() {
        const nombre = nombreInput.value.trim();
        const nave = naveSelect.value;

        if (!nombre || !nave) {
            editFields.style.display = 'none';
            errorMsg.textContent = '';
            clearAsterisks();
            return;
        }

        fetch('/Monitoreo_Energetico/get_object_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, nave })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                errorMsg.textContent = data.error;
                errorMsg.style.color = 'red';
                editFields.style.display = 'none';
                clearAsterisks();
            } else {
                errorMsg.textContent = '';
                // Rellenar los campos
                document.getElementById('x').value = data.x;
                document.getElementById('y').value = data.y;
                document.getElementById('Enc_NProd').value = data.Enc_NProd;
                document.getElementById('Enc_Prod').value = data.Enc_Prod;
                document.getElementById('Alert').value = data.Alert;
                document.getElementById('Rad').value = data.Rad;
                document.getElementById('Area').value = data.Area;
                editFields.style.display = 'block';
                clearAsterisks();
            }
        })
        .catch(error => {
            errorMsg.textContent = 'Error al cargar los datos';
            errorMsg.style.color = 'red';
            editFields.style.display = 'none';
            clearAsterisks();
        });
    }

    // Función para limpiar el formulario
    function clearForm() {
        nombreInput.value = '';
        naveSelect.value = '';
        document.getElementById('x').value = '';
        document.getElementById('y').value = '';
        document.getElementById('Enc_NProd').value = '';
        document.getElementById('Enc_Prod').value = '';
        document.getElementById('Alert').value = '';
        document.getElementById('Rad').value = '';
        document.getElementById('Area').value = '';
        editFields.style.display = 'none';
        errorMsg.textContent = '';
        clearAsterisks();
    }

    // Función para limpiar los asteriscos rojos
    function clearAsterisks() {
        document.querySelectorAll('.required-asterisk').forEach(asterisk => {
            asterisk.classList.remove('show');
        });
    }

    // Manejar el botón de cancelar
    cancelBtn.addEventListener('click', () => {
        clearForm();
    });

    // Manejar el botón de editar
    editBtn.addEventListener('click', () => {
        const nombre = nombreInput.value.trim();
        const nave = naveSelect.value;

        if (!nombre || !nave) {
            errorMsg.textContent = 'Por favor complete nombre y nave';
            errorMsg.style.color = 'red';
            return;
        }

        const updates = {
            x: document.getElementById('x').value,
            y: document.getElementById('y').value,
            Enc_NProd: document.getElementById('Enc_NProd').value,
            Enc_Prod: document.getElementById('Enc_Prod').value,
            Alert: document.getElementById('Alert').value,
            Rad: document.getElementById('Rad').value,
            Area: document.getElementById('Area').value
        };

        // Validar que todos los campos de edición estén llenos
        const fields = [
            { id: 'x', name: 'Coordenada X' },
            { id: 'y', name: 'Coordenada Y' },
            { id: 'Enc_NProd', name: 'Valor encendido sin producir' },
            { id: 'Enc_Prod', name: 'Valor encendido produciendo' },
            { id: 'Alert', name: 'Valor de alerta' },
            { id: 'Rad', name: 'Radio del círculo' },
            { id: 'Area', name: 'UAP' }
        ];
        let hasEmptyFields = false;
        clearAsterisks();
        fields.forEach(field => {
            if (!updates[field.id]) {
                errorMsg.textContent = 'Por favor complete todos los campos';
                errorMsg.style.color = 'red';
                document.getElementById(field.id).previousElementSibling.querySelector('.required-asterisk').classList.add('show');
                hasEmptyFields = true;
            }
        });

        if (hasEmptyFields) {
            return;
        }

        fetch('/Monitoreo_Energetico/update_object', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, nave, updates })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                errorMsg.textContent = data.error;
                errorMsg.style.color = 'red';
            } else {
                clearForm();
                errorMsg.textContent = 'Datos actualizados correctamente';
                errorMsg.style.color = 'green';
            }
        })
        .catch(error => {
            errorMsg.textContent = 'Error al actualizar los datos';
            errorMsg.style.color = 'red';
        });
    });
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