// Manejar la subida del archivo
document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('excel-file');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch('/AnalisisE/upload_file', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Mostrar resultados
            const resultsDiv = document.getElementById('results');
            const plotImage = document.getElementById('plot-image');
            const uapDropdown = document.getElementById('uap-dropdown');
            
            // Establecer la imagen
            plotImage.src = `data:image/png;base64,${result.image}`;
            
            // Llenar el dropdown con UAPs
            uapDropdown.innerHTML = '<option value="General">GENERAL</option>';
            result.uaps.forEach(uap => {
                const option = document.createElement('option');
                option.value = uap;
                option.textContent = uap;
                uapDropdown.appendChild(option);
            });
            
            // Mostrar el contenedor de resultados
            resultsDiv.style.display = 'block';
            
            // Guardar datos de Excel para descarga
            window.currentExcelData = result.excel_data;
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al procesar el archivo');
    }
});

// Manejar la selección de UAP
document.getElementById('uap-dropdown').addEventListener('change', async (e) => {
    const uap = e.target.value;
    
    try {
        const response = await fetch('/AnalisisE/filter_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ uap })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Actualizar imagen y datos de descarga
            document.getElementById('plot-image').src = `data:image/png;base64,${result.image}`;
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
    const link = document.createElement('a');
    link.href = `data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,${window.currentExcelData}`;
    link.download = 'Consumo.xlsx';
    link.click();
});

document.querySelector('.download-image').addEventListener('click', () => {
    const imgSrc = document.getElementById('plot-image').src;
    const link = document.createElement('a');
    link.href = imgSrc;
    link.download = 'Consumo.png';
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