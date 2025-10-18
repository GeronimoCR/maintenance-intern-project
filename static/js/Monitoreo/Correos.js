document.addEventListener('DOMContentLoaded', () => {
    const emailList = document.getElementById('emailList');
    const deleteButton = document.getElementById('deleteButton');
    const addButton = document.getElementById('addButton');
    const addForm = document.getElementById('addForm');
    const newEmailInput = document.getElementById('newEmail');
    const submitEmailButton = document.getElementById('submitEmail');
    const messageDiv = document.getElementById('message');
    let selectedEmail = null;

    // Load emails on page load
    loadEmails();

    // Load emails from server
    function loadEmails() {
        fetch('/Monitoreo_Energetico/get_emails')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderEmails(data.emails);
                } else {
                    showMessage(data.message, false);
                }
            })
            .catch(error => showMessage('Error al cargar correos: ' + error, false));
    }

    // Render emails in the list
    function renderEmails(emails) {
        emailList.innerHTML = '';
        emails.forEach(email => {
            const div = document.createElement('div');
            div.textContent = email;
            div.addEventListener('click', () => {
                // Remove previous selection
                document.querySelectorAll('.email-list div').forEach(el => el.classList.remove('selected'));
                // Add selection
                div.classList.add('selected');
                selectedEmail = email;
                deleteButton.style.display = 'inline-block';
            });
            emailList.appendChild(div);
        });
        // Clear selection if no emails are selected
        if (!emails.includes(selectedEmail)) {
            selectedEmail = null;
            deleteButton.style.display = 'none';
        }
    }

    // Show success or error message
    function showMessage(message, isSuccess) {
        messageDiv.textContent = message;
        messageDiv.className = 'message ' + (isSuccess ? 'success' : 'error');
        messageDiv.style.display = 'block';

    }

    // Delete selected email
    deleteButton.addEventListener('click', () => {
        if (!selectedEmail) return;

        fetch('/Monitoreo_Energetico/delete_email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: selectedEmail })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderEmails(data.emails);
                    showMessage(data.message, true);
                } else {
                    showMessage(data.message, false);
                }
            })
            .catch(error => showMessage('Error al eliminar correo: ' + error, false));
    });

    // Show/hide add form
    addButton.addEventListener('click', () => {
        addForm.style.display = addForm.style.display === 'none' ? 'block' : 'none';
        newEmailInput.value = '';
    });

    // Add new email
    submitEmailButton.addEventListener('click', () => {
        const newEmail = newEmailInput.value.trim();
        if (!newEmail) {
            showMessage('Por favor, ingrese un correo.', false);
            return;
        }

        fetch('/Monitoreo_Energetico/add_email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: newEmail })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderEmails(data.emails);
                    addForm.style.display = 'none';
                    newEmailInput.value = '';
                    showMessage(data.message, true);
                } else {
                    showMessage(data.message, false);
                }
            })
            .catch(error => showMessage('Error al añadir correo: ' + error, false));
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