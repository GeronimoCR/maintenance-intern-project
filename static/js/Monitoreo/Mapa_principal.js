// Escucha el evento 'click' del botón "Seleccionar Archivo" [DESCOMENTAR]
/*document.getElementById('selectFileButton').addEventListener('click', () => {
   document.getElementById('upload').click();
});*/

// Escucha el evento 'change' del input de archivo
document.getElementById('upload').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    document.getElementById('fileStatus').textContent = 'Subiendo archivo...';

    const formData = new FormData();
    formData.append("file", file);

    fetch('/Monitoreo_Energetico/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
            document.getElementById('fileStatus').textContent = 'Error al subir el archivo';
            document.getElementById('MapNave1').disabled = true;
            document.getElementById('MapNave2').disabled = true;
            document.getElementById('editInterfaceButton').disabled = true;
            toggleDropdownItems(true);
            return;
        }
        document.getElementById('fileStatus').textContent = 'Archivo cargado correctamente';
        document.getElementById('MapNave1').disabled = false;
        document.getElementById('MapNave2').disabled = false;
        document.getElementById('editInterfaceButton').disabled = false;
        toggleDropdownItems(false);
        // Después de subir el archivo, recargar las tablas
        loadEnergyTables();
    })
    .catch(error => {
        console.error('Error al enviar el archivo:', error);
        document.getElementById('fileStatus').textContent = 'Error al cargar el archivo';
        document.getElementById('MapNave1').disabled = true;
        document.getElementById('MapNave2').disabled = true;
        document.getElementById('editInterfaceButton').disabled = true;
        toggleDropdownItems(true);
    });
});

// Función para habilitar/deshabilitar ítems del dropdown
function toggleDropdownItems(disable) {
    const items = ['EditObj', 'AddObj', 'DelObj', 'Layout', 'Correos'];
    items.forEach(id => {
        const item = document.getElementById(id);
        item.setAttribute('data-disabled', disable.toString());
        item.style.pointerEvents = disable ? 'none' : 'auto';
        item.style.color = disable ? '#ccc' : 'black';
        item.style.backgroundColor = disable ? '#f9f9f9' : '#f9f9f9';
    });
}

// Maneja el clic en el botón "Ver Nave1"
document.getElementById('MapNave1')?.addEventListener('click', () => {
    window.location.href = '/Monitoreo_Energetico/nave1';
});

// Maneja el clic en el botón "Ver Nave2"
document.getElementById('MapNave2')?.addEventListener('click', () => {
    window.location.href = '/Monitoreo_Energetico/nave2';
});

// NUEVA LÓGICA PARA EL MODAL
const FIXED_PASSWORD = '1318Mantenimiento'; // Contraseña fija
let currentCallback = null; 

function showPasswordModal(callback) {
    const modal = document.getElementById('passwordModal');
    const passwordInput = document.getElementById('passwordInput');
    passwordInput.value = ''; // Limpiar el campo
    modal.style.display = 'flex';
    currentCallback = callback; 
}

function hidePasswordModal() {
    const modal = document.getElementById('passwordModal');
    modal.style.display = 'none';
}

// Maneja el botón "Aceptar" del modal
document.getElementById('modalAcceptButton')?.addEventListener('click', () => {
    const passwordInput = document.getElementById('passwordInput');
    if (passwordInput.value === FIXED_PASSWORD) {
        hidePasswordModal();
        if (currentCallback) {
            currentCallback();
        }
    } else {
        alert('Contraseña incorrecta. Acceso denegado.');
        passwordInput.value = ''; 
    }
});
// Acepta el enter
document.getElementById('passwordInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const passwordInput = document.getElementById('passwordInput');
        if (passwordInput.value === FIXED_PASSWORD) {
            hidePasswordModal();
            if (currentCallback) {
                currentCallback();
            }
        } else {
            alert('Contraseña incorrecta. Acceso denegado.');
            passwordInput.value = ''; 
        }
    }
});

// Maneja el botón "Cancelar" del modal
document.getElementById('modalCancelButton')?.addEventListener('click', () => {
    hidePasswordModal();
});

// Maneja los clics en los ítems del dropdown con verificación de contraseña
document.getElementById('EditObj')?.addEventListener('click', (e) => {
    e.preventDefault();
    if (e.target.getAttribute('data-disabled') === 'false') {
        showPasswordModal(() => {
            window.location.href = '/Monitoreo_Energetico/EditObj';
        });
    }
});

document.getElementById('AddObj')?.addEventListener('click', (e) => {
    e.preventDefault();
    if (e.target.getAttribute('data-disabled') === 'false') {
        showPasswordModal(() => {
            window.location.href = '/Monitoreo_Energetico/AddObj';
        });
    }
});

