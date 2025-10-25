// Manejar la subida del archivo [DESCOMENTAR]
/*document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('excel-file');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch('/AnalisisE/upload_file_wknd', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Mostrar selector de naves
            const resultsDiv = document.getElementById('results');
            const naveDropdown = document.getElementById('nave-dropdown');
            
            // Llenar dropdown con naves
            naveDropdown.innerHTML = '<option value="" disabled selected>Selecciona una nave</option>';
            result.naves.forEach(nave => {
                const option = document.createElement('option');
                option.value = nave;
                option.textContent = nave;
                naveDropdown.appendChild(option);
            });
            
            // Mostrar el contenedor de resultados
            resultsDiv.style.display = 'block';
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al procesar el archivo');
    }
});*/

// Manejar la selección de nave
document.getElementById('nave-dropdown').addEventListener('change', async (e) => {
    const nave = e.target.value;
    if (!nave) return; // Ignorar si no se selecciona nada
    
    try {
        const response = await fetch('/AnalisisE/filter_data_wknd', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ nave })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Actualizar texto del período
            const periodText = document.getElementById('period-text');
            periodText.textContent = `Periodo Base Load detectado en ${nave}:\n${result.period_start} - ${result.period_end}`;
            periodText.style.display = 'block';
            
            // Actualizar imagen
            const imageContainer = document.querySelector('.image-container');
            document.getElementById('plot-image').src = `data:image/png;base64,${result.image}`;
            imageContainer.style.display = 'block';
            
            // Guardar datos de Excel para descarga
            window.currentExcelData = result.excel_data;
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al filtrar los datos');
    }
});

// Manejar descargas
document.querySelector('.download-excel').addEventListener('click', () => {
    if (!window.currentExcelData) return;
    const link = document.createElement('a');
    link.href = `data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,${window.currentExcelData}`;
    link.download = 'result.xlsx';
    link.click();
});

document.querySelector('.download-image').addEventListener('click', () => {
    const imgSrc = document.getElementById('plot-image').src;
    if (!imgSrc) return;
    const link = document.createElement('a');
    link.href = imgSrc;
    link.download = 'plot.png';
    link.click();
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