// Autocompletado para Maquina
const maquinaInput = document.getElementById('Maquina');
const suggestionsContainer = document.getElementById('maquina-suggestions');
const maquinaError = document.getElementById('maquina-error');
const submitButton = document.getElementById('submit-button');
const form = document.getElementById('predict-form');

console.log('Formulario encontrado:', !!form);

function validateMaquina(value) {
    console.log('Validando Maquina:', value);
    const isValidLength = value.length === 8;
    const isValidID = validMaquina.includes(value);
    if (!isValidLength) {
        maquinaError.textContent = 'El ID debe tener exactamente 8 dígitos.';
        maquinaError.style.display = 'block';
        submitButton.disabled = true;
    } else if (!isValidID) {
        maquinaError.textContent = 'El ID ingresado no es válido. Selecciona un ID válido.';
        maquinaError.style.display = 'block';
        submitButton.disabled = true;
    } else {
        maquinaError.style.display = 'none';
        submitButton.disabled = false;
    }
}

maquinaInput.addEventListener('input', function() {
    const value = this.value;
    suggestionsContainer.innerHTML = '';

    if (value.length > 0) {
        const suggestions = validMaquina.filter(id => id.startsWith(value));
        console.log('Sugerencias:', suggestions);
        suggestions.forEach(id => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'suggestion-item';
            suggestionItem.textContent = id;
            suggestionItem.addEventListener('click', function() {
                maquinaInput.value = id;
                suggestionsContainer.innerHTML = '';
                validateMaquina(id);
            });
            suggestionsContainer.appendChild(suggestionItem);
        });
    }

    validateMaquina(value);
});

document.addEventListener('click', function(event) {
    if (!maquinaInput.contains(event.target) && !suggestionsContainer.contains(event.target)) {
        suggestionsContainer.innerHTML = '';
    }
});

// Manejo del envío del formulario
form.addEventListener('submit', function(event) {
    event.preventDefault();
    console.log('Formulario enviado');
    
    const maquinaValue = maquinaInput.value;
    console.log('Maquina:', maquinaValue);
    if (maquinaValue.length !== 8 || !validMaquina.includes(maquinaValue)) {
        maquinaError.textContent = 'Por favor, ingresa un ID válido de 8 dígitos.';
        maquinaError.style.display = 'block';
        return;
    }

    const hora = parseFloat(document.getElementById('Hora').value);
    const semana = parseFloat(document.getElementById('Semana').value);
    const prior = parseFloat(document.getElementById('Prior').value);
    const l_av = parseFloat(document.getElementById('L_Av').value);
    const l_prev = parseFloat(document.getElementById('L_Prev').value);
    const l_imp = parseFloat(document.getElementById('L_Imp').value);
    const noprev_3m = parseFloat(document.getElementById('NoPrev_3m').value);
    const noav_3m = parseFloat(document.getElementById('NoAv_3m').value);
    const noimp_3m = parseFloat(document.getElementById('NoImp_3m').value);

    if (isNaN(hora) || hora < 0 || hora > 23) {
        alert('La hora debe estar entre 0 y 23.');
        return;
    }
    if (isNaN(semana) || semana < 1 || semana > 52) {
        alert('La semana debe estar entre 1 y 52.');
        return;
    }
    if (isNaN(prior) || prior < 0) {
        alert('La prioridad debe ser un número no negativo.');
        return;
    }
    if (isNaN(l_av) || l_av < 0) {
        alert('L Av debe ser un número no negativo.');
        return;
    }
    if (isNaN(l_prev) || l_prev < 0) {
        alert('L Prev debe ser un número no negativo.');
        return;
    }
    if (isNaN(l_imp) || l_imp < 0) {
        alert('L Imp debe ser un número no negativo.');
        return;
    }
    if (isNaN(noprev_3m) || noprev_3m < 0) {
        alert('NoPrev 3m debe ser un número no negativo.');
        return;
    }
    if (isNaN(noav_3m) || noav_3m < 0) {
        alert('NoAv 3m debe ser un número no negativo.');
        return;
    }
    if (isNaN(noimp_3m) || noimp_3m < 0) {
        alert('NoImp 3m debe ser un número no negativo.');
        return;
    }

    submitButton.disabled = true;
    const formData = new FormData(this);
    console.log('Enviando datos a:', this.action);
    fetch(this.action, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Respuesta recibida:', response.status);
        return response.text();
    })
    .then(html => {
        console.log('HTML recibido');
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const errorMessage = doc.querySelector('.error-message:not(#maquina-error)');
        const resultBoxContent = doc.querySelector('#result-box').innerHTML;

        console.log('Error encontrado:', !!errorMessage);
        console.log('Contenido de result-box:', resultBoxContent);

        const currentError = document.querySelector('.error-message:not(#maquina-error)');
        if (currentError) currentError.remove();

        const currentResult = document.querySelector('#result-box');
        currentResult.innerHTML = resultBoxContent;

        if (errorMessage) {
            document.querySelector('.content .container').insertAdjacentElement('beforeend', errorMessage);
        }

        submitButton.disabled = false;
    })
    .catch(error => {
        console.error('Error en fetch:', error);
        const errorDiv = document.createElement('p');
        errorDiv.className = 'error-message';
        errorDiv.textContent = 'Error al procesar la solicitud. Intenta de nuevo.';
        document.querySelector('.content .container').insertAdjacentElement('beforeend', errorDiv);
        submitButton.disabled = false;
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