document.getElementById('DelObj')?.addEventListener('click', (e) => {
    e.preventDefault();
    if (e.target.getAttribute('data-disabled') === 'false') {
        showPasswordModal(() => {
            window.location.href = '/Monitoreo_Energetico/DelObj';
        });
    }
});

document.getElementById('Layout')?.addEventListener('click', (e) => {
    e.preventDefault();
    if (e.target.getAttribute('data-disabled') === 'false') {
        showPasswordModal(() => {
            window.location.href = '/Monitoreo_Energetico/Layout';
        });
    }
});

document.getElementById('Correos')?.addEventListener('click', (e) => {
    e.preventDefault();
    if (e.target.getAttribute('data-disabled') === 'false') {
        showPasswordModal(() => {
            window.location.href = '/Monitoreo_Energetico/Correos';
        });
    }
});

// Manejo del hover para el dropdown
const dropdown = document.querySelector('.dropdown');
const dropdownContent = document.getElementById('editDropdown');
dropdown.addEventListener('mouseenter', () => {
    if (!document.getElementById('editInterfaceButton').disabled) {
        dropdownContent.classList.add('show-dropdown');
    }
});
dropdown.addEventListener('mouseleave', () => {
    dropdownContent.classList.remove('show-dropdown');
});

// NUEVA FUNCIÓN PARA CARGAR LAS TABLAS
function loadEnergyTables() {
    fetch('/Monitoreo_Energetico/energy_tables')
        .then(response => response.json())
        .then(data => {
            const tablesContainer = document.getElementById('tables-container');
            const summaryTitle = document.getElementById('energy-summary-title');
            if (data.error) {
                summaryTitle.textContent = 'Resumen consumo energético';
                tablesContainer.innerHTML = '<p>No hay datos disponibles. Por favor, cargue un archivo.</p>';
                return;
            }

            // Actualizar el título con la fecha
            summaryTitle.textContent = `Resumen consumo energético de ${data.last_date}`;

            // Limpiar el contenedor
            tablesContainer.innerHTML = '';

            // Generar tablas para cada área
            for (const [area, machines] of Object.entries(data.areas)) {
                // Crear título del área
                const areaTitle = document.createElement('h2');
                areaTitle.textContent = area;
                areaTitle.style.textAlign = 'center';
                tablesContainer.appendChild(areaTitle);

                // Crear tabla
                const table = document.createElement('table');
                table.className = 'energy-table';
                table.style.margin = '0 auto 20px auto';

                // Crear encabezado de la tabla
                const thead = document.createElement('thead');
                thead.innerHTML = `
                    <tr>
                        <th>Máquina</th>
                        <th>Estatus</th>
                        <th>Consumo (KWh)</th>
                    </tr>
                `;
                table.appendChild(thead);

                // Crear cuerpo de la tabla
                const tbody = document.createElement('tbody');
                machines.forEach(machine => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${machine.maquina}</td>
                        <td>${machine.status}</td>
                        <td>${machine.consumo}</td>
                    `;
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);

                tablesContainer.appendChild(table);
            }
        })
        .catch(error => {
            console.error('Error al cargar las tablas:', error);
            const tablesContainer = document.getElementById('tables-container');
            tablesContainer.innerHTML = '<p>Error al conectar con el servidor.</p>';
            document.getElementById('energy-summary-title').textContent = 'Resumen consumo energético';
        });
}

// Verificar si hay datos disponibles al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('fileStatus').textContent = 'Espere, verificando datos en servidor...';
    fetch('/Monitoreo_Energetico/get_data')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.log('No hay datos disponibles:', data.error);
                document.getElementById('fileStatus').textContent = 'No hay archivo cargado';
                document.getElementById('MapNave1').disabled = true;
                document.getElementById('MapNave2').disabled = true;
                document.getElementById('editInterfaceButton').disabled = true;
                toggleDropdownItems(true);
            } else {
                document.getElementById('fileStatus').textContent = 'Datos cargados desde el servidor';
                document.getElementById('MapNave1').disabled = false;
                document.getElementById('MapNave2').disabled = false;
                document.getElementById('editInterfaceButton').disabled = false;
                toggleDropdownItems(false);
            }
            // Cargar las tablas al iniciar
            loadEnergyTables();
        })
        .catch(error => {
            console.error('Error al obtener datos:', error);
            document.getElementById('fileStatus').textContent = 'Error al conectar con el servidor';
            document.getElementById('MapNave1').disabled = true;
            document.getElementById('MapNave2').disabled = true;
            document.getElementById('editInterfaceButton').disabled = true;
            toggleDropdownItems(true);
            // Intentar cargar las tablas de todos modos
            loadEnergyTables();
        });
});