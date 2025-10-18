// Funciones para el modal
function abrirModal() {
    document.getElementById('modal').style.display = 'flex';
}

function cerrarModal() {
    document.getElementById('modal').style.display = 'none';
}

// Limpieza de archivo: Detectar cambio en el input oculto
document.getElementById('input-archivo').addEventListener('change', async (e) => {
    const archivo = e.target.files[0];
    const estado = document.getElementById('estado-subida');

    if (!archivo) {
        estado.textContent = 'Por favor, selecciona un archivo.';
        return;
    }

    const formData = new FormData();
    formData.append('archivo', archivo);

    try {
        estado.textContent = 'Procesando archivo...';
        const respuesta = await fetch('/Scorecard/limpiar_archivo', {
            method: 'POST',
            body: formData
        });

        const resultado = await respuesta.json();
        if (respuesta.ok) {
            estado.textContent = 'Archivo procesado correctamente. Selecciona un periodo para descargar.';
            // Mostrar contenedor del botón Descargar periodo
            const descargarPeriodo = document.getElementById('descargar-periodo');
            descargarPeriodo.style.display = 'block';

            // Llenar la lista con las semanas y Periodo completo
            const lista = document.querySelector('.periodo-lista');
            lista.innerHTML = ''; // Limpiar lista previa
            resultado.semanas.forEach(semana => {
                const li = document.createElement('li');
                li.textContent = `Semana ${semana}`;
                li.dataset.semana = semana;
                li.addEventListener('click', () => descargarSemana(semana));
                lista.appendChild(li);
            });
            const liCompleto = document.createElement('li');
            liCompleto.textContent = 'Periodo completo';
            liCompleto.addEventListener('click', descargarCompleto);
            lista.appendChild(liCompleto);
        } else {
            estado.textContent = `Error: ${resultado.error}`;
        }
    } catch (error) {
        estado.textContent = 'Error al procesar el archivo.';
        console.error(error);
    }
});

// Descargar semana específica
async function descargarSemana(semana) {
    const estado = document.getElementById('estado-subida');

    try {
        const respuesta = await fetch(`/Scorecard/descargar_semana?semana=${semana}`);
        if (respuesta.ok) {
            const blob = await respuesta.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `SegLab_SEM${semana}.xlsx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            estado.textContent = 'Descarga iniciada.';
        } else {
            const resultado = await respuesta.json();
            estado.textContent = `Error: ${resultado.error}`;
        }
    } catch (error) {
        estado.textContent = 'Error al descargar.';
        console.error(error);
    }
}

// Descargar archivo completo
async function descargarCompleto() {
    const estado = document.getElementById('estado-subida');

    try {
        const respuesta = await fetch('/Scorecard/descargar_completo');
        if (respuesta.ok) {
            const blob = await respuesta.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'SegLab.xlsx';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            estado.textContent = 'Descarga iniciada.';
        } else {
            const resultado = await respuesta.json();
            estado.textContent = `Error: ${resultado.error}`;
        }
    } catch (error) {
        estado.textContent = 'Error al descargar.';
        console.error(error);
    }
}

// Subir base de datos: Detectar cambio en el input oculto
document.getElementById('input-bd').addEventListener('change', async (e) => {
    const archivo = e.target.files[0];
    const estado = document.getElementById('estado-subida-bd');

    if (!archivo) {
        estado.textContent = 'Por favor, selecciona un archivo.';
        return;
    }

    const formData = new FormData();
    formData.append('archivo', archivo);

    try {
        estado.textContent = 'Subiendo base de datos...';
        const respuesta = await fetch('/Scorecard/subir_base_datos', {
            method: 'POST',
            body: formData
        });

        const resultado = await respuesta.json();
        if (respuesta.ok) {
            estado.textContent = 'Base de datos subida y guardada correctamente, puedes acceder a tus indicadores';
        } else {
            estado.textContent = `Error: ${resultado.error}`;
        }
    } catch (error) {
        estado.textContent = 'Error al subir la base de datos.';
        console.error(error);
    }
});

// Mostrar/ocultar lista en hover
const descargarBtn = document.querySelector('.descargar-periodo-btn');
const lista = document.querySelector('.periodo-lista');

descargarBtn.addEventListener('mouseenter', () => {
    lista.style.display = 'block';
});

descargarBtn.addEventListener('mouseleave', () => {
    // Retrasar el ocultar para permitir mover el cursor a la lista
    setTimeout(() => {
        if (!lista.matches(':hover')) {
            lista.style.display = 'none';
        }
    }, 100);
});

lista.addEventListener('mouseenter', () => {
    lista.style.display = 'block';
});

lista.addEventListener('mouseleave', () => {
    lista.style.display = 'none';
});