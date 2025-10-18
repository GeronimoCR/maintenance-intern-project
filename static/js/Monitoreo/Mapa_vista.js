// static/js/Monitoreo/Mapa_vista.js
document.addEventListener('DOMContentLoaded', () => {
    // Configurar el mapa con Leaflet
    var map = L.map('map', {
        center: [0, 0],
        zoom: -0.1,
        minZoom: 0,
        maxZoom: 16,
        crs: L.CRS.Simple
    });

    // Obtener la ruta del mapa, bounds y zona desde los atributos data
    const mapDiv = document.getElementById('map');
    const mapaUrl = mapDiv.getAttribute('data-mapa') || '/static/mapas/Nave1.jpg';
    const boundsStr = mapDiv.getAttribute('data-bounds') || '[[0, 0], [1000, 1500]]';
    const zona = mapDiv.getAttribute('data-zona') || 'Nave1';
    const bounds = JSON.parse(boundsStr);

    // Añadir la imagen de fondo
    L.imageOverlay(mapaUrl, bounds).addTo(map);
    map.fitBounds(bounds);

    // Mostrar el overlay de carga
    const loadingOverlay = document.getElementById('loadingOverlay');

    // Obtener datos del servidor
    fetch('/Monitoreo_Energetico/get_data')
        .then(response => response.json())
        .then(data => {
            // Ocultar el overlay de carga
            loadingOverlay.classList.add('hidden');

            if (data.error) {
                console.error('Error:', data.error);
                alert('No se encontraron datos. Por favor, sube un archivo Excel primero.');
                return;
            }

            // Actualizar la fecha de última medición en el DOM
            const lastDateElement = document.getElementById('last-date');
            if (lastDateElement && data.last_date) {
                // Parsear la fecha en formato "DD/MM/YYYY HH:mm:ss"
                const [datePart, timePart] = data.last_date.split(' ');
                const [day, month, year] = datePart.split('/');
                const [hours, minutes, seconds] = timePart.split(':');
                const date = new Date(year, month - 1, day, hours, minutes, seconds);

                // Formatear la fecha en español
                if (!isNaN(date.getTime())) { // Verificar que la fecha es válida
                    const options = { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' };
                    lastDateElement.textContent = `Datos del ${date.toLocaleString('es-ES', options)}`;
                } else {
                    lastDateElement.textContent = `Datos del ${data.last_date}`; // Fallback si la fecha no es válida
                    console.warn('Fecha inválida:', data.last_date);
                }
            } else {
                console.warn('No se encontró last_date o el elemento #last-date');
            }

            // Filtrar datos según la zona actual
            const filteredData = data.data.filter(item => item.zona === zona);

            // Mostrar marcadores si hay datos para esta zona
            if (filteredData.length > 0) {
                filteredData.forEach((item) => {
                    const maquina = item.maquina;
                    const consumo = item.consumo;
                    const color = item.color;
                    const radio = item.radio;
                    const x = item.x;
                    const y = item.y;

                    // Establecer el color del contorno: rojo si el color es "black"
                    const borderColor = color === 'black' ? 'red' : color;

                    L.circle([x, y], {
                        radius: radio,
                        color: borderColor,
                        fillColor: color,
                        fillOpacity: 0.8
                    }).addTo(map).bindPopup(`Máquina: ${maquina}<br>Consumo: ${consumo} kWh`);
                });
            } else {
                alert('No se encontraron datos para esta zona. Por favor, sube un archivo Excel primero.');
            }
        })
        .catch(error => {
            // Ocultar el overlay de carga en caso de error
            loadingOverlay.classList.add('hidden');
            console.error('Error al obtener datos:', error);
            alert('Error al cargar los datos. Por favor, intenta de nuevo.');
        });
});