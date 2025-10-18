document.addEventListener('DOMContentLoaded', () => {
    const nombreInput = document.getElementById('Nombre'); 
    const naveSelect = document.getElementById('Nave'); 
    const editFields = document.getElementById('editFields');
    const delBtn = document.getElementById('DelBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const errorMsg = document.getElementById('errorMsg');

    // Hacer los campos de la columna derecha de solo lectura
    const inputFields = ['x', 'y', 'Enc_NProd', 'Enc_Prod', 'Alert', 'Rad', 'Area'];
    inputFields.forEach(id => {
        document.getElementById(id).setAttribute('readonly', true);
    });

    // Mostrar datos cuando se selecciona nombre y nave
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
            } else {
                errorMsg.textContent = '';
                // Rellenar campos
                document.getElementById('x').value = data.x;
                document.getElementById('y').value = data.y;
                document.getElementById('Enc_NProd').value = data.Enc_NProd;
                document.getElementById('Enc_Prod').value = data.Enc_Prod;
                document.getElementById('Alert').value = data.Alert;
                document.getElementById('Rad').value = data.Rad;
                document.getElementById('Area').value = data.Area;
                editFields.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error en fetch get_object_data:', error); // Depuración
            errorMsg.textContent = 'Error al cargar los datos';
            errorMsg.style.color = 'red';
            editFields.style.display = 'none';
        });
    }

    // Función para limpiar el formulario
    function clearForm() {
        nombreInput.value = '';
        naveSelect.value = '';
        inputFields.forEach(id => {
            document.getElementById(id).value = ''; 
        });
        editFields.style.display = 'none';
        errorMsg.textContent = '';
    }

    // Manejar botón de cancelar
    cancelBtn.addEventListener('click', () => {
        clearForm();
    });

    // Manejar botón de eliminar
    delBtn.addEventListener('click', () => {
        const nombre = nombreInput.value.trim(); 
        const nave = naveSelect.value;

        if (!nombre || !nave) {
            errorMsg.textContent = 'Por favor complete nombre y nave';
            errorMsg.style.color = 'red';
            return;
        }

        if (confirm('¿Está seguro de que desea eliminar este equipo?')) {
            fetch('/Monitoreo_Energetico/delete_object', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nombre, nave })
            })
            .then(response => {
                return response.json();
            })
            .then(data => { 
                if (data.error) {
                    errorMsg.textContent = data.error;
                    errorMsg.style.color = 'red';
                } else {
                    clearForm();
                    errorMsg.textContent = data.message;
                    errorMsg.style.color = 'green';
                    
                }
            })
            .catch(error => {
                console.error('Error en fetch delete_object:', error);
                errorMsg.textContent = 'Error al eliminar el equipo';
                errorMsg.style.color = 'red';
            });
        }
    });
});