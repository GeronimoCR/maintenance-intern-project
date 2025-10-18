document.addEventListener('DOMContentLoaded', () => {
    const uapButton = document.querySelector('.uap-btn');
    const weekButton = document.querySelector('.week-btn');
    const resultImage = document.getElementById('result-image');
    const xlsButton = document.getElementById('download-xls');
    const pdfButton = document.getElementById('download-pdf');

    // Validar que los botones existan
    if (!uapButton || !weekButton) {
        console.error('No se encontraron los botones .uap-btn o .week-btn en el DOM');
        return;
    }

    const uapDropdown = uapButton.nextElementSibling;
    const weekDropdown = weekButton.nextElementSibling;

    // Validar que los dropdowns existan
    if (!uapDropdown || !weekDropdown) {
        console.error('No se encontraron los elementos .dropdown-content');
        return;
    }

    const uapItems = uapDropdown.querySelectorAll('.dropdown-item');
    const weekItems = weekDropdown.querySelectorAll('.dropdown-item');

    let selectedUap = null;
    let selectedWeek = null;

    // Seleccionar UAP
uapItems.forEach(item => {
    item.addEventListener('click', () => {
        selectedUap = item.getAttribute('data-value');
        uapButton.textContent = selectedUap;
        uapDropdown.classList.remove('show'); // Respaldo para ocultar tras clic
        if (selectedUap && selectedWeek) {
            fetchData(selectedUap, selectedWeek);
        }
    });
});

// Seleccionar Semana
weekItems.forEach(item => {
    item.addEventListener('click', () => {
        selectedWeek = item.getAttribute('data-value');
        weekButton.textContent = `Semana ${selectedWeek}`;
        weekDropdown.classList.remove('show'); // Respaldo para ocultar tras clic
        if (selectedUap && selectedWeek) {
            fetchData(selectedUap, selectedWeek);
        }
    });
});

    // Función para obtener datos y mostrar la imagen
    function fetchData(uap, week) {
        fetch('/Scorecard/process_filters', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ uap, week }),
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error); });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            resultImage.src = `data:image/png;base64,${data.image}`;
            resultImage.style.display = 'block';
            xlsButton.style.display = 'block';
            pdfButton.style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Error al procesar los datos: ${error.message}`);
        });
    }

    // Descargar Excel
    xlsButton.addEventListener('click', () => {
        fetch('/Scorecard/download_excel', {
            method: 'GET',
            credentials: 'same-origin'  // Incluir cookies de sesión
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error); });
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${selectedUap}_SEM${selectedWeek}.xlsx`;
            link.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Error al descargar Excel:', error);
            alert(`Error al descargar Excel: ${error.message}`);
        });
    });

    // Descargar PDF
    pdfButton.addEventListener('click', () => {
        fetch('/Scorecard/download_pdf', {
            method: 'GET',
            credentials: 'same-origin'  // Incluir cookies de sesión
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error); });
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${selectedUap}_SEM${selectedWeek}.pdf`;
            link.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Error al descargar PDF:', error);
            alert(`Error al descargar PDF: ${error.message}`);
        });
    });
});