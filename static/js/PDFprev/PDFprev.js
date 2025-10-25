// Variables para almacenar los archivos
let pdfFile = null;
let csvFile = null;
let pdfResult = null;

// Determinar si estamos en auditorias.html o coordinadores.html
const isAuditorias = window.location.pathname.includes('/auditorias');

// Actualizar el estado de los archivos
function updateFileStatus() {
    const fileStatus = document.getElementById('fileStatus');
    const procesarBtn = document.getElementById('procesarbtn');
    if (pdfFile && csvFile) {
        fileStatus.textContent = 'PDF y CSV seleccionados';
        procesarBtn.disabled = false;
    } else if (pdfFile) {
        fileStatus.textContent = 'PDF seleccionado, falta CSV';
        procesarBtn.disabled = true;
    } else if (csvFile) {
        fileStatus.textContent = 'CSV seleccionado, falta PDF';
        procesarBtn.disabled = true;
    } else {
        fileStatus.textContent = 'Ningún archivo seleccionado';
        procesarBtn.disabled = true;
    }
}

// Seleccionar archivo PDF [DESCOMETAR]
/*document.getElementById('selectPDFbtn').addEventListener('click', () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf';
    input.onchange = (event) => {
        pdfFile = event.target.files[0];
        updateFileStatus();
    };
    input.click();
});*/

// Seleccionar archivo CSV [DESCOMENTAR]
/*document.getElementById('selectEXCELbtn').addEventListener('click', () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv';
    input.onchange = (event) => {
        csvFile = event.target.files[0];
        updateFileStatus();
    };
    input.click();
});*/

// Procesar archivos
document.getElementById('procesarbtn').addEventListener('click', async () => {
    if (!pdfFile || !csvFile) {
        alert('Por favor, selecciona ambos archivos primero.');
        return;
    }

    const formData = new FormData();
    formData.append('pdf', pdfFile);
    formData.append('csv', csvFile);
    formData.append('isAuditorias', isAuditorias);

    try {
        const response = await fetch('/PDFprev/procesar_archivos', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Error del servidor: ${response.status} - ${errorText}`);
        }

        pdfResult = await response.blob();
        document.getElementById('descargabtn').disabled = false;
        alert('Archivos procesados correctamente. Puedes descargar el PDF.');
    } catch (error) {
        console.error('Error detallado:', error);
        alert(`Hubo un error al procesar los archivos: ${error.message}`);
    }
});

// Descargar el PDF automáticamente
document.getElementById('descargabtn').addEventListener('click', () => {
    if (!pdfResult) {
        alert('Primero procesa los archivos.');
        return;
    }

    // Crear URL temporal para el Blob
    const url = window.URL.createObjectURL(pdfResult);
    // Crear elemento <a> para la descarga
    const a = document.createElement('a');
    a.href = url;
    a.download = isAuditorias ? 'Documento_auditorias.pdf' : 'Documento_coordinadores.pdf';
    
    // Agregar el elemento al DOM, simular clic y limpiarlo
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    // Liberar la URL creada
    window.URL.revokeObjectURL(url);
    
    alert('Archivo descargado exitosamente.');
});
