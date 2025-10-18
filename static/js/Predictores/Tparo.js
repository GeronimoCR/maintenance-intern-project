// Autocompletado para IDMaquina
const idMaquinaInput = document.getElementById('IDMaquina');
const suggestionsContainer = document.getElementById('idmaquina-suggestions');
const idMaquinaError = document.getElementById('idmaquina-error');
const submitButton = document.getElementById('submit-button');
const form = document.getElementById('predict-form');

console.log('Formulario encontrado:', !!form);

function validateIDMaquina(value) {
    console.log('Validando IDMaquina:', value);
    const isValidLength = value.length === 8;
    const isValidID = validIDMaquina.includes(value);
    if (!isValidLength) {
        idMaquinaError.textContent = 'El ID debe tener exactamente 8 dígitos.';
        idMaquinaError.style.display = 'block';
        submitButton.disabled = true;
    } else if (!isValidID) {
        idMaquinaError.textContent = 'El ID ingresado no es válido. Selecciona un ID válido.';
        idMaquinaError.style.display = 'block';
        submitButton.disabled = true;
    } else {
        idMaquinaError.style.display = 'none';
        submitButton.disabled = false;
    }
}

idMaquinaInput.addEventListener('input', function() {
    const value = this.value;
    suggestionsContainer.innerHTML = '';

    if (value.length > 0) {
        const suggestions = validIDMaquina.filter(id => id.startsWith(value));
        console.log('Sugerencias:', suggestions);
        suggestions.forEach(id => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'suggestion-item';
            suggestionItem.textContent = id;
            suggestionItem.addEventListener('click', function() {
                idMaquinaInput.value = id;
                suggestionsContainer.innerHTML = '';
                validateIDMaquina(id);
            });
            suggestionsContainer.appendChild(suggestionItem);
        });
    }

    validateIDMaquina(value);
});

document.addEventListener('click', function(event) {
    if (!idMaquinaInput.contains(event.target) && !suggestionsContainer.contains(event.target)) {
        suggestionsContainer.innerHTML = '';
    }
});

// Manejo del envío del formulario
form.addEventListener('submit', function(event) {
    event.preventDefault();
    console.log('Formulario enviado');
    
    const idMaquinaValue = idMaquinaInput.value;
    console.log('IDMaquina:', idMaquinaValue);
    if (idMaquinaValue.length !== 8 || !validIDMaquina.includes(idMaquinaValue)) {
        idMaquinaError.textContent = 'Por favor, ingresa un ID válido de 8 dígitos.';
        idMaquinaError.style.display = 'block';
        return;
    }

    submitButton.disabled = true; // Deshabilitar botón
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
        const errorMessage = doc.querySelector('.error-message:not(#idmaquina-error)');
        const resultBoxContent = doc.querySelector('#result-box').innerHTML;

        console.log('Error encontrado:', !!errorMessage);
        console.log('Contenido de result-box:', resultBoxContent);

        const currentError = document.querySelector('.error-message:not(#idmaquina-error)');
        if (currentError) currentError.remove();

        const currentResult = document.querySelector('#result-box');
        currentResult.innerHTML = resultBoxContent;

        if (errorMessage) {
            document.querySelector('.content .container').insertAdjacentElement('beforeend', errorMessage);
        }

        submitButton.disabled = false; // Rehabilitar botón
